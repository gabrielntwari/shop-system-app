import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (
    BusinessPaymentInfo,
    Order,
    PaymentProof,
)


# ==========================================================
# RWANDA PHONE VALIDATION
# ==========================================================

def validate_rwanda_phone(value):
    """
    Validates common Rwandan mobile phone formats.

    Accepted examples:

        0781234567
        0791234567
        0721234567
        0731234567

        +250781234567
        +250791234567
        +250721234567
        +250731234567

    This checks the phone number format only.
    It does not verify ownership or send an OTP.
    """

    phone = value.strip()

    # Local Rwanda format: 07XXXXXXXX
    local_pattern = r"^07[2389]\d{7}$"

    # International Rwanda format: +2507XXXXXXXX
    international_pattern = r"^\+2507[2389]\d{7}$"

    if not (
        re.fullmatch(local_pattern, phone)
        or re.fullmatch(international_pattern, phone)
    ):
        raise forms.ValidationError(
            "Enter a valid Rwandan mobile phone number, "
            "for example 0781234567 or +250781234567."
        )

    return phone


# ==========================================================
# CUSTOMER REGISTRATION
# ==========================================================

class CustomerRegistrationForm(UserCreationForm):

    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="First name",
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Last name",
    )

    email = forms.EmailField(
        required=True,
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "yourname@example.com",
            }
        ),
    )

    phone = forms.CharField(
        max_length=30,
        required=True,
        label="Phone number",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "0781234567",
            }
        ),
    )

    class Meta:
        model = User

        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]

    def save(self, commit=True):
        """Create the user and keep the phone number on a profile."""
        user = super().save(commit=commit)

        if commit:
            from .models import CustomerProfile

            CustomerProfile.objects.update_or_create(
                user=user,
                defaults={"phone": self.cleaned_data["phone"]},
            )

        return user

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        return validate_rwanda_phone(phone)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )

        return email


# ==========================================================
# BUSINESS PAYMENT SETTINGS
# ==========================================================

class BusinessPaymentInfoForm(forms.ModelForm):

    class Meta:
        model = BusinessPaymentInfo

        fields = [
            "business_name",

            "mtn_momo_number",
            "mtn_momo_name",

            "airtel_money_number",
            "airtel_money_name",

            "bank_name",
            "bank_account_name",
            "bank_account_number",

            "card_instructions",
            "other_instructions",
        ]

        widgets = {

            "business_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Business name",
                }
            ),

            "mtn_momo_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "MTN MoMo number",
                }
            ),

            "mtn_momo_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "MTN MoMo account name",
                }
            ),

            "airtel_money_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Airtel Money number",
                }
            ),

            "airtel_money_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Airtel Money account name",
                }
            ),

            "bank_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Bank name",
                }
            ),

            "bank_account_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Bank account name",
                }
            ),

            "bank_account_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Bank account number",
                }
            ),

            "card_instructions": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Card payments accepted at the shop",
                }
            ),

            "other_instructions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Any other payment instructions "
                        "customers should know..."
                    ),
                }
            ),
        }


# ==========================================================
# CUSTOMER SIGNUP
# ==========================================================

class CustomerSignUpForm(forms.Form):

    username = forms.CharField(
        max_length=150,
        label="Username",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Choose a username",
            }
        ),
    )

    phone = forms.CharField(
        max_length=30,
        required=True,
        label="Phone number",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "0781234567",
            }
        ),
    )

    email = forms.EmailField(
        required=True,
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "yourname@example.com",
            }
        ),
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Create a password",
            }
        ),
        label="Password",
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm your password",
            }
        ),
        label="Confirm Password",
    )

    def clean_username(self):

        username = self.cleaned_data["username"].strip()

        if User.objects.filter(
            username__iexact=username
        ).exists():

            raise forms.ValidationError(
                "That username is already taken."
            )

        return username

    def clean_phone(self):

        phone = self.cleaned_data["phone"]

        return validate_rwanda_phone(phone)

    def clean_email(self):

        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(
            email__iexact=email
        ).exists():

            raise forms.ValidationError(
                "An account with this email address already exists."
            )

        return email

    def clean(self):

        cleaned_data = super().clean()

        password1 = cleaned_data.get(
            "password1"
        )

        password2 = cleaned_data.get(
            "password2"
        )

        if (
            password1
            and password2
            and password1 != password2
        ):

            raise forms.ValidationError(
                "Passwords do not match."
            )

        return cleaned_data


