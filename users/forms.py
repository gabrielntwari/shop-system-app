from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import EmployeeMessage


class EmployeeCreationForm(UserCreationForm):

    first_name = forms.CharField(
        max_length=150,
        required=True
    )

    last_name = forms.CharField(
        max_length=150,
        required=True
    )

    email = forms.EmailField(
        required=False
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


class EmployeeMessageForm(forms.ModelForm):

    class Meta:
        model = EmployeeMessage

        fields = [
            "message",
        ]

        widgets = {
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Write your message to the owner...",
                "rows": 6,
            }),
        }

    def clean_message(self):

        message = self.cleaned_data.get("message")

        if not message or not message.strip():
            raise forms.ValidationError(
                "Please enter a message."
            )

        return message.strip()