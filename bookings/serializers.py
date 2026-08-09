

from rest_framework import serializers

from .models import Booking
from .utils import (
    get_business_hours,
    is_within_business_hours,
    has_booking_conflict,
)

from services.models import Resource


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
            "resource",
            "status",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "resource",
            "status",
            "created_at",
        ]

    def validate(self, attrs):

        tenant = self.context["tenant"]

        service = attrs["service"]

        booking_date = attrs["booking_date"]

        booking_time = attrs["booking_time"]

        # --------------------------------
        # 1. Check service belongs to tenant
        # --------------------------------

        if service.tenant != tenant:

            raise serializers.ValidationError(
                "Invalid service selected."
            )

        # --------------------------------
        # 2. Get business hours
        # --------------------------------

        business_hours = get_business_hours(
            tenant,
            booking_date
        )

        if business_hours is None:

            raise serializers.ValidationError(
                "Business hours are not configured for this day."
            )

        if business_hours.is_closed:

            raise serializers.ValidationError(
                "Business is closed on this day."
            )

        # --------------------------------
        # 3. Check booking is within hours
        # --------------------------------

        if not is_within_business_hours(
            business_hours,
            booking_time,
            service.duration
        ):

            raise serializers.ValidationError(
                "Booking is outside business hours."
            )

        # --------------------------------
        # 4. Get active resources
        # --------------------------------

        resources = Resource.objects.filter(
            service=service,
            is_active=True
        )

        if not resources.exists():

            raise serializers.ValidationError(
                "No resources are available for this service."
            )

        # --------------------------------
        # 5. Find an available resource
        # --------------------------------

        available_resource = None

        for resource in resources:

            if not has_booking_conflict(
                resource,
                booking_date,
                booking_time,
                service.duration
            ):

                available_resource = resource
                break

        # --------------------------------
        # 6. All resources are occupied
        # --------------------------------

        if available_resource is None:

            raise serializers.ValidationError(
                "All resources are booked for this time slot."
            )

        # --------------------------------
        # 7. Assign resource
        # --------------------------------

        attrs["resource"] = available_resource

        return attrs