# ==========================================================
# ORDER / DELIVERY FORM
# ==========================================================

class OrderDeliveryForm(forms.ModelForm):

    customer_name = forms.CharField(
        max_length=150,
        required=True,
        label="Full name",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Name of the person receiving the order",
            }
        ),
    )

    delivery_email = forms.EmailField(
        required=True,
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "yourname@example.com",
            }
        ),
    )

    delivery_phone = forms.CharField(
        max_length=30,
        required=True,
        label="Phone number",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "0781234567",
            }
        ),
    )

    district = forms.CharField(
        max_length=100,
        required=True,
        label="District",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Gasabo",
            }
        ),
    )

    sector = forms.CharField(
        max_length=100,
        required=True,
        label="Sector",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Remera",
            }
        ),
    )

    cell_village = forms.CharField(
        max_length=100,
        required=True,
        label="Cell / Village",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Rukiri",
            }
        ),
    )

    detailed_address = forms.CharField(
        max_length=255,
        required=True,
        label="Detailed address",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Street, building, landmark, etc.",
            }
        ),
    )

    class Meta:
        model = Order

        fields = [
            "customer_name",
            "delivery_email",
            "delivery_phone",
            "district",
            "sector",
            "cell_village",
            "detailed_address",
            "notes",
        ]

        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Additional delivery instructions "
                        "(optional)"
                    ),
                }
            ),
        }

    def clean_customer_name(self):

        name = " ".join(self.cleaned_data["customer_name"].split())

        if len(name) < 3:
            raise forms.ValidationError(
                "Please enter your full name."
            )

        return name

    def clean_delivery_email(self):

        email = self.cleaned_data["delivery_email"]

        return email.strip().lower()

    def clean_delivery_phone(self):

        phone = self.cleaned_data["delivery_phone"]

        return validate_rwanda_phone(phone)

    def clean_district(self):

        district = self.cleaned_data["district"].strip()

        if len(district) < 2:
            raise forms.ValidationError(
                "Please enter a valid district."
            )

        return district

    def clean_sector(self):

        sector = self.cleaned_data["sector"].strip()

        if len(sector) < 2:
            raise forms.ValidationError(
                "Please enter a valid sector."
            )

        return sector

    def clean_cell_village(self):

        cell_village = self.cleaned_data["cell_village"].strip()

        if len(cell_village) < 2:
            raise forms.ValidationError(
                "Please enter a valid cell or village."
            )

        return cell_village

    def clean_detailed_address(self):

        address = self.cleaned_data["detailed_address"].strip()

        if len(address) < 3:
            raise forms.ValidationError(
                "Please provide a more complete delivery address."
            )

        return address
#=======================================================
# PAYMENT PROOF
# ==========================================================

PROOF_MAX_BYTES = 5 * 1024 * 1024  # 5 MB

# extension -> allowed leading bytes of a genuine file of that type
PROOF_SIGNATURES = {
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".pdf": (b"%PDF-",),
    ".webp": (b"RIFF",),
}


class PaymentProofForm(forms.ModelForm):

    def clean_proof_file(self):
        upload = self.cleaned_data.get("proof_file")

        if not upload:
            return upload

        name = upload.name.lower()
        extension = name[name.rfind("."):] if "." in name else ""

        if extension not in PROOF_SIGNATURES:
            raise forms.ValidationError(
                "Please upload a photo (JPG, PNG, WEBP) or a PDF."
            )

        if upload.size > PROOF_MAX_BYTES:
            raise forms.ValidationError(
                "The file is too large. Maximum size is 5 MB."
            )

        header = upload.read(16)
        upload.seek(0)

        if not header.startswith(PROOF_SIGNATURES[extension]):
            raise forms.ValidationError(
                "This file does not look like a valid "
                f"{extension.lstrip('.').upper()} file."
            )

        return upload

    class Meta:
        model = PaymentProof

        fields = [
            "proof_file",
            "payment_method",
            "reference_note",
        ]

        widgets = {

            "proof_file": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*,.pdf",
                }
            ),

            "payment_method": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "reference_note": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Transaction ID / payment reference "
                        "(optional)"
                    ),
                }
            ),
        }
