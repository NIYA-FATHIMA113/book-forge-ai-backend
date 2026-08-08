from datetime import datetime

from ai_assistant.models import BusinessConfiguration


def update_business_configuration(
    conversation,
    business_info,
):
    configuration, created = (
        BusinessConfiguration.objects.get_or_create(
            conversation=conversation
        )
    )

    if business_info.business_name:
        configuration.business_name = (
            business_info.business_name
        )

    if business_info.business_type:
        configuration.business_type = (
            business_info.business_type
        )

    if business_info.booking_deposit is not None:
        configuration.booking_deposit = (
            business_info.booking_deposit
        )

    if business_info.opening_time:
        configuration.opening_time = datetime.strptime(
            business_info.opening_time,
            "%H:%M"
        ).time()

    if business_info.closing_time:
        configuration.closing_time = datetime.strptime(
            business_info.closing_time,
            "%H:%M"
        ).time()

    if business_info.working_days:
        configuration.working_days = (
            business_info.working_days
        )

    if business_info.location:
        configuration.location = (
            business_info.location
        )

    if business_info.contact_phone:
        configuration.contact_phone = (
            business_info.contact_phone
        )

    if business_info.contact_email:
        configuration.contact_email = (
            business_info.contact_email
        )

    if business_info.booking_length_minutes:
        configuration.booking_length_minutes = (
            business_info.booking_length_minutes
        )

    configuration.save()

    return configuration