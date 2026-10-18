from django import forms
from django.forms import inlineformset_factory
from .models import Category, Product, ProductColor, ProductSpec


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product

        fields = [
            "item_name",
            "brand",
            "specification",
            "minimum_selling_price",
            "photo",
            "source",
            "category",
            "display_price",
            "tier",
            "show_in_shop",
            "description",
        ]

        widgets = {

            "photo": forms.ClearableFileInput(attrs={
                "class": "form-control",
            }),

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

            "category": forms.Select(attrs={"class": "form-control"}),

            "display_price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Price customers see (optional)",
                "step": "0.01",
                "min": "0",
            }),

            "tier": forms.Select(attrs={"class": "form-control"}),

            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe the product for customers",
            }),
        }

    def clean(self):
        cleaned = super().clean()
        display = cleaned.get("display_price")
        minimum = cleaned.get("minimum_selling_price")
        if display is not None and minimum is not None and display < minimum:
            self.add_error(
                "display_price",
                "The display price cannot be lower than the minimum selling price.",
            )
        return cleaned


class CategoryForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = ["name", "position"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Category name"}),
            "position": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
        }


_spec_widgets = {
    "label": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Screen"}),
    "value": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 6.5 inch"}),
}

_color_widgets = {
    "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Black"}),
    "hex_code": forms.TextInput(attrs={"type": "color", "class": "color-input"}),
}

SpecFormSet = inlineformset_factory(
    Product, ProductSpec, fields=["label", "value"],
    widgets=_spec_widgets, extra=0, can_delete=True,
)

ColorFormSet = inlineformset_factory(
    Product, ProductColor, fields=["name", "hex_code"],
    widgets=_color_widgets, extra=0, can_delete=True,
)