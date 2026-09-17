from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProformaForm, ProformaItemFormSet
from .models import Proforma


def can_manage_proforma(user):
    return (
        user.groups.filter(name="owner").exists()
        or user.groups.filter(name="employee").exists()
    )


# ============================================================
# CREATE PROFORMA
# ============================================================

@login_required
def create_proforma(request):

    if not can_manage_proforma(request.user):
        raise PermissionDenied

    if request.method == "POST":

        form = ProformaForm(request.POST)
        formset = ProformaItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():

            try:
                proforma = form.save(commit=False)
                proforma.created_by = request.user
                proforma.full_clean()
                proforma.save()

                formset.instance = proforma

                items = formset.save(commit=False)

                for item in items:
                    item.full_clean()
                    item.save()

                for obj in formset.deleted_objects:
                    obj.delete()

                messages.success(
                    request,
                    f"Proforma {proforma.proforma_number} created successfully."
                )

                return redirect("proforma_detail", proforma_id=proforma.id)

            except ValidationError as error:

                if hasattr(error, "message_dict"):
                    for field, msgs in error.message_dict.items():
                        for msg in msgs:
                            form.add_error(
                                field if field in form.fields else None,
                                msg
                            )
                else:
                    form.add_error(None, error)

    else:

        form = ProformaForm()
        formset = ProformaItemFormSet()

    return render(
        request,
        "proforma/create_proforma.html",
        {
            "form": form,
            "formset": formset,
        }
    )


# ============================================================
# LIST PROFORMAS
# ============================================================

@login_required
def proforma_list(request):

    if not can_manage_proforma(request.user):
        raise PermissionDenied

    proformas = Proforma.objects.select_related("created_by").prefetch_related("items")

    return render(
        request,
        "proforma/proforma_list.html",
        {
            "proformas": proformas,
        }
    )


# ============================================================
# PROFORMA DETAIL / PRINT VIEW
# ============================================================

@login_required
def proforma_detail(request, proforma_id):

    if not can_manage_proforma(request.user):
        raise PermissionDenied

    proforma = get_object_or_404(
        Proforma.objects.prefetch_related("items"),
        id=proforma_id
    )

    return render(
        request,
        "proforma/proforma_detail.html",
        {
            "proforma": proforma,
        }
    )


# ============================================================
# UPDATE PROFORMA STATUS
# ============================================================

@login_required
def update_proforma_status(request, proforma_id):

    if not request.user.groups.filter(name="owner").exists():
        raise PermissionDenied

    proforma = get_object_or_404(Proforma, id=proforma_id)

    if request.method == "POST":

        new_status = request.POST.get("status")

        if new_status in dict(Proforma.STATUS_CHOICES):
            proforma.status = new_status
            proforma.save(update_fields=["status"])
            messages.success(request, f"Status updated to {proforma.get_status_display()}.")

    return redirect("proforma_detail", proforma_id=proforma.id)
