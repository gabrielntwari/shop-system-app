from django.db import models
from django.contrib.auth.models import User


class Expense(models.Model):

    CATEGORY_CHOICES = [
        ("rent", "Rent"),
        ("electricity", "Electricity"),
        ("water", "Water"),
        ("internet", "Internet"),
        ("transport", "Transport"),
        ("repairs", "Repairs"),
        ("packaging", "Packaging"),
        ("salary", "Salary"),
        ("other", "Other"),
    ]

    # Employee/Owner can type any expense type
    expense_type = models.CharField(
        max_length=100
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="other"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    description = models.TextField(
        blank=True
    )

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_expenses"
    )

    date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.expense_type} - {self.amount} RWF"
class OwnerWithdrawal(models.Model):

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    description = models.TextField(
        blank=True
    )

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owner_withdrawals"
    )

    date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Owner Withdrawal - {self.amount} RWF"