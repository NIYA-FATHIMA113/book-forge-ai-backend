from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny

from tenants.models import Tenant
from .models import Service, Resource
from .serializers import ServiceSerializer, ResourceSerializer

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
class ResourceListCreateView(generics.ListCreateAPIView):
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated]

    def get_service(self):
        return get_object_or_404(
            Service,
            id=self.kwargs["service_id"],
            tenant__owner=self.request.user,
        )

    def get_queryset(self):
        return Resource.objects.filter(
            service=self.get_service()
        )

    def perform_create(self, serializer):
        serializer.save(
            service=self.get_service()
        )


class ResourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Resource.objects.filter(
            service__tenant__owner=self.request.user
        )