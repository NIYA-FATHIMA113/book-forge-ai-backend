from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from tenants.models import Tenant
from .models import Service
from .serializers import ServiceSerializer
from rest_framework.permissions import AllowAny

class ServiceListCreateView(generics.ListCreateAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def get_tenant(self):
        return get_object_or_404(
            Tenant,
            id=self.kwargs["tenant_id"],
            owner=self.request.user,
        )

    def get_queryset(self):
        return Service.objects.filter(
            tenant=self.get_tenant()
        )

    def perform_create(self, serializer):
        serializer.save(
            tenant=self.get_tenant()
        )

class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Service.objects.filter(
            tenant__owner=self.request.user
        )

class PublicServiceListView(generics.ListAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Service.objects.filter(
            tenant__slug=self.kwargs["slug"],
            tenant__is_active=True,
            is_active=True,
        )