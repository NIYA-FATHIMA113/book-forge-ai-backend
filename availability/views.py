from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import BusinessHours
from .serializers import BusinessHoursSerializer


class BusinessHoursListCreateView(generics.ListCreateAPIView):
    serializer_class = BusinessHoursSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BusinessHours.objects.filter(
            tenant__owner=self.request.user
        )