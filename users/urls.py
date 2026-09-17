from django.urls import path
from . import views


urlpatterns = [

    # Authentication
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Main dashboard routing
    path("dashboard/", views.dashboard, name="dashboard"),

    # Owner dashboard
    path("owner/", views.owner_dashboard, name="owner_dashboard"),

    # Employee dashboard
    path("employee/", views.employee_dashboard, name="employee_dashboard"),

    # Employee creation
    path(
        "employees/create/",
        views.create_employee,
        name="create_employee"
    ),

    path(
        "employees/success/",
        views.employee_success,
        name="employee_success"
    ),

    # Owner pages
    path(
        "owner/inventory/",
        views.owner_inventory,
        name="owner_inventory"
    ),

    path(
        "owner/transactions/",
        views.owner_transactions,
        name="owner_transactions"
    ),

    path(
        "owner/employees/",
        views.owner_employees,
        name="owner_employees"
    ),

    # Employee pages
    path(
        "employee/transactions/",
        views.employee_transactions,
        name="employee_transactions"
    ),

    path(
        "employee/profile/",
        views.employee_profile,
        name="employee_profile"
    ),
    path(
    "owner/employees/<int:employee_id>/",
    views.owner_employee_detail,
    name="owner_employee_detail"
    ),
    path(
    "employee/message-owner/",
    views.message_owner,
    name="message_owner"
    ),
    path(
    "owner/messages/",
    views.owner_messages,
    name="owner_messages"
    ),
    path(
    "owner/messages/<int:message_id>/read/",
    views.mark_message_read,
    name="mark_message_read"
   ),
]