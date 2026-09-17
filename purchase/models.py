from django.db import models
from inventory.models import Product
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Purchase(models.Model):

    PAYMENT_STATUS_CHOICES = [
        ("paid", "Paid"),
        ("credit", "Credit"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("cash", "Cash"),
        ("mobile_money", "Mobile Money"),
        ("bank", "Bank"),
        ("card", "Card"),
        ("other", "Other"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="purchases"
    )

    employee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField()

    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    supplier = models.CharField(
        max_length=200
    )

    supplier_email = models.EmailField(
        blank=True
    )

    supplier_phone = models.CharField(
        max_length=30,
        blank=True
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="paid"
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True
    )

    date = models.DateTimeField(
        auto_now_add=True
    )

    @property
    def total_cost(self):
        return self.quantity * self.unit_cost

    @property
    def total_credit_paid(self):
        return sum(
            payment.amount
            for payment in self.credit_payments.all()
        )

    @property
    def outstanding_credit(self):

        if self.payment_status != "credit":
            return 0

        return self.total_cost - self.total_credit_paid

    @property
    def credit_cleared(self):
        return self.outstanding_credit <= 0

    def clean(self):

        errors = {}

        if self.quantity <= 0:
            errors["quantity"] = (
                "Quantity must be greater than 0."
            )

        if self.unit_cost <= 0:
            errors["unit_cost"] = (
                "Unit cost must be greater than 0."
            )

        if self.payment_status == "paid" and not self.payment_method:
            errors["payment_method"] = (
                "Please select a payment method."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.product} - {self.quantity}"