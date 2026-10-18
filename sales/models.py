from django.db import models
from inventory.models import Product
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Sale(models.Model):

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
        related_name="sales"
    )

    employee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField()

    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    customer_name = models.CharField(
        max_length=200,
        blank=True
    )

    customer_email = models.EmailField(
        blank=True
    )

    customer_phone = models.CharField(
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

    # The receipt this line belongs to (older sales have none).
    receipt = models.ForeignKey(
        "sales.Receipt",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales",
    )

    # ==========================================================
    # TOTAL SALE
    # ==========================================================

    def total_sales(self):
        return self.quantity * self.selling_price

    # ==========================================================
    # CREDIT PAYMENT TOTAL
    # ==========================================================

    @property
    def total_credit_paid(self):

        return sum(
            payment.amount
            for payment in self.credit_payments.all()
        )

    # ==========================================================
    # OUTSTANDING CREDIT
    # ==========================================================

    @property
    def outstanding_credit(self):

        if self.payment_status != "credit":
            return 0

        return self.total_sales() - self.total_credit_paid

    # ==========================================================
    # CREDIT STATUS
    # ==========================================================

    @property
    def credit_cleared(self):

        return self.outstanding_credit <= 0

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def clean(self):

        errors = {}

        # ------------------------------------------------------
        # QUANTITY
        # ------------------------------------------------------

        if self.quantity is None:

            errors["quantity"] = (
                "Quantity is required."
            )

        elif self.quantity <= 0:

            errors["quantity"] = (
                "Quantity must be greater than 0."
            )

        # ------------------------------------------------------
        # SELLING PRICE
        # ------------------------------------------------------

        if self.selling_price is None:

            errors["selling_price"] = (
                "Selling price is required."
            )

        elif self.selling_price <= 0:

            errors["selling_price"] = (
                "Selling price must be greater than 0."
            )

        # ------------------------------------------------------
        # STOCK VALIDATION
        # ------------------------------------------------------

        if (
            self.product_id
            and self.quantity is not None
            and self.quantity > self.product.current_stock
        ):

            errors["quantity"] = (
                f"Not enough stock. "
                f"Available stock is "
                f"{self.product.current_stock}."
            )

        # ------------------------------------------------------
        # MINIMUM SELLING PRICE
        # ------------------------------------------------------

        if (
            self.product_id
            and self.selling_price is not None
            and self.product.minimum_selling_price is not None
            and self.selling_price
            < self.product.minimum_selling_price
        ):

            errors["selling_price"] = (
                f"Selling price cannot be below "
                f"the minimum price of "
                f"{self.product.minimum_selling_price}."
            )

        # ------------------------------------------------------
        # PAYMENT METHOD
        # ------------------------------------------------------

        if (
            self.payment_status == "paid"
            and not self.payment_method
        ):

            errors["payment_method"] = (
                "Please select a payment method."
            )

        # ------------------------------------------------------
        # RAISE VALIDATION ERRORS
        # ------------------------------------------------------

        if errors:

            raise ValidationError(errors)

    # ==========================================================
    # STRING
    # ==========================================================

    def __str__(self):

        return f"{self.product} - {self.quantity}"

# ==============================================================
# RECEIPTS  (one receipt groups many Sale lines)
# ==============================================================

class Receipt(models.Model):

    employee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="receipts",
    )
    customer_name = models.CharField(max_length=200, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=30, blank=True)

    # Filled when the receipt comes from a website order.
    order_number = models.CharField(max_length=30, blank=True)

    note = models.CharField(max_length=300, blank=True)
    promise_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    @property
    def number(self):
        return f"RCT-{self.pk:04d}"

    @property
    def lines(self):
        return self.sales.select_related("product").order_by("id")

    @property
    def total(self):
        return sum((s.total_sales() for s in self.sales.all()), 0)

    @property
    def paid(self):
        return sum((p.amount for p in self.payments.all()), 0)

    @property
    def balance(self):
        return self.total - self.paid

    @property
    def is_paid(self):
        return self.balance <= 0

    @property
    def items_count(self):
        return self.sales.count()

    @property
    def units_count(self):
        return sum(s.quantity for s in self.sales.all())

    @property
    def source_label(self):
        if self.order_number:
            return f"Website order {self.order_number}"
        return "Counter sale"

    def __str__(self):
        return self.number


class ReceiptPayment(models.Model):

    receipt = models.ForeignKey(
        Receipt, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(
        max_length=30, choices=Sale.PAYMENT_METHOD_CHOICES, blank=True
    )
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "id"]

    def __str__(self):
        return f"{self.receipt.number} payment {self.amount}"
