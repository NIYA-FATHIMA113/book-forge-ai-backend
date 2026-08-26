from datetime import datetime

from ai_assistant.models import BusinessConfiguration
from datetime import datetime


def parse_time_value(value):
    if not value:
        return None

    value = str(value).strip()

    formats = [
        "%H:%M",
        "%I:%M %p",
        "%I %p",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue

    return None
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
        configuration.opening_time = parse_time_value(
            business_info.opening_time
        )

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
    if business_info.number_of_resources is not None:
        configuration.number_of_resources = (
            business_info.number_of_resources
        )
    if business_info.services:
        configuration.services = [
            {
                "name": service.name,
                "price": service.price,
                "duration_minutes": service.duration_minutes,
            }
            for service in business_info.services
        ]
    configuration.is_complete = configuration.check_completion()
    configuration.save()

    return configuration