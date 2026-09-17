from django.db import models
from django.core.exceptions import ValidationError

from sales.models import Sale
from purchase.models import Purchase
from django.contrib.auth.models import User


PAYMENT_METHOD_CHOICES = [
    ("cash", "Cash"),
    ("mobile_money", "Mobile Money"),
    ("bank", "Bank"),
    ("card", "Card"),
    ("other", "Other"),
]


class SaleCreditPayment(models.Model):

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="credit_payments"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES
    )

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    date = models.DateTimeField(
        auto_now_add=True
    )

    def clean(self):

        if self.amount <= 0:
            raise ValidationError({
                "amount": "Payment amount must be greater than 0."
            })

        if self.sale.payment_status != "credit":
            raise ValidationError({
                "sale": "This sale is not a credit transaction."
            })

        already_paid = sum(
            payment.amount
            for payment in self.sale.credit_payments.exclude(
                pk=self.pk
            )
        )

        remaining = self.sale.total_sales() - already_paid

        if self.amount > remaining:
            raise ValidationError({
                "amount": (
                    f"Payment cannot exceed the outstanding "
                    f"credit of {remaining} RWF."
                )
            })

    def __str__(self):
        return f"Sale credit payment - {self.amount} RWF"


class PurchaseCreditPayment(models.Model):

    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name="credit_payments"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES
    )

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    date = models.DateTimeField(
        auto_now_add=True
    )

    def clean(self):

        if self.amount <= 0:
            raise ValidationError({
                "amount": "Payment amount must be greater than 0."
            })

        if self.purchase.payment_status != "credit":
            raise ValidationError({
                "purchase": "This purchase is not a credit transaction."
            })

        already_paid = sum(
            payment.amount
            for payment in self.purchase.credit_payments.exclude(
                pk=self.pk
            )
        )

        remaining = self.purchase.total_cost - already_paid

        if self.amount > remaining:
            raise ValidationError({
                "amount": (
                    f"Payment cannot exceed the outstanding "
                    f"credit of {remaining} RWF."
                )
            })

    def __str__(self):
        return f"Purchase credit payment - {self.amount} RWF"