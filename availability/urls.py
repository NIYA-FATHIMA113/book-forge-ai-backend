from django.urls import path

from .views import (
    BusinessHoursListCreateView,
    BusinessHoursDetailView,
)


urlpatterns = [

    path(
        "tenants/<int:tenant_id>/business-hours/",
        BusinessHoursListCreateView.as_view(),
        name="business-hours-list-create",
    ),

    path(
        "business-hours/<int:pk>/",
        BusinessHoursDetailView.as_view(),
        name="business-hours-detail",
    ),

]