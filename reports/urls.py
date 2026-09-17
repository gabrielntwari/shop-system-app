from django.urls import path
from . import views


urlpatterns = [

    path(
        "",
        views.owner_reports,
        name="owner_reports"
    ),

]
