from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from sales.models import Sale
from purchase.models import Purchase

from .forms import (
    SaleCreditPaymentForm,
    PurchaseCreditPaymentForm,
)

from .models import (
    SaleCreditPayment,
    PurchaseCreditPayment,
)


def can_manage_credits(user):
    return (
        user.groups.filter(name="owner").exists()
        or user.groups.filter(name="employee").exists()
    )


# ============================================================
# SALE CREDIT PAYMENT
# ============================================================

@login_required
def pay_sale_credit(request, sale_id):

    sale = get_object_or_404(
        Sale,
        id=sale_id
    )

    # Employee can only record payment
    # for a credit sale they created.
    if request.user.groups.filter(name="employee").exists():

        if sale.employee != request.user:
            raise PermissionDenied

    # Owner can record payment for any credit sale.
    elif not request.user.groups.filter(name="owner").exists():

        raise PermissionDenied

    if sale.payment_status != "credit":
        messages.error(
            request,
            "This sale is not a credit transaction."
        )
        return redirect("dashboard")

    if sale.credit_cleared:
        messages.error(
            request,
            "This credit has already been fully paid."
        )
        return redirect("dashboard")

    if request.method == "POST":

        # IMPORTANT:
        # Attach the sale BEFORE form validation.
        payment_instance = SaleCreditPayment(
            sale=sale,
            recorded_by=request.user
        )

        form = SaleCreditPaymentForm(
            request.POST,
            instance=payment_instance
        )

        if form.is_valid():

            try:
                payment = form.save()

                return redirect("dashboard")

            except ValidationError as error:
                form.add_error(None, error)

    else:

        payment_instance = SaleCreditPayment(
            sale=sale,
            recorded_by=request.user
        )

        form = SaleCreditPaymentForm(
            instance=payment_instance
        )

    return render(
        request,
        "credit/pay_sale_credit.html",
        {
            "form": form,
            "sale": sale,
        }
    )
@login_required
def pay_purchase_credit(request, purchase_id):

    purchase = get_object_or_404(
        Purchase,
        id=purchase_id
    )

    # Employee can only record payment
    # for a credit purchase they created.
    if request.user.groups.filter(name="employee").exists():

        if purchase.employee != request.user:
            raise PermissionDenied

    # Owner can record payment for any credit purchase.
    elif not request.user.groups.filter(name="owner").exists():

        raise PermissionDenied

    if purchase.payment_status != "credit":
        messages.error(
            request,
            "This purchase is not a credit transaction."
        )
        return redirect("dashboard")

    if purchase.credit_cleared:
        messages.error(
            request,
            "This credit has already been fully paid."
        )
        return redirect("dashboard")

    if request.method == "POST":

        # IMPORTANT:
        # Attach the purchase BEFORE form validation.
        payment_instance = PurchaseCreditPayment(
            purchase=purchase,
            recorded_by=request.user
        )

        form = PurchaseCreditPaymentForm(
            request.POST,
            instance=payment_instance
        )

        if form.is_valid():

            try:
                payment = form.save()

                return redirect("dashboard")

            except ValidationError as error:
                form.add_error(None, error)

    else:

        payment_instance = PurchaseCreditPayment(
            purchase=purchase,
            recorded_by=request.user
        )

        form = PurchaseCreditPaymentForm(
            instance=payment_instance
        )

    return render(
        request,
        "credit/pay_purchase_credit.html",
        {
            "form": form,
            "purchase": purchase,
        }
    )
# ============================================================
# OWNER SALE CREDITS
# ============================================================

