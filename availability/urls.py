from django.urls import path
from .views import BusinessHoursListCreateView

urlpatterns = [
    path(
        "",
        BusinessHoursListCreateView.as_view(),
        name="business-hours"
    ),
]