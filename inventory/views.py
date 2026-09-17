from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Product
from .forms import ProductForm


# =========================================================
# ADD PRODUCT
# =========================================================

@login_required
def add_product(request):

    # Only owner can manually add products
    if not request.user.groups.filter(name="owner").exists():
        raise PermissionDenied

    if request.method == "POST":

        form = ProductForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect("owner_inventory")

    else:

        form = ProductForm()

    return render(
        request,
        "owner/add_product.html",
        {
            "form": form
        }
    )


# =========================================================
# UPDATE PRODUCT
# =========================================================

@login_required
def update_product(request, product_id):

    # Only owner can change product information
    if not request.user.groups.filter(name="owner").exists():
        raise PermissionDenied

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            instance=product
        )

        if form.is_valid():

            form.save()

            return redirect("owner_inventory")

    else:

        form = ProductForm(
            instance=product
        )

    return render(
        request,
        "owner/update_product.html",
        {
            "form": form,
            "product": product,
        }
    )


# =========================================================
# OWNER INVENTORY
# =========================================================

@login_required
def owner_inventory(request):

    # Only owner can view the owner inventory
    if not request.user.groups.filter(name="owner").exists():
        raise PermissionDenied

    products = Product.objects.all().order_by("-created_at")

    # A product is NEW only for 24 hours
    new_product_limit = timezone.now() - timedelta(hours=24)

    for product in products:

        product.is_new = (
            product.created_at >= new_product_limit
        )

    return render(
        request,
        "owner/inventory.html",
        {
            "products": products,
        }
    )
