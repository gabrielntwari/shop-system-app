from django.urls import path
from . import views


urlpatterns = [

    path(
        "add/",
        views.add_expense,
        name="add_expense"
    ),

    path(
        "employee/",
        views.employee_expenses,
        name="employee_expenses"
    ),

    path(
        "owner/",
        views.owner_expenses,
        name="owner_expenses"
    ),
       path(
        "withdrawal/add/",
        views.add_withdrawal,
        name="add_withdrawal" )

]
