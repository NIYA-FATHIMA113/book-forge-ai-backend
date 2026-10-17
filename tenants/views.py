

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Tenant
from .serializers import TenantSerializer


class PublicTenantDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        tenant = get_object_or_404(Tenant, slug=slug, is_active=True)
        return Response({
            "id": tenant.id,
            "business_name": tenant.business_name,
            "business_type": tenant.business_type,
            "website_style": tenant.website_style,
            "location": tenant.location,
            "contact_phone": tenant.contact_phone,
            "contact_email": tenant.contact_email,
        })


class TenantListCreateView(generics.ListCreateAPIView):

    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Tenant.objects.filter(
            owner=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(
            owner=self.request.user
        )


class TenantDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Tenant.objects.filter(
            owner=self.request.user
        )
