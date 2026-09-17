from django.contrib import admin

from .models import Proforma, ProformaItem


class ProformaItemInline(admin.TabularInline):
    model = ProformaItem
    extra = 1


@admin.register(Proforma)
class ProformaAdmin(admin.ModelAdmin):
    list_display = ("proforma_number", "client_name", "date", "valid_until", "status", "created_by")
    list_filter = ("status",)
    search_fields = ("proforma_number", "client_name")
    inlines = [ProformaItemInline]
