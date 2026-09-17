from django.urls import path
from . import views


urlpatterns = [

    # Sale credit payment
    path(
        "sale/<int:sale_id>/pay/",
        views.pay_sale_credit,
        name="pay_sale_credit"
    ),

    # Purchase credit payment
    path(
        "purchase/<int:purchase_id>/pay/",
        views.pay_purchase_credit,
        name="pay_purchase_credit"
    ),

    # Owner credit pages
    path(
        "owner/sales/",
        views.owner_sale_credits,
        name="owner_sale_credits"
    ),

    path(
        "owner/purchases/",
        views.owner_purchase_credits,
        name="owner_purchase_credits"
    ),

    # Employee credit pages
    path(
        "employee/sales/",
        views.employee_sale_credits,
        name="employee_sale_credits"
    ),

    path(
        "employee/purchases/",
        views.employee_purchase_credits,
        name="employee_purchase_credits"
    ),
]
