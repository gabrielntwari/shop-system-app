from django import forms

from .models import Purchase
from inventory.models import Product


class PurchaseForm(forms.ModelForm):

    # =====================================================
    # NEW PRODUCT OPTION
    # =====================================================

    add_new_product = forms.BooleanField(
        required=False,
        label="Add a new product",
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "add-new-product-checkbox",
            }
        )
    )

    new_product_name = forms.CharField(
        required=False,
        label="Product Name",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter product name",
                "id": "new-product-name",
            }
        )
    )

    new_product_brand = forms.CharField(
        required=False,
        label="Brand",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter brand",
                "id": "new-product-brand",
            }
        )
    )

    new_product_specification = forms.CharField(
        required=False,
        label="Specification",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Example: Size 5",
                "id": "new-product-specification",
            }
        )
    )

    new_product_minimum_price = forms.DecimalField(
        required=False,
        label="Minimum Selling Price",
        min_value=0.01,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Minimum selling price",
                "step": "0.01",
                "min": "0.01",
                "id": "new-product-minimum-price",
            }
        )
    )

    new_product_source = forms.ChoiceField(
        required=False,
        label="Product Source",
        choices=Product.SOURCE_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "id": "new-product-source",
            }
        )
    )

    class Meta:

        model = Purchase

        fields = [
            "product",
            "quantity",
            "unit_cost",
            "supplier",
            "supplier_email",
            "supplier_phone",
            "payment_status",
            "payment_method",
        ]

        widgets = {

            "product": forms.Select(
                attrs={
                    "class": "form-control",
                    "id": "existing-product",
                }
            ),

            "unit_cost": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter unit cost",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),

            "supplier": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Supplier name",
                }
            ),

            "supplier_email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Supplier email (optional)",
                }
            ),

            "supplier_phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Supplier phone (optional)",
                }
            ),

            "payment_status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "payment_method": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    # =====================================================
    # QUANTITY
    # =====================================================

    quantity = forms.IntegerField(
        min_value=1,
        error_messages={
            "required": "Please enter a quantity.",
            "min_value": "Quantity must be greater than 0.",
            "invalid": "Please enter a valid whole number.",
        },
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "1",
                "placeholder": "Enter quantity",
            }
        )
    )

    # =====================================================
    # INITIALIZE FORM
    # =====================================================

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["product"].queryset = Product.objects.all()

        self.fields["product"].empty_label = (
            "Select existing product"
        )

        # IMPORTANT:
        # Product is optional because the user can choose
        # "Add New Product" instead.
        self.fields["product"].required = False

    # =====================================================
    # VALIDATION
    # =====================================================

    def clean(self):

        cleaned_data = super().clean()

        add_new_product = cleaned_data.get(
            "add_new_product"
        )

        product = cleaned_data.get(
            "product"
        )

        # =================================================
        # EXISTING PRODUCT
        # =================================================

        if not add_new_product:

            if not product:

                self.add_error(
                    "product",
                    (
                        "Please select a product or "
                        "choose Add New Product."
                    )
                )

        # =================================================
        # NEW PRODUCT
        # =================================================

        if add_new_product:

            product_name = cleaned_data.get(
                "new_product_name"
            )

            brand = cleaned_data.get(
                "new_product_brand"
            )

            specification = cleaned_data.get(
                "new_product_specification"
            )

            minimum_price = cleaned_data.get(
                "new_product_minimum_price"
            )

            source = cleaned_data.get(
                "new_product_source"
            )

            if not product_name:

                self.add_error(
                    "new_product_name",
                    "Please enter the product name."
                )

            if not brand:

                self.add_error(
                    "new_product_brand",
                    "Please enter the brand."
                )

            if not minimum_price:

                self.add_error(
                    "new_product_minimum_price",
                    "Please enter the minimum selling price."
                )

            if not source:

                self.add_error(
                    "new_product_source",
                    "Please select the product source."
                )

            # =============================================
            # PREVENT DUPLICATE PRODUCTS
            # =============================================

            if product_name and brand:

                specification_value = (
                    specification.strip()
                    if specification
                    else ""
                )

                duplicate = Product.objects.filter(
                    item_name__iexact=product_name.strip(),
                    brand__iexact=brand.strip(),
                    specification__iexact=specification_value,
                ).exists()

                if duplicate:

                    self.add_error(
                        "new_product_name",
                        (
                            "This product, brand and "
                            "specification already exist. "
                            "Please select it from the "
                            "existing product list."
                        )
                    )

        # =================================================
        # PURCHASE VALIDATION
        # =================================================

        quantity = cleaned_data.get(
            "quantity"
        )

        unit_cost = cleaned_data.get(
            "unit_cost"
        )

        if quantity and quantity <= 0:

            self.add_error(
                "quantity",
                "Quantity must be greater than 0."
            )

        if unit_cost and unit_cost <= 0:

            self.add_error(
                "unit_cost",
                "Unit cost must be greater than 0."
            )

        payment_status = cleaned_data.get(
            "payment_status"
        )

        payment_method = cleaned_data.get(
            "payment_method"
        )

        if (
            payment_status == "paid"
            and not payment_method
        ):

            self.add_error(
                "payment_method",
                (
                    "Please select a payment method "
                    "for a paid purchase."
                )
            )

        return cleaned_data
