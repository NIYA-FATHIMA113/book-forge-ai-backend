from datetime import date

from django.db.models import Count, Sum, F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from bookings.models import Booking
from services.models import Service


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        today = date.today()

        bookings = Booking.objects.filter(
            tenant__owner=request.user
        )

        today_bookings = bookings.filter(
            booking_date=today
        ).count()

        total_bookings = bookings.count()

        total_services = Service.objects.filter(
            tenant__owner=request.user
        ).count()

        today_revenue = (
            bookings.filter(
                booking_date=today
            ).aggregate(
                total=Sum("service__price")
            )["total"] or 0
        )

        return Response({
            "today_bookings": today_bookings,
            "today_revenue": today_revenue,
            "total_bookings": total_bookings,
            "total_services": total_services,
        })