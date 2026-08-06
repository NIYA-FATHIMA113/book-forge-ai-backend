from django.urls import path
from .views import ServiceListCreateView

urlpatterns = [
    path(
        "tenants/<int:tenant_id>/services/",
        ServiceListCreateView.as_view(),
        name="service-list-create",
    ),
]