@login_required
def owner_sale_credits(request):

    if not request.user.groups.filter(name="owner").exists():
        raise PermissionDenied

    sales = Sale.objects.filter(
        payment_status="credit"
    ).select_related(
        "product",
        "employee"
    ).prefetch_related(
        "credit_payments"
    )

    status = request.GET.get(
        "status",
        "outstanding"
    )

    if status == "outstanding":

        sales = [
            sale
            for sale in sales
            if not sale.credit_cleared
        ]

    elif status == "cleared":

        sales = [
            sale
            for sale in sales
            if sale.credit_cleared
        ]

    total_original = sum(
        sale.total_sales()
        for sale in sales
    )

    total_paid = sum(
        sale.total_credit_paid
        for sale in sales
    )

    total_outstanding = sum(
        sale.outstanding_credit
        for sale in sales
    )

    return render(
        request,
        "credit/owner_sale_credits.html",
        {
            "sales": sales,
            "selected_status": status,
            "total_original": total_original,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
        }
    )


# ============================================================
# OWNER PURCHASE CREDITS
# ============================================================

@login_required
def owner_purchase_credits(request):

    if not request.user.groups.filter(name="owner").exists():
        raise PermissionDenied

    purchases = Purchase.objects.filter(
        payment_status="credit"
    ).select_related(
        "product",
        "employee"
    ).prefetch_related(
        "credit_payments"
    )

    status = request.GET.get(
        "status",
        "outstanding"
    )

    if status == "outstanding":

        purchases = [
            purchase
            for purchase in purchases
            if not purchase.credit_cleared
        ]

    elif status == "cleared":

        purchases = [
            purchase
            for purchase in purchases
            if purchase.credit_cleared
        ]

    total_original = sum(
        purchase.total_cost
        for purchase in purchases
    )

    total_paid = sum(
        purchase.total_credit_paid
        for purchase in purchases
    )

    total_outstanding = sum(
        purchase.outstanding_credit
        for purchase in purchases
    )

    return render(
        request,
        "credit/owner_purchase_credits.html",
        {
            "purchases": purchases,
            "selected_status": status,
            "total_original": total_original,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
        }
    )


# ============================================================
# EMPLOYEE SALE CREDITS
# ============================================================

@login_required
def employee_sale_credits(request):

    if not request.user.groups.filter(name="employee").exists():
        raise PermissionDenied

    sales = Sale.objects.filter(
        employee=request.user,
        payment_status="credit"
    ).select_related(
        "product",
        "employee"
    ).prefetch_related(
        "credit_payments"
    )

    status = request.GET.get(
        "status",
        "outstanding"
    )

    if status == "outstanding":

        sales = [
            sale
            for sale in sales
            if not sale.credit_cleared
        ]

    elif status == "cleared":

        sales = [
            sale
            for sale in sales
            if sale.credit_cleared
        ]

    total_original = sum(
        sale.total_sales()
        for sale in sales
    )

    total_paid = sum(
        sale.total_credit_paid
        for sale in sales
    )

    total_outstanding = sum(
        sale.outstanding_credit
        for sale in sales
    )

    return render(
        request,
        "credit/employee_sale_credits.html",
        {
            "sales": sales,
            "selected_status": status,
            "total_original": total_original,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
        }
    )


# ============================================================
# EMPLOYEE PURCHASE CREDITS
# ============================================================

@login_required
def employee_purchase_credits(request):

    if not request.user.groups.filter(name="employee").exists():
        raise PermissionDenied

    purchases = Purchase.objects.filter(
        employee=request.user,
        payment_status="credit"
    ).select_related(
        "product",
        "employee"
    ).prefetch_related(
        "credit_payments"
    )

    status = request.GET.get(
        "status",
        "outstanding"
    )

    if status == "outstanding":

        purchases = [
            purchase
            for purchase in purchases
            if not purchase.credit_cleared
        ]

    elif status == "cleared":

        purchases = [
            purchase
            for purchase in purchases
            if purchase.credit_cleared
        ]

    total_original = sum(
        purchase.total_cost
        for purchase in purchases
    )

    total_paid = sum(
        purchase.total_credit_paid
        for purchase in purchases
    )

    total_outstanding = sum(
        purchase.outstanding_credit
        for purchase in purchases
    )

    return render(
        request,
        "credit/employee_purchase_credits.html",
        {
            "purchases": purchases,
            "selected_status": status,
            "total_original": total_original,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
        }
    )
