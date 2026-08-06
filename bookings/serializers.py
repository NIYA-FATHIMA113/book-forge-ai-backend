from rest_framework import serializers
from .models import Booking


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
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate(self, attrs):
        tenant = self.context["tenant"]
        service = attrs["service"]

        # Ensure the selected service belongs to this tenant
        if service.tenant != tenant:
            raise serializers.ValidationError(
                "Invalid service selected."
            )

        # Prevent duplicate bookings
        if Booking.objects.filter(
            tenant=tenant,
            booking_date=attrs["booking_date"],
            booking_time=attrs["booking_time"],
        ).exists():
            raise serializers.ValidationError(
                "This time slot is already booked."
            )

        return attrs