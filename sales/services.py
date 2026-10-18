from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from credit.models import SaleCreditPayment

from .models import Receipt, ReceiptPayment, Sale


def _spread(sales, amount, method, user):
    """
    Share a payment over the receipt's lines, oldest line first.
    Lines fully covered become "paid"; the rest stay "credit" and get a
    SaleCreditPayment so the existing credit pages and dashboards stay right.
    """
    remaining = Decimal(amount)

    for sale in sales:

        if remaining <= 0:
            break

        if sale.payment_status == "paid":
            continue

        owed = sale.total_sales() - sale.total_credit_paid
        part = min(owed, remaining)

        if part > 0:
            SaleCreditPayment.objects.create(
                sale=sale,
                amount=part,
                payment_method=method or "other",
                recorded_by=user,
            )
            remaining -= part


@transaction.atomic
def create_receipt(
    *, user, lines, paid, method, customer_name="", customer_email="",
    customer_phone="", note="", promise_date=None, order_number="",
):
    """
    lines: list of (product, quantity, price).
    Raises ValidationError (nothing is saved) if any line is not allowed.
    """
    if not lines:
        raise ValidationError("Add at least one product.")

    paid = Decimal(paid or 0)
    total = sum((Decimal(q) * Decimal(p) for _, q, p in lines), Decimal(0))

    if paid < 0:
        raise ValidationError("The amount paid cannot be negative.")
    if paid > total:
        raise ValidationError(
            "The amount paid cannot be more than the sale total."
        )
    if paid > 0 and not method:
        raise ValidationError("Please select a payment method.")
    if paid < total and not (customer_name or customer_phone):
        raise ValidationError(
            "Enter the customer's name or phone number when part of the "
            "sale will be paid later."
        )

    receipt = Receipt.objects.create(
        employee=user,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        order_number=order_number,
        note=note,
        promise_date=promise_date,
    )

    sales = []
    for product, qty, price in lines:
        sale = Sale(
            product=product,
            employee=user,
            quantity=qty,
            selling_price=price,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            payment_status="paid" if paid >= total else "credit",
            payment_method=method or "",
            receipt=receipt,
        )
        try:
            # Each saved line lowers the stock seen by the next one,
            # so the same product on two lines is checked correctly.
            sale.full_clean()
        except ValidationError as error:
            msgs = []
            for field_msgs in getattr(error, "message_dict", {}).values():
                msgs.extend(field_msgs)
            raise ValidationError(
                [f"{product}: {m}" for m in (msgs or error.messages)]
            )
        sale.save()
        sales.append(sale)

    if paid > 0:
        ReceiptPayment.objects.create(
            receipt=receipt, amount=paid,
            payment_method=method, recorded_by=user,
        )
        if paid < total:
            _spread(sales, paid, method, user)

    return receipt


@transaction.atomic
def add_receipt_payment(*, receipt, amount, method, user):

    amount = Decimal(amount)
    receipt = Receipt.objects.select_for_update().get(pk=receipt.pk)

    if amount <= 0:
        raise ValidationError("Payment amount must be greater than 0.")
    if not method:
        raise ValidationError("Please select a payment method.")
    if amount > receipt.balance:
        raise ValidationError(
            f"Payment cannot be more than the balance of "
            f"{receipt.balance:,.0f} RWF."
        )

    ReceiptPayment.objects.create(
        receipt=receipt, amount=amount,
        payment_method=method, recorded_by=user,
    )

    sales = [s for s in receipt.sales.order_by("id")
             if s.payment_status == "credit"]
    _spread(sales, amount, method, user)

    return receipt
