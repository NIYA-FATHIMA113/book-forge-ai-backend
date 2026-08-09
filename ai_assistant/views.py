from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import (
    AIConversation,
    AIMessage,
    BusinessConfiguration,
)

from .serializers import AIChatSerializer

from .services.gemini import (
    generate_ai_response,
    extract_business_info,
)

from .services.business_config import (
    update_business_configuration,
)

from .services.business_setup import (
    create_business_from_configuration,
)

# Keep this for now only if you still want the
# customer-facing AI booking endpoint as a future feature.
from .services.booking_ai import process_booking_request


class AIChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # -----------------------------
        # 1. Validate request
        # -----------------------------

        serializer = AIChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]

        conversation_id = serializer.validated_data.get(
            "conversation_id"
        )

        # -----------------------------
        # 2. Get or create conversation
        # -----------------------------

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
                    status=status.HTTP_404_NOT_FOUND,
                )

        else:

            conversation = AIConversation.objects.create(
                owner=request.user,
                title="New Business Setup",
            )

        # -----------------------------
        # 3. Save owner's message
        # -----------------------------

        AIMessage.objects.create(
            conversation=conversation,
            role="user",
            content=message,
        )

        # -----------------------------
        # 4. Build conversation history
        # -----------------------------

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

            conversation_history.append(
                {
                    "role": role,
                    "parts": [
                        {
                            "text": msg.content
                        }
                    ],
                }
            )

        # -----------------------------
        # 5. Generate AI response
        # -----------------------------

        ai_response = generate_ai_response(
            conversation_history
        )

        # -----------------------------
        # 6. Save AI response
        # -----------------------------

        AIMessage.objects.create(
            conversation=conversation,
            role="assistant",
            content=ai_response,
        )

        # -----------------------------
        # 7. Extract business information
        # -----------------------------

        business_info = extract_business_info(
            message
        )

        # -----------------------------
        # 8. Update configuration
        # -----------------------------

        configuration = update_business_configuration(
            conversation,
            business_info,
        )

        # -----------------------------
        # 9. Return response
        # -----------------------------

        return Response(
            {
                "conversation_id": conversation.id,

                "message": ai_response,

                "business_configuration": {
                    "business_name": (
                        configuration.business_name
                    ),

                    "business_type": (
                        configuration.business_type
                    ),

                    "services": (
                        configuration.services
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

                    "is_complete": (
                        configuration.is_complete
                    ),
                    "number_of_resources": (
                        configuration.number_of_resources
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )


class AIConfirmSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # -----------------------------
        # 1. Get conversation ID
        # -----------------------------

        conversation_id = request.data.get(
            "conversation_id"
        )

        if not conversation_id:

            return Response(
                {
                    "error": (
                        "conversation_id is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------
        # 2. Get owner's conversation
        # -----------------------------

        conversation = AIConversation.objects.filter(
            id=conversation_id,
            owner=request.user,
        ).first()

        if not conversation:

            return Response(
                {
                    "error": "Conversation not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -----------------------------
        # 3. Get configuration
        # -----------------------------

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
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------
        # 4. Validate required information
        # -----------------------------

        if not configuration.business_name:

            return Response(
                {
                    "error": (
                        "Business name is missing."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not configuration.business_type:

            return Response(
                {
                    "error": (
                        "Business type is missing."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not configuration.services:

            return Response(
                {
                    "error": (
                        "At least one service "
                        "is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------
        # 5. Create actual platform
        # -----------------------------

        try:

            tenant = create_business_from_configuration(
                configuration,
                request.user,
                configuration.services,
            )

        except ValueError as e:

            return Response(
                {
                    "error": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------
        # 6. Mark configuration complete
        # -----------------------------

        configuration.is_complete = True

        configuration.save(
            update_fields=[
                "is_complete",
                "updated_at",
            ]
        )

        # -----------------------------
        # 7. Return result
        # -----------------------------

        return Response(
            {
                "message": (
                    "Business setup completed "
                    "successfully."
                ),

                "tenant_id": tenant.id,

                "business_name": (
                    tenant.business_name
                ),

                "slug": tenant.slug,
            },
            status=status.HTTP_201_CREATED,
        )


# --------------------------------------------------
# FUTURE CUSTOMER AI BOOKING ENDPOINT
# --------------------------------------------------

class AIBookingView(APIView):

    def post(self, request):

        message = request.data.get("message")

        if not message:

            return Response(
                {
                    "error": "Message is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            result = process_booking_request(
                message
            )

            if not result["success"]:

                return Response(
                    result,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                result,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:

            return Response(
                {
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )