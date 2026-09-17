from django.urls import path
from . import views


urlpatterns = [

    # Owner inventory
    path(
        "",
        views.owner_inventory,
        name="owner_inventory"
    ),

    # Add product
    path(
        "add/",
        views.add_product,
        name="add_product"
    ),

    # Update product
    path(
        "update/<int:product_id>/",
        views.update_product,
        name="update_product"
    ),

]
