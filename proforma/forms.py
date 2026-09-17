from django import forms
from django.forms import inlineformset_factory

from .models import Proforma, ProformaItem


class ProformaForm(forms.ModelForm):

    class Meta:
        model = Proforma
        fields = [
            "client_name",
            "client_address",
            "client_phone",
            "client_email",
            "purpose",
            "date",
            "valid_until",
            "tax_rate",
            "other_costs",
            "other_costs_description",
            "status",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "valid_until": forms.DateInput(attrs={"type": "date"}),
        }


class ProformaItemForm(forms.ModelForm):

    class Meta:
        model = ProformaItem
        fields = ["description", "quantity", "rate"]


ProformaItemFormSet = inlineformset_factory(
    Proforma,
    ProformaItem,
    form=ProformaItemForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
