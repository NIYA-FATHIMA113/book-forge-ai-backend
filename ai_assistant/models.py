from django.conf import settings
from django.db import models


class AIConversation(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_conversations",
    )

    title = models.CharField(
        max_length=200,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.owner.username} - {self.title or 'AI Conversation'}"

class AIMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
    )

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.role} - {self.conversation.id}"

class BusinessConfiguration(models.Model):
    conversation = models.OneToOneField(
        AIConversation,
        on_delete=models.CASCADE,
        related_name="configuration",
    )

    business_name = models.CharField(
        max_length=200,
        blank=True,
    )

    business_type = models.CharField(
        max_length=100,
        blank=True,
    )

    services = models.JSONField(
        default=list,
        blank=True,
    )

    booking_deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    opening_time = models.TimeField(
        null=True,
        blank=True,
    )

    closing_time = models.TimeField(
        null=True,
        blank=True,
    )

    working_days = models.JSONField(
        default=list,
        blank=True,
    )

    location = models.CharField(
        max_length=300,
        blank=True,
    )

    contact_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    contact_email = models.EmailField(
        blank=True,
    )

    booking_length_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    number_of_resources = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    is_complete = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.business_name or "Business Configuration"