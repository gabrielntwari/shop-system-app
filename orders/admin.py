
from django.contrib import admin

from .models import (
    BusinessPaymentInfo,
    CustomerProfile,
    Order,
    OrderItem,
    PaymentProof,
)


@admin.register(BusinessPaymentInfo)
class BusinessPaymentInfoAdmin(admin.ModelAdmin):

    list_display = (
        "business_name",
        "mtn_momo_number",
        "airtel_money_number",
        "bank_name",
        "updated_at",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "order_number",
        "customer",
        "status",
        "total",
        "processed_by",
        "created_at",
        "paid_at",
        "delivered_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "order_number",
        "customer_name",
        "delivery_phone",
        "delivery_email",
        "customer__username",
        "customer__first_name",
        "customer__last_name",
    )

    readonly_fields = (
        "order_number",
        "created_at",
        "paid_at",
        "delivered_at",
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "product",
        "quantity",
        "price",
        "amount",
    )

    search_fields = (
        "order__order_number",
        "product__item_name",
    )


@admin.register(PaymentProof)
class PaymentProofAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "payment_method",
        "reference_note",
        "uploaded_at",
    )

    list_filter = (
        "payment_method",
        "uploaded_at",
    )

    search_fields = (
        "order__order_number",
        "reference_note",
    )


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "phone",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone",
    )
