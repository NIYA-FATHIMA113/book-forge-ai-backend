from rest_framework import serializers

from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tenant

        fields = [
            "id",
            "business_name",
            "slug",
            "business_type",
            "location",
            "contact_phone",
            "contact_email",
            "booking_length_minutes",
            "booking_deposit",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "slug",
            "created_at",
            "updated_at",
        ]