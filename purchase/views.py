from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import render, redirect

from .forms import PurchaseForm
from inventory.models import Product


@login_required
def add_purchase(request):

    # =====================================================
    # ACCESS CONTROL
    # =====================================================

    if not (
        request.user.groups.filter(
            name="owner"
        ).exists()

        or

        request.user.groups.filter(
            name="employee"
        ).exists()
    ):

        raise PermissionDenied

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        form = PurchaseForm(
            request.POST
        )

        if form.is_valid():

            try:

                # -----------------------------------------
                # CREATE NEW PRODUCT IF REQUESTED
                # -----------------------------------------

                if form.cleaned_data.get(
                    "add_new_product"
                ):

                    product = Product.objects.create(

                        item_name=form.cleaned_data[
                            "new_product_name"
                        ].strip(),

                        brand=form.cleaned_data[
                            "new_product_brand"
                        ].strip(),

                        specification=(
                            form.cleaned_data[
                                "new_product_specification"
                            ].strip()
                            if form.cleaned_data[
                                "new_product_specification"
                            ]
                            else ""
                        ),

                        minimum_selling_price=(
                            form.cleaned_data[
                                "new_product_minimum_price"
                            ]
                        ),

                        source=form.cleaned_data[
                            "new_product_source"
                        ],
                    )

                # -----------------------------------------
                # USE EXISTING PRODUCT
                # -----------------------------------------

                else:

                    product = form.cleaned_data[
                        "product"
                    ]

                # -----------------------------------------
                # CREATE PURCHASE
                # -----------------------------------------

                purchase = form.save(
                    commit=False
                )

                purchase.product = product

                # Automatically record who made
                # the purchase.

                purchase.employee = request.user

                purchase.full_clean()

                purchase.save()

                return redirect(
                    "dashboard"
                )

            except ValidationError as error:

                form.add_error(
                    None,
                    error
                )

    # =====================================================
    # GET
    # =====================================================

    else:

        form = PurchaseForm()

    # =====================================================
    # RENDER
    # =====================================================

    return render(
        request,
        "purchase/add_purchase.html",
        {
            "form": form
        }
    )