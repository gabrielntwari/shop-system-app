from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce


class Category(models.Model):

    name = models.CharField(max_length=100, unique=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):

    TIER_CHOICES = [
        ("", "Normal"),
        ("standard", "Standard"),
        ("hot", "Hot"),
    ]

    SOURCE_CHOICES = [
        ("own_stock", "Own Stock"),
        ("supplier", "External Supplier"),
    ]

    item_name = models.CharField(
        max_length=200
    )

    brand = models.CharField(
        max_length=100,
        blank=True
    )

    specification = models.CharField(
        max_length=200,
        blank=True
    )

    minimum_selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    photo = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
        help_text="Optional main photo of the product, shown to customers in the shop catalog.",
    )

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES
    )

    # ---- Shop (customer side) fields ----
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )

    display_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price shown to customers. Leave empty to show the minimum selling price.",
    )

    tier = models.CharField(
        max_length=10,
        choices=TIER_CHOICES,
        blank=True,
        default="",
    )

    description = models.TextField(blank=True)

    show_in_shop = models.BooleanField(default=True)

    # Records when the product was first created.
    # Used for the temporary NEW badge in Inventory.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "item_name",
                    "brand",
                    "specification",
                ],
                name="unique_product_brand_specification"
            )
        ]

    @property
    def shop_images(self):
        """Image URLs for the shop: main photo first, then the gallery."""
        urls = []
        if self.photo:
            urls.append(self.photo.url)
        for extra in self.photos.all():
            urls.append(extra.image.url)
        return urls

    @property
    def shop_price(self):
        return self.display_price or self.minimum_selling_price

    @property
    def current_stock(self):

        total_purchased = self.purchases.aggregate(
            total=Coalesce(
                Sum("quantity"),
                0
            )
        )["total"]

        total_sold = self.sales.aggregate(
            total=Coalesce(
                Sum("quantity"),
                0
            )
        )["total"]

        return total_purchased - total_sold

    def __str__(self):

        parts = [self.item_name]

        if self.brand:
            parts.append(self.brand)

        if self.specification:
            parts.append(self.specification)

        return " - ".join(parts)


class ProductPhoto(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="photos"
    )

    image = models.ImageField(
        upload_to="products/gallery/"
    )

    position = models.PositiveSmallIntegerField(
        choices=[
            (1, "Photo 1"),
            (2, "Photo 2"),
            (3, "Photo 3"),
        ]
    )

    class Meta:
        ordering = ["position"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "product",
                    "position",
                ],
                name="unique_product_photo_position"
            )
        ]

    def __str__(self):
        return f"{self.product.item_name} - Photo {self.position}"


class ProductSpec(models.Model):

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="specs"
    )
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.label}: {self.value}"


class ProductColor(models.Model):

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="colors"
    )
    name = models.CharField(max_length=50)
    hex_code = models.CharField(
        max_length=7, default="#888888",
        help_text="Colour swatch, e.g. #1d4ed8",
    )
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.product.item_name} - {self.name}"
