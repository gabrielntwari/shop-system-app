from django import forms
from .models import OwnerWithdrawal

from .models import Expense


class ExpenseForm(forms.ModelForm):

    class Meta:
        model = Expense

        fields = [
            "expense_type",
            "amount",
            "description",
        ]

        widgets = {

            "expense_type": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Transport, Electricity, Repair",
                }
            ),

            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter amount",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter description (optional)",
                    "rows": 4,
                }
            ),
        }

    def clean_expense_type(self):

        expense_type = self.cleaned_data.get(
            "expense_type"
        )

        if not expense_type:
            raise forms.ValidationError(
                "Please enter the expense type."
            )

        return expense_type.strip()

    def clean_amount(self):

        amount = self.cleaned_data.get("amount")

        if amount is not None and amount <= 0:
            raise forms.ValidationError(
                "Expense amount must be greater than 0."
            )

        return amount

class OwnerWithdrawalForm(forms.ModelForm):

    class Meta:
        model = OwnerWithdrawal
        fields = [
            "amount",
            "description",
        ]

        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter withdrawal amount",
                    "min": "0",
                    "step": "0.01",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Reason or description (optional)",
                    "rows": 4,
                }
            ),
        }

    def clean_amount(self):
        amount = self.cleaned_data["amount"]

        if amount <= 0:
            raise forms.ValidationError(
                "Withdrawal amount must be greater than 0."
            )

        return amount
