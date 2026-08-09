from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from tenants.models import Tenant
from .models import Booking
from .serializers import BookingSerializer
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta

from availability.models import BusinessHours
class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingSerializer

    def get_tenant(self):
        return get_object_or_404(
            Tenant,
            slug=self.kwargs["slug"],
            is_active=True
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["tenant"] = self.get_tenant()
        return context

    def perform_create(self, serializer):
        serializer.save(tenant=self.get_tenant())

class BookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Booking.objects.filter(
            tenant__owner=self.request.user
        )

        booking_date = self.request.query_params.get("date")
        customer = self.request.query_params.get("customer")
        service = self.request.query_params.get("service")
        booking_status = self.request.query_params.get("status")

        if booking_date:
            queryset = queryset.filter(
                booking_date=booking_date
            )

        if customer:
            queryset = queryset.filter(
                customer_name__icontains=customer
            )

        if service:
            queryset = queryset.filter(
                service_id=service
            )

        if booking_status:
            queryset = queryset.filter(
                status=booking_status.upper()
            )

        return queryset

class BookingDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Booking.objects.all()

    def get_queryset(self):
        return Booking.objects.filter(
            tenant__owner=self.request.user
        )


class BookingStatusUpdateView(generics.UpdateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(
            tenant__owner=self.request.user
        )

    def update(self, request, *args, **kwargs):
        booking = self.get_object()

        new_status = request.data.get("status")

        allowed_statuses = [
            "PENDING",
            "CONFIRMED",
            "COMPLETED",
            "CANCELLED",
        ]

        if new_status not in allowed_statuses:
            return Response(
                {
                    "error": "Invalid booking status."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = new_status
        booking.save()

        return Response(
            BookingSerializer(booking).data
        )


class AvailableSlotsView(generics.ListAPIView):
    permission_classes = []

    def get(self, request, slug):
        tenant = get_object_or_404(
            Tenant,
            slug=slug,
            is_active=True
        )

        date_string = request.query_params.get("date")
        service_id = request.query_params.get("service")

        if not date_string:
            return Response(
                {"error": "Please provide a date."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not service_id:
            return Response(
                {"error": "Please provide a service."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert date string to date
        try:
            selected_date = datetime.strptime(
                date_string,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            return Response(
                {
                    "error": "Invalid date format. Use YYYY-MM-DD."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find business hours for this day
        day_of_week = selected_date.weekday()

        business_hours = BusinessHours.objects.filter(
            tenant=tenant,
            day_of_week=day_of_week,
            is_closed=False
        ).first()

        if not business_hours:
            return Response({
                "date": date_string,
                "available_slots": []
            })

        # Get requested service
        service = get_object_or_404(
            tenant.services,
            id=service_id,
            is_active=True
        )

        # Existing non-cancelled bookings
        bookings = Booking.objects.filter(
            tenant=tenant,
            booking_date=selected_date
        ).exclude(
            status="CANCELLED"
        )

        slots = []

        current_time = datetime.combine(
            selected_date,
            business_hours.opening_time
        )

        closing_time = datetime.combine(
            selected_date,
            business_hours.closing_time
        )

        while (
            current_time
            + timedelta(minutes=service.duration)
            <= closing_time
        ):

            new_start = current_time

            new_end = (
                current_time
                + timedelta(minutes=service.duration)
            )

            # Assume slot is available
            is_available = True

            # Check overlap with existing bookings
            for booking in bookings:

                existing_start = datetime.combine(
                    booking.booking_date,
                    booking.booking_time
                )

                existing_end = (
                    existing_start
                    + timedelta(
                        minutes=booking.service.duration
                    )
                )

                # Overlap condition
                if (
                    new_start < existing_end
                    and new_end > existing_start
                ):
                    is_available = False
                    break

            if is_available:
                slots.append(
                    current_time.strftime("%H:%M")
                )

            # Move to next possible slot
            current_time += timedelta(
                minutes=service.duration
            )

        return Response({
            "date": date_string,
            "service": service.name,
            "duration": service.duration,
            "available_slots": slots
        })

class PublicBookingDetailView(generics.RetrieveAPIView):
    permission_classes = []

    def get(self, request, slug, pk):
        tenant = get_object_or_404(
            Tenant,
            slug=slug,
            is_active=True
        )

        phone = request.query_params.get("phone")

        if not phone:
            return Response(
                {
                    "error": "Phone number is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        booking = get_object_or_404(
            Booking,
            id=pk,
            tenant=tenant,
            customer_phone=phone
        )

        return Response({
            "booking_id": booking.id,
            "business": tenant.business_name,
            "customer_name": booking.customer_name,
            "customer_phone": booking.customer_phone,
            "service": booking.service.name,
            "date": booking.booking_date,
            "time": booking.booking_time,
            "status": booking.status,
        })