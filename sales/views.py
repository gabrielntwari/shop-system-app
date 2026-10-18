import json
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from inventory.models import Product

from .models import Receipt, Sale
from .services import add_receipt_payment, create_receipt


METHODS = Sale.PAYMENT_METHOD_CHOICES


def _is_owner(user):
    return user.groups.filter(name="owner").exists()


def _is_staff_user(user):
    return _is_owner(user) or user.groups.filter(name="employee").exists()


def _require_staff(user):
    if not _is_staff_user(user):
        raise PermissionDenied


def _can_see(user, receipt):
    return _is_owner(user) or receipt.employee_id == user.id


def _money(text):
    text = (text or "").replace(",", "").replace(" ", "").strip()
    if not text:
        return Decimal(0)
    try:
        return Decimal(text)
    except InvalidOperation:
        raise ValidationError("Please enter a valid amount.")


def _product_choices():
    items = []
    for p in Product.objects.all().order_by("item_name", "brand"):
        stock = p.current_stock
        if stock > 0:
            items.append({
                "id": p.id,
                "name": str(p),
                "stock": stock,
                "min": float(p.minimum_selling_price),
                "price": float(p.shop_price),
            })
    return items


# ==============================================================
# ADD SALE (many products, one receipt)
# ==============================================================

@login_required
def add_sale(request):

    _require_staff(request.user)

    products = _product_choices()
    rows = []
    form = {
        "customer_name": "", "customer_phone": "", "customer_email": "",
        "paid": "", "method": "cash", "promise_date": "", "note": "",
    }
    errors = []

    if request.method == "POST":

        for key in form:
            form[key] = request.POST.get(key, "").strip()

        pids = request.POST.getlist("product")
        qtys = request.POST.getlist("quantity")
        prices = request.POST.getlist("price")

        lines = []
        for pid, qty, price in zip(pids, qtys, prices):
            if not pid and not qty and not price:
                continue
            rows.append({"product": pid, "quantity": qty, "price": price})
            try:
                product = Product.objects.get(pk=int(pid))
                q = int(qty)
                pr = _money(price)
            except (ValueError, TypeError, Product.DoesNotExist,
                    ValidationError):
                errors.append(
                    "Every row needs a product, a whole quantity and a price."
                )
                continue
            lines.append((product, q, pr))

        promise = None
        if form["promise_date"]:
            try:
                promise = datetime.strptime(
                    form["promise_date"], "%Y-%m-%d"
                ).date()
            except ValueError:
                errors.append("The promised date is not valid.")

        if not errors:
            try:
                total = sum((Decimal(q) * p for _, q, p in lines), Decimal(0))
                paid_text = form["paid"]
                paid = total if paid_text == "" else _money(paid_text)

                receipt = create_receipt(
                    user=request.user,
                    lines=lines,
                    paid=paid,
                    method=form["method"] if paid > 0 else "",
                    customer_name=form["customer_name"],
                    customer_email=form["customer_email"],
                    customer_phone=form["customer_phone"],
                    note=form["note"],
                    promise_date=promise,
                )
                messages.success(
                    request, f"Sale saved. Receipt {receipt.number} created."
                )
                return redirect("receipt_detail", pk=receipt.pk)

            except ValidationError as error:
                errors.extend(error.messages)

    if not rows:
        rows = [{"product": "", "quantity": "1", "price": ""}]

    return render(request, "sales/add_sale.html", {
        "products_json": json.dumps(products),
        "rows_json": json.dumps(rows),
        "form": form,
        "errors": errors,
        "methods": METHODS,
    })


# ==============================================================
# RECEIPT LIST
# ==============================================================

