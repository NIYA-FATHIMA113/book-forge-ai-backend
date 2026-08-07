from rest_framework import serializers
from .models import BusinessHours


class BusinessHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessHours
        fields = "__all__"