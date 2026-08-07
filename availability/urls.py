from django.urls import path
from .views import AvailableSlotsView

urlpatterns = [
    path(
        "book/<slug:slug>/available-slots/",
        AvailableSlotsView.as_view(),
        name="available-slots",
    ),
]