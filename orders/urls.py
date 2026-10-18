from django.urls import path

from . import views

urlpatterns = [
    path("catalog/", views.product_catalog, name="product_catalog"),
    path("product/<int:product_id>/", views.product_detail, name="product_detail"),
    path("signup/", views.customer_signup, name="customer_signup"),

    path("cart/", views.view_cart, name="view_cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),

    path("checkout/", views.checkout, name="checkout"),
    path("<int:order_id>/pay/", views.order_payment, name="order_payment"),
    path("proof/<int:proof_id>/", views.payment_proof_file, name="payment_proof_file"),

    path("my/", views.my_orders, name="my_orders"),
    path("<int:order_id>/", views.order_detail, name="order_detail"),
    path("<int:order_id>/receipt/", views.order_receipt, name="order_receipt"),
    path("<int:order_id>/cancel/", views.cancel_order, name="cancel_order"),

    path("manage/", views.manage_orders, name="manage_orders"),
    path("<int:order_id>/mark-paid/", views.mark_order_paid, name="mark_order_paid"),
    path("<int:order_id>/mark-delivered/", views.mark_order_delivered, name="mark_order_delivered"),
    path("payment-settings/", views.payment_settings, name="payment_settings"),
]
