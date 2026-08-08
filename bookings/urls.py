from django.urls import path
from .views import BookingCreateView, BookingListView,BookingDeleteView,BookingStatusUpdateView

urlpatterns = [
    path(
        "book/<slug:slug>/",
        BookingCreateView.as_view(),
        name="create-booking",
    ),

    path(
        "bookings/",
        BookingListView.as_view(),
        name="booking-list",
    ),

    path(
        "bookings/<int:pk>/",
        BookingDeleteView.as_view(),
        name="booking-delete",
    ),
    path(
        "bookings/<int:pk>/status/",
        BookingStatusUpdateView.as_view(),
        name="booking-status-update",
    ),
]