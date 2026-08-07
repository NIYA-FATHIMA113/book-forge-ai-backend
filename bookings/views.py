from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from tenants.models import Tenant
from .models import Booking
from .serializers import BookingSerializer


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

        return queryset

class BookingDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Booking.objects.all()

    def get_queryset(self):
        return Booking.objects.filter(
            tenant__owner=self.request.user
        )