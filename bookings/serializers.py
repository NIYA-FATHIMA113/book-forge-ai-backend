from rest_framework import serializers
from .models import Booking

from .utils import (
    get_business_hours,
    is_within_business_hours,
    has_booking_conflict,
)
class BookingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Booking
        fields = [
            "id",
            "customer_name",
            "customer_phone",
            "booking_date",
            "booking_time",
            "service",
            "status",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate(self, attrs):
        tenant = self.context["tenant"]
        service = attrs["service"]

        business_hours = get_business_hours(
            tenant,
            attrs["booking_date"]
        )

        if business_hours is None:
            raise serializers.ValidationError(
                "Business hours are not configured for this day."
            )

        if business_hours.is_closed:
            raise serializers.ValidationError(
                "Business is closed on this day."
            )

        if not is_within_business_hours(
            business_hours,
            attrs["booking_time"],
            service.duration,
        ):
            raise serializers.ValidationError(
                "Booking is outside business hours."
            )

        # Ensure the selected service belongs to this tenant
        if service.tenant != tenant:
            raise serializers.ValidationError(
                "Invalid service selected."
            )

        # Prevent overlapping bookings
        if has_booking_conflict(
            tenant,
            attrs["booking_date"],
            attrs["booking_time"],
            service.duration,
        ):
            raise serializers.ValidationError(
                "This booking overlaps with an existing booking."
            )

        return attrs