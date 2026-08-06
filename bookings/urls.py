from django.urls import path
from .views import BookingCreateView, BookingListView

urlpatterns = [
    path("book/<slug:slug>/", BookingCreateView.as_view(), name="create-booking"),
    path("bookings/", BookingListView.as_view(), name="booking-list"),
]