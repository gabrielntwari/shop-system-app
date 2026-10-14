from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce


class Product(models.Model):

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