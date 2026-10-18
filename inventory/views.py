
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST

from .models import Category, Product, ProductPhoto
from .forms import CategoryForm, ColorFormSet, ProductForm, SpecFormSet


# =========================================================
# STAFF PERMISSION HELPER
# =========================================================

def staff_user(request):
    return (
        request.user.groups.filter(name="owner").exists()
        or request.user.groups.filter(name="employee").exists()
    )


def _save_ordered(formset):
    """Save an inline formset, keeping rows in the order entered."""
    for index, form in enumerate(formset.forms):
        form.instance.position = index
    objs = formset.save(commit=False)
    for obj in formset.deleted_objects:
        obj.delete()
    for obj in objs:
        obj.save()


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

        specs = SpecFormSet(request.POST, prefix="specs")
        colors = ColorFormSet(request.POST, prefix="colors")

        if form.is_valid() and specs.is_valid() and colors.is_valid():

            with transaction.atomic():
                product = form.save()
                specs.instance = product
                colors.instance = product
                _save_ordered(specs)
                _save_ordered(colors)

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
        specs = SpecFormSet(prefix="specs")
        colors = ColorFormSet(prefix="colors")

    return render(
        request,
        "owner/add_product.html",
        {
            "form": form,
            "specs": specs,
            "colors": colors,
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

        specs = SpecFormSet(request.POST, instance=product, prefix="specs")
        colors = ColorFormSet(request.POST, instance=product, prefix="colors")

        if form.is_valid() and specs.is_valid() and colors.is_valid():

            with transaction.atomic():
                product = form.save()
                _save_ordered(specs)
                _save_ordered(colors)

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
        specs = SpecFormSet(instance=product, prefix="specs")
        colors = ColorFormSet(instance=product, prefix="colors")

    return render(
        request,
        "owner/update_product.html",
        {
            "form": form,
            "product": product,
            "specs": specs,
            "colors": colors,
        }
    )


# =========================================================
# OWNER / STAFF INVENTORY
# =========================================================

@login_required
def owner_inventory(request):

    if not staff_user(request):
        raise PermissionDenied

    products = Product.objects.select_related("category").order_by("-created_at")

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



# =========================================================
# QUICK TIER CHANGE (Hot / Standard) FROM THE INVENTORY LIST
# =========================================================

@login_required
@require_POST
def set_product_tier(request, product_id):

    if not staff_user(request):
        raise PermissionDenied

    product = get_object_or_404(Product, id=product_id)
    tier = request.POST.get("tier", "")

    if tier in dict(Product.TIER_CHOICES):
        product.tier = tier
        product.save(update_fields=["tier"])

    return redirect("owner_inventory")


# =========================================================
# CATEGORIES
# =========================================================

@login_required
def manage_categories(request):

    if not staff_user(request):
        raise PermissionDenied

    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category added.")
            return redirect("manage_categories")
    else:
        form = CategoryForm()

    from django.db.models import Count

    return render(
        request,
        "owner/categories.html",
        {
            "form": form,
            "categories": Category.objects.annotate(n=Count("products")),
        },
    )


@login_required
@require_POST
def edit_category(request, category_id):

    if not staff_user(request):
        raise PermissionDenied

    category = get_object_or_404(Category, id=category_id)

    if request.POST.get("action") == "delete":
        category.delete()
        messages.success(request, "Category deleted. Its products are now uncategorised.")
    else:
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated.")
        else:
            messages.error(request, "Could not update category (name must be unique).")

    return redirect("manage_categories")
