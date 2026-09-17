from django.urls import path

from . import views

urlpatterns = [
    path("add/", views.create_proforma, name="create_proforma"),
    path("", views.proforma_list, name="proforma_list"),
    path("<int:proforma_id>/", views.proforma_detail, name="proforma_detail"),
    path("<int:proforma_id>/status/", views.update_proforma_status, name="update_proforma_status"),
]
