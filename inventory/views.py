
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Product, ProductPhoto
from .forms import ProductForm


# =========================================================
# STAFF PERMISSION HELPER
# =========================================================

def staff_user(request):
    return (
        request.user.groups.filter(name="owner").exists()
        or request.user.groups.filter(name="employee").exists()
    )


# =========================================================
# ADD PRODUCT
# =========================================================

@login_required
def add_product(request):

    if not staff_user(request):
        raise PermissionDenied

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            product = form.save()

            # -------------------------------------------------
            # SAVE UP TO 3 GALLERY PHOTOS
            # -------------------------------------------------

            for position in range(1, 4):

                photo = request.FILES.get(
                    f"gallery_photo_{position}"
                )

                if photo:
                    ProductPhoto.objects.create(
                        product=product,
                        image=photo,
                        position=position
                    )

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

    if not staff_user(request):
        raise PermissionDenied

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product
        )

        if form.is_valid():

            product = form.save()

            # -------------------------------------------------
            # UPDATE GALLERY PHOTOS
            # -------------------------------------------------

            for position in range(1, 4):

                photo = request.FILES.get(
                    f"gallery_photo_{position}"
                )

                if photo:

                    ProductPhoto.objects.update_or_create(
                        product=product,
                        position=position,
                        defaults={
                            "image": photo
                        }
                    )

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
# OWNER / STAFF INVENTORY
# =========================================================

@login_required
def owner_inventory(request):

    if not staff_user(request):
        raise PermissionDenied

    products = Product.objects.all().order_by("-created_at")

    # Product is NEW for 24 hours
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