@login_required
def receipt_list(request):

    _require_staff(request.user)

    receipts = Receipt.objects.prefetch_related("sales", "payments")
    if not _is_owner(request.user):
        receipts = receipts.filter(employee=request.user)

    q = request.GET.get("q", "").strip()
    if q:
        digits = q.upper().replace("RCT-", "").lstrip("0")
        cond = (
            Q(customer_name__icontains=q)
            | Q(customer_phone__icontains=q)
            | Q(order_number__icontains=q)
        )
        if digits.isdigit():
            cond |= Q(pk=int(digits))
        receipts = receipts.filter(cond)

    flt = request.GET.get("filter", "all")
    if flt == "web":
        receipts = receipts.exclude(order_number="")

    receipts = list(receipts)

    if flt == "due":
        receipts = [r for r in receipts if r.balance > 0]
    elif flt == "paid":
        receipts = [r for r in receipts if r.balance <= 0]

    today = timezone.localdate()
    all_mine = Receipt.objects.prefetch_related("sales", "payments")
    if not _is_owner(request.user):
        all_mine = all_mine.filter(employee=request.user)
    all_mine = list(all_mine)

    sold_today = sum(
        r.total for r in all_mine
        if timezone.localtime(r.created_at).date() == today
    )
    collected_today = sum(
        p.amount for r in all_mine for p in r.payments.all()
        if timezone.localtime(p.date).date() == today
    )
    owing = [r for r in all_mine if r.balance > 0]

    return render(request, "sales/receipt_list.html", {
        "receipts": receipts[:300],
        "q": q,
        "filter": flt,
        "sold_today": sold_today,
        "collected_today": collected_today,
        "owing_total": sum(r.balance for r in owing),
        "owing_count": len(owing),
        "today_count": sum(
            1 for r in all_mine
            if timezone.localtime(r.created_at).date() == today
        ),
    })


# ==============================================================
# RECEIPT DETAIL + PAYMENT
# ==============================================================

def _get_receipt(request, pk):
    _require_staff(request.user)
    receipt = get_object_or_404(
        Receipt.objects.prefetch_related(
            "sales__product", "payments__recorded_by"
        ),
        pk=pk,
    )
    if not _can_see(request.user, receipt):
        raise PermissionDenied
    return receipt


def _phone_for_whatsapp(phone):
    digits = "".join(c for c in phone if c.isdigit())
    if digits.startswith("0"):
        digits = "250" + digits[1:]
    return digits


@login_required
def receipt_detail(request, pk):

    receipt = _get_receipt(request, pk)

    if request.method == "POST":
        try:
            add_receipt_payment(
                receipt=receipt,
                amount=_money(request.POST.get("amount")),
                method=request.POST.get("method", ""),
                user=request.user,
            )
            messages.success(request, "Payment saved.")
        except ValidationError as error:
            for m in error.messages:
                messages.error(request, m)
        return redirect("receipt_detail", pk=pk)

    previous = []
    if receipt.customer_phone or receipt.customer_name:
        cond = Q()
        if receipt.customer_phone:
            cond |= Q(customer_phone=receipt.customer_phone)
        elif receipt.customer_name:
            cond |= Q(customer_name__iexact=receipt.customer_name)
        previous = list(
            Receipt.objects.filter(cond).exclude(pk=receipt.pk)
            .prefetch_related("sales", "payments")
        )
        if not _is_owner(request.user):
            previous = [r for r in previous
                        if r.employee_id == request.user.id]

    return render(request, "sales/receipt_detail.html", {
        "receipt": receipt,
        "lines": receipt.lines,
        "payments": receipt.payments.all(),
        "methods": METHODS,
        "previous_count": len(previous),
        "previous_total": sum(r.total for r in previous),
        "previous_owed": sum(r.balance for r in previous),
        "whatsapp": _phone_for_whatsapp(receipt.customer_phone),
    })


@login_required
def receipt_print(request, pk):

    receipt = _get_receipt(request, pk)

    return render(request, "sales/receipt_print.html", {
        "receipt": receipt,
        "lines": receipt.lines,
        "payments": receipt.payments.all(),
        "size": "80" if request.GET.get("size") == "80" else "a4",
    })
