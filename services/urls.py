from django.urls import path
from .views import (
    ServiceListCreateView,
    ServiceDetailView,
    PublicServiceListView,
)

urlpatterns = [
    path(
        "tenants/<int:tenant_id>/services/",
        ServiceListCreateView.as_view(),
        name="service-list-create",
    ),

    path(
        "services/<int:pk>/",
        ServiceDetailView.as_view(),
        name="service-detail",
    ),

    path(
        "book/<slug:slug>/services/",
        PublicServiceListView.as_view(),
        name="public-service-list",
    ),
]