from django.contrib import admin

from .models import Receipt, ReceiptPayment, Sale

admin.site.register(Sale)


class ReceiptPaymentInline(admin.TabularInline):
    model = ReceiptPayment
    extra = 0


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ("number", "customer_name", "order_number", "created_at")
    search_fields = ("customer_name", "customer_phone", "order_number")
    inlines = [ReceiptPaymentInline]
