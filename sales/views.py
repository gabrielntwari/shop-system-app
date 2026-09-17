from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError

from .forms import SaleForm


@login_required
def add_sale(request):

    if not (
        request.user.groups.filter(name="owner").exists()
        or request.user.groups.filter(name="employee").exists()
    ):
        raise PermissionDenied

    if request.method == "POST":

        form = SaleForm(request.POST)

        if form.is_valid():

            sale = form.save(commit=False)

            # Automatically record who made the transaction
            sale.employee = request.user

            try:
                sale.full_clean()
                sale.save()

                return redirect("dashboard")

            except ValidationError as error:
                form.add_error(None, error)

    else:
        form = SaleForm()

    return render(
        request,
        "sales/add_sale.html",
        {"form": form}
    )