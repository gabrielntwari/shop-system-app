from django.contrib import admin

from .models import Product, ProductPhoto


class ProductPhotoInline(admin.TabularInline):
    model = ProductPhoto
    extra = 3
    max_num = 3


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "item_name",
        "brand",
        "specification",
        "minimum_selling_price",
        "source",
        "current_stock",
        "created_at",
    )

    search_fields = (
        "item_name",
        "brand",
        "specification",
    )

    list_filter = (
        "source",
        "created_at",
    )

    readonly_fields = (
        "current_stock",
        "created_at",
    )

    inlines = [
        ProductPhotoInline,
    ]


@admin.register(ProductPhoto)
class ProductPhotoAdmin(admin.ModelAdmin):

    list_display = (
        "product",
        "position",
    )

    list_filter = (
        "position",
    )

    search_fields = (
        "product__item_name",
        "product__brand",
    )