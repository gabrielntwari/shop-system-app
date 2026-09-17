from django import forms
from .models import Product


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product

        fields = [
            "item_name",
            "brand",
            "specification",
            "minimum_selling_price",
            "source",
        ]

        widgets = {

            "item_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter product name",
            }),

            "brand": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter brand",
            }),

            "specification": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter specification",
            }),

            "minimum_selling_price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter minimum selling price",
                "step": "0.01",
                "min": "0",
            }),

            "source": forms.Select(attrs={
                "class": "form-control",
            }),
        }