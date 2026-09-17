from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Proforma(models.Model):

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("accepted", "Accepted"),
        ("expired", "Expired"),
        ("converted", "Converted to Invoice"),
    ]

    # ==========================================================
    # NUMBERING
    # ==========================================================

    proforma_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        editable=False,
    )

    # ==========================================================
    # CLIENT DETAILS
    # ==========================================================

    client_name = models.CharField(
        max_length=200
    )

    client_address = models.CharField(
        max_length=255,
        blank=True
    )

    client_phone = models.CharField(
        max_length=30,
        blank=True
    )

    client_email = models.EmailField(
        blank=True
    )

    purpose = models.CharField(
        max_length=255,
        blank=True,
        help_text="What this proforma is for, e.g. 'Solar lights and CCTV installation'.",
    )

    # ==========================================================
    # DATES
    # ==========================================================

    date = models.DateField(
        default=timezone.localdate
    )

    valid_until = models.DateField(
        blank=True,
        null=True,
    )

    # ==========================================================
    # CHARGES
    # ==========================================================

    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18.00,
        help_text="Percentage, e.g. 18.00 for 18%.",
    )

    other_costs = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    other_costs_description = models.CharField(
        max_length=200,
        blank=True,
    )

    # ==========================================================
    # STATUS / AUDIT
    # ==========================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    # ==========================================================
    # AUTO NUMBERING (PF-001, PF-002, ...)
    # ==========================================================

    def save(self, *args, **kwargs):

        if not self.proforma_number:

            last = (
                Proforma.objects
                .exclude(proforma_number="")
                .order_by("-id")
                .first()
            )

            next_seq = 1

            if last and last.proforma_number.startswith("PF-"):

                try:
                    next_seq = int(last.proforma_number.split("-")[1]) + 1
                except (IndexError, ValueError):
                    next_seq = last.id + 1

            self.proforma_number = f"PF-{next_seq:03d}"

        if self.valid_until is None and self.date:
            self.valid_until = self.date + timedelta(days=14)

        super().save(*args, **kwargs)

    # ==========================================================
    # TOTALS
    # ==========================================================

    @property
    def subtotal(self):

        return sum(
            (item.amount for item in self.items.all()),
            0,
        )

    @property
    def tax_amount(self):

        return (self.subtotal * self.tax_rate) / 100

    @property
    def total(self):

        return self.subtotal + self.tax_amount + (self.other_costs or 0)

    @property
    def is_expired(self):

        if not self.valid_until:
            return False

        return timezone.localdate() > self.valid_until

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def clean(self):

        errors = {}

        if not self.client_name:

            errors["client_name"] = (
                "Client name is required."
            )

        if self.tax_rate is not None and self.tax_rate < 0:

            errors["tax_rate"] = (
                "Tax rate cannot be negative."
            )

        if self.other_costs is not None and self.other_costs < 0:

            errors["other_costs"] = (
                "Other costs cannot be negative."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):

        return f"{self.proforma_number} - {self.client_name}"


class ProformaItem(models.Model):

    proforma = models.ForeignKey(
        Proforma,
        on_delete=models.CASCADE,
        related_name="items",
    )

    description = models.CharField(
        max_length=255
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    # ==========================================================
    # AMOUNT
    # ==========================================================

    @property
    def amount(self):

        if self.quantity is None or self.rate is None:
            return 0

        return self.quantity * self.rate

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def clean(self):

        errors = {}

        if not self.description:

            errors["description"] = (
                "Item description is required."
            )

        if self.quantity is not None and self.quantity <= 0:

            errors["quantity"] = (
                "Quantity must be greater than 0."
            )

        if self.rate is not None and self.rate <= 0:

            errors["rate"] = (
                "Rate must be greater than 0."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):

        return f"{self.description} ({self.quantity} x {self.rate})"
