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

        booking_exists = Booking.objects.filter(
            tenant=tenant,
            booking_date=attrs["booking_date"],
            booking_time=attrs["booking_time"],
        ).exists()

        if booking_exists:
            raise serializers.ValidationError(
                "This time slot is already booked."
            )

        return attrs