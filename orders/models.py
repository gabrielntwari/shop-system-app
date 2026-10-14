from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from inventory.models import Product


PAYMENT_METHOD_CHOICES = [
    ("cash", "Cash"),
    ("mobile_money", "Mobile Money"),
    ("bank", "Bank"),
    ("card", "Card"),
    ("other", "Other"),
]


class BusinessPaymentInfo(models.Model):
    """
    Stores the business payment information displayed to customers.

    The owner can update these details from the Payment Settings page.
    """

    business_name = models.CharField(
        max_length=200,
        default="GNT Partners Ltd",
    )

    # ==========================================================
    # MTN MOBILE MONEY
    # ==========================================================

    mtn_momo_number = models.CharField(
        max_length=30,
        blank=True,
    )

    mtn_momo_name = models.CharField(
        max_length=100,
        blank=True,
    )

    # ==========================================================
    # AIRTEL MONEY
    # ==========================================================

    airtel_money_number = models.CharField(
        max_length=30,
        blank=True,
    )

    airtel_money_name = models.CharField(
        max_length=100,
        blank=True,
    )

    # ==========================================================
    # BANK
    # ==========================================================

    bank_name = models.CharField(
        max_length=100,
        blank=True,
    )

    bank_account_name = models.CharField(
        max_length=200,
        blank=True,
    )

    bank_account_number = models.CharField(
        max_length=50,
        blank=True,
    )

    # ==========================================================
    # CARD
    # ==========================================================

    card_instructions = models.CharField(
        max_length=255,
        blank=True,
        help_text=(
            "Example: Card payments accepted at the shop."
        ),
    )

    # ==========================================================
    # OTHER
    # ==========================================================

    other_instructions = models.TextField(
        blank=True,
        help_text="Any other payment instructions for customers.",
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Business Payment Info"
        verbose_name_plural = "Business Payment Info"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Payment info for {self.business_name}"


class Order(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending Payment"),
        ("paid", "Paid"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    order_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        editable=False,
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",
    )

    # ==========================================================
    # CUSTOMER DELIVERY CONTACT
    # ==========================================================

    delivery_email = models.EmailField(
        max_length=254,
        blank=True,
    )

    delivery_phone = models.CharField(
        max_length=30,
        blank=True,
    )

    # ==========================================================
    # DELIVERY ADDRESS
    # ==========================================================

    delivery_address = models.CharField(
        max_length=255,
        blank=True,
        help_text=(
            "District, Sector, Cell/Village, and detailed address."
        ),
    )

    notes = models.TextField(
        blank=True,
    )

    # ==========================================================
    # ORDER STATUS
    # ==========================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_processed",
        help_text=(
            "Employee/owner who marked this order paid or delivered."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.order_number:
            last = (
                Order.objects
                .exclude(order_number="")
                .order_by("-id")
                .first()
            )

            next_seq = 1

            if last and last.order_number.startswith("ORD-"):
                try:
                    next_seq = (
                        int(last.order_number.split("-")[1]) + 1
                    )
                except (IndexError, ValueError):
                    next_seq = last.id + 1

            self.order_number = f"ORD-{next_seq:03d}"

        super().save(*args, **kwargs)

    @property
    def total(self):
        return sum(
            (item.amount for item in self.items.all()),
            0,
        )

    @property
    def latest_proof(self):
        return (
            self.payment_proofs
            .order_by("-uploaded_at")
            .first()
        )

    def __str__(self):
        return (
            f"{self.order_number} - "
            f"{self.customer.username}"
        )


class OrderItem(models.Model):
    """
    A product contained inside an order.

    The product price is copied into this model when the order
    is created so that later product price changes do not alter
    old orders.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="ordered_in",
    )

    quantity = models.PositiveIntegerField(
        default=1,
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text=(
            "Snapshot of the product's price at the time "
            "the order was placed."
        ),
    )

    @property
    def amount(self):
        if self.quantity is None or self.price is None:
            return 0

        return self.quantity * self.price

    def clean(self):
        errors = {}

        if self.quantity is not None and self.quantity <= 0:
            errors["quantity"] = (
                "Quantity must be greater than 0."
            )

        if (
            self.product_id
            and self.quantity is not None
            and self.quantity > self.product.current_stock
        ):
            errors["quantity"] = (
                f"Only {self.product.current_stock} units of "
                f"{self.product.item_name} are currently available."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.product} x {self.quantity}"


def payment_proof_upload_path(instance, filename):
    return (
        f"payment_proofs/"
        f"{instance.order.order_number}/"
        f"{filename}"
    )


class PaymentProof(models.Model):
    """
    Payment evidence uploaded by a customer for an order.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payment_proofs",
    )

    proof_file = models.FileField(
        upload_to=payment_proof_upload_path,
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
    )

    reference_note = models.CharField(
        max_length=255,
        blank=True,
        help_text=(
            "Optional transaction ID / reference from the payment."
        ),
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"Proof for {self.order.order_number} "
            f"({self.uploaded_at:%Y-%m-%d})"
        )