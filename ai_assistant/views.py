from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services.business_setup import (
    create_business_from_configuration,
)
from .models import (
    AIConversation,
    AIMessage,
)

from .serializers import AIChatSerializer

from .services.gemini import (
    generate_ai_response,
    extract_business_info,
)

from .services.business_config import (
    update_business_configuration,
)


class AIChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = AIChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]
        conversation_id = serializer.validated_data.get(
            "conversation_id"
        )

        # Get existing conversation
        if conversation_id:

            conversation = AIConversation.objects.filter(
                id=conversation_id,
                owner=request.user,
            ).first()

            if not conversation:
                return Response(
                    {
                        "error": "Conversation not found."
                    },
                    status=404,
                )

        # Create new conversation
        else:

            conversation = AIConversation.objects.create(
                owner=request.user,
                title="New Business Setup",
            )

        # Save owner's message
        AIMessage.objects.create(
            conversation=conversation,
            role="user",
            content=message,
        )

        # Get complete conversation history
        messages = conversation.messages.order_by(
            "created_at"
        )

        conversation_history = []

        for msg in messages:

            role = (
                "user"
                if msg.role == "user"
                else "model"
            )

            conversation_history.append({
                "role": role,
                "parts": [
                    {
                        "text": msg.content
                    }
                ],
            })

        # Generate Gemini response
        ai_response = generate_ai_response(
            conversation_history
        )

        # Save Gemini response
        AIMessage.objects.create(
            conversation=conversation,
            role="assistant",
            content=ai_response,
        )

        # Extract structured business information
        business_info = extract_business_info(
            message
        )

        # Update BusinessConfiguration
        configuration = update_business_configuration(
            conversation,
            business_info,
        )

        return Response({
            "conversation_id": conversation.id,

            "message": ai_response,

            "business_configuration": {
                "business_name": (
                    configuration.business_name
                ),

                "business_type": (
                    configuration.business_type
                ),

                "booking_deposit": (
                    configuration.booking_deposit
                ),

                "opening_time": (
                    configuration.opening_time
                ),

                "closing_time": (
                    configuration.closing_time
                ),

                "working_days": (
                    configuration.working_days
                ),

                "location": (
                    configuration.location
                ),

                "contact_phone": (
                    configuration.contact_phone
                ),

                "contact_email": (
                    configuration.contact_email
                ),

                "booking_length_minutes": (
                    configuration.booking_length_minutes
                ),
            },
        })

class AIConfirmSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        conversation_id = request.data.get(
            "conversation_id"
        )

        if not conversation_id:
            return Response(
                {
                    "error": "conversation_id is required."
                },
                status=400,
            )

        # Get the owner's conversation
        conversation = AIConversation.objects.filter(
            id=conversation_id,
            owner=request.user,
        ).first()

        if not conversation:
            return Response(
                {
                    "error": "Conversation not found."
                },
                status=404,
            )

        # Get business configuration
        try:
            configuration = (
                conversation.configuration
            )
        except BusinessConfiguration.DoesNotExist:
            return Response(
                {
                    "error": (
                        "Business configuration "
                        "does not exist."
                    )
                },
                status=400,
            )

        # Make sure required information exists
        if not configuration.business_name:
            return Response(
                {
                    "error": (
                        "Business name is missing."
                    )
                },
                status=400,
            )

        if not configuration.business_type:
            return Response(
                {
                    "error": (
                        "Business type is missing."
                    )
                },
                status=400,
            )

        # Get services from the latest AI message
        messages = conversation.messages.filter(
            role="user"
        ).order_by("-created_at")

        if not messages.exists():
            return Response(
                {
                    "error": (
                        "No business information found."
                    )
                },
                status=400,
            )

        # For now, we'll extract the latest
        # business information again.
        latest_message = messages.first()

        business_info = extract_business_info(
            latest_message.content
        )

        # Create the actual booking platform
        tenant = create_business_from_configuration(
            configuration,
            request.user,
            business_info.services,
        )

        # Mark configuration as complete
        configuration.is_complete = True
        configuration.save(
            update_fields=[
                "is_complete",
                "updated_at",
            ]
        )

        return Response(
            {
                "message": (
                    "Business setup completed successfully."
                ),
                "tenant_id": tenant.id,
                "business_name": tenant.business_name,
                "slug": tenant.slug,
            }
        )