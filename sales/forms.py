from django import forms

from .models import Sale
from inventory.models import Product


class SaleForm(forms.ModelForm):

    class Meta:
        model = Sale

        fields = [
            "product",
            "quantity",
            "selling_price",
            "customer_name",
            "customer_email",
            "customer_phone",
            "payment_status",
            "payment_method",
        ]

        widgets = {

            "product": forms.Select(attrs={
                "class": "form-control",
            }),

            "selling_price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter selling price",
                "step": "0.01",
                "min": "0",
            }),

            "customer_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Customer name (optional)",
            }),

            "customer_email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Customer email (optional)",
            }),

            "customer_phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Customer phone (optional)",
            }),

            "payment_status": forms.Select(attrs={
                "class": "form-control",
            }),

            "payment_method": forms.Select(attrs={
                "class": "form-control",
            }),
        }

    quantity = forms.IntegerField(
        min_value=1,
        error_messages={
            "required": "Please enter a quantity.",
            "min_value": "Quantity must be greater than 0.",
            "invalid": "Please enter a valid whole number.",
        },
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "min": "1",
            "placeholder": "Enter quantity",
        })
    )

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Only show products that currently have stock available.
        available_products = [
            product
            for product in Product.objects.all()
            if product.current_stock > 0
        ]

        self.fields["product"].queryset = Product.objects.filter(
            id__in=[product.id for product in available_products]
        )

        self.fields["product"].empty_label = "Select available product"

    def clean(self):

        cleaned_data = super().clean()

        product = cleaned_data.get("product")
        quantity = cleaned_data.get("quantity")
        selling_price = cleaned_data.get("selling_price")

        if product and quantity:

            if quantity > product.current_stock:
                self.add_error(
                    "quantity",
                    f"Only {product.current_stock} units are available."
                )

        if product and selling_price:

            if selling_price < product.minimum_selling_price:
                self.add_error(
                    "selling_price",
                    (
                        f"Selling price cannot be below the "
                        f"minimum price of "
                        f"{product.minimum_selling_price} RWF."
                    )
                )

        payment_status = cleaned_data.get("payment_status")
        payment_method = cleaned_data.get("payment_method")

        if payment_status == "paid" and not payment_method:
            self.add_error(
                "payment_method",
                "Please select a payment method for a paid sale."
            )

        return cleaned_data