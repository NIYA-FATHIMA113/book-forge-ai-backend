from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "tenant",
        "booking_date",
        "booking_time",
        "service",
    )

    search_fields = (
        "customer_name",
        "customer_phone",
    )

    list_filter = (
        "booking_date",
        "tenant",
    )