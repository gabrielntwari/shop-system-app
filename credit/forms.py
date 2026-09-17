from django import forms

from .models import (
    SaleCreditPayment,
    PurchaseCreditPayment,
)


class SaleCreditPaymentForm(forms.ModelForm):

    class Meta:
        model = SaleCreditPayment

        fields = [
            "amount",
            "payment_method",
        ]

        widgets = {

            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter amount paid",
                "step": "0.01",
                "min": "0.01",
            }),

            "payment_method": forms.Select(attrs={
                "class": "form-control",
            }),
        }


class PurchaseCreditPaymentForm(forms.ModelForm):

    class Meta:
        model = PurchaseCreditPayment

        fields = [
            "amount",
            "payment_method",
        ]

        widgets = {

            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter amount paid",
                "step": "0.01",
                "min": "0.01",
            }),

            "payment_method": forms.Select(attrs={
                "class": "form-control",
            }),
        }