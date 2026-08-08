from rest_framework import serializers


class AIChatSerializer(serializers.Serializer):
    message = serializers.CharField()
    conversation_id = serializers.IntegerField(
        required=False,
        allow_null=True
    )