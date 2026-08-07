from datetime import datetime

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response

from tenants.models import Tenant
from services.models import Service

from bookings.utils import get_business_hours, has_booking_conflict
from .utils import generate_time_slots


class AvailableSlotsView(APIView):

    def get(self, request, slug):

        tenant = get_object_or_404(
            Tenant,
            slug=slug,
            is_active=True
        )

        date_string = request.query_params.get("date")
        service_id = request.query_params.get("service")

        if not date_string or not service_id:
            return Response(
                {
                    "error": "date and service are required."
                },
                status=400
            )

        booking_date = datetime.strptime(
            date_string,
            "%Y-%m-%d"
        ).date()

        service = get_object_or_404(
            Service,
            id=service_id,
            tenant=tenant,
            is_active=True
        )

        business_hours = get_business_hours(
            tenant,
            booking_date
        )

        if business_hours is None:
            return Response(
                {
                    "error": "Business hours are not configured."
                },
                status=400
            )

        if business_hours.is_closed:
            return Response(
                {
                    "error": "Business is closed."
                },
                status=400
            )

        slots = generate_time_slots(
            business_hours.opening_time,
            business_hours.closing_time,
            service.duration
        )
        available_slots = []

        for slot in slots:
            if not has_booking_conflict(
                tenant,
                booking_date,
                slot,
                service.duration,
            ):
                available_slots.append(slot)

        return Response({
            "date": booking_date,
            "available_slots": [
                slot.strftime("%H:%M")
                for slot in available_slots
            ]
        })