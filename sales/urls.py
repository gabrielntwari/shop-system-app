from django.urls import path
from . import views


urlpatterns = [
    path("add/", views.add_sale, name="add_sale"),
    path("receipts/", views.receipt_list, name="receipt_list"),
    path("receipts/<int:pk>/", views.receipt_detail, name="receipt_detail"),
    path("receipts/<int:pk>/print/", views.receipt_print, name="receipt_print"),
]
