from django.db import transaction

from tenants.models import Tenant
from services.models import Service, Resource
from availability.models import BusinessHours


# --------------------------------
# Business type mapping
# --------------------------------

BUSINESS_TYPE_MAPPING = {
    # Turf aliases and the canonical normalized token.
    "football turf": "sports_turf",
    "football_turf": "sports_turf",
    "sports turf": "sports_turf",
    "sports_turf": "sports_turf",
    "turf": "sports_turf",
    "football ground": "sports_turf",
    "football pitch": "sports_turf",
    "sports facility": "sports_turf",

    # Salon
    "salon": "salon",
    "beauty salon": "salon",
    "hair salon": "salon",

    # Dental clinic
    "dental clinic": "clinic",
    "dentist": "clinic",
    "dental": "clinic",

    # Restaurant
    "restaurant": "restaurant",
    "cafe": "restaurant",
    "coffee shop": "restaurant",
}
# --------------------------------
# Day mapping
# --------------------------------

DAY_MAPPING = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


@transaction.atomic
def create_business_from_configuration(
    configuration,
    owner,
    services_data,
):
    """
    Convert confirmed AI business configuration
    into actual booking-system records.

    Creates/updates:

        Tenant
        Services
        Resources
        Business Hours
    """

    # --------------------------------
    # 1. Validate business information
    # --------------------------------

    if not configuration.business_name:
        raise ValueError("Business name is required.")

    if not configuration.business_type:
        raise ValueError("Business type is required.")

    business_type = BUSINESS_TYPE_MAPPING.get(
        configuration.business_type.lower()
    )

    if not business_type:
        raise ValueError(
            f"Unsupported business type: "
            f"{configuration.business_type}"
        )

    # --------------------------------
    # 2. Create / update Tenant
    # --------------------------------

    tenant, created = Tenant.objects.update_or_create(
        owner=owner,
        business_name=configuration.business_name,
        defaults={
            "business_type": business_type,
            "location": configuration.location or "",
            "contact_phone": configuration.contact_phone or "",
            "contact_email": configuration.contact_email or "",
            "booking_length_minutes": (
                configuration.booking_length_minutes
            ),
            "booking_deposit": (
                configuration.booking_deposit
            ),
            "is_active": True,
        },
    )

    # --------------------------------
    # 3. Create / update Services
    # --------------------------------

    for service_data in services_data:

        # BusinessConfiguration stores services
        # as dictionaries.

        service_name = service_data.get("name")

        if not service_name:
            continue

        duration = (
            service_data.get("duration_minutes")
            or configuration.booking_length_minutes
            or 60
        )

        price = service_data.get("price")

        if price is None:
            price = 0

        Service.objects.update_or_create(
            tenant=tenant,
            name=service_name,
            defaults={
                "duration": duration,
                "price": price,
                "is_active": True,
            },
        )

    # --------------------------------
    # 4. Create tenant-level Resources
    # --------------------------------

    number_of_resources = configuration.number_of_resources or 1

    for resource_number in range(1, number_of_resources + 1):
        Resource.objects.get_or_create(
            tenant=tenant,
            name=f"Resource {resource_number}",
            defaults={"is_active": True},
        )

    # --------------------------------
    # 5. Create Business Hours
    # --------------------------------
    print("AI WORKING DAYS:", configuration.working_days)
    print("AI OPENING TIME:", configuration.opening_time)
    print("AI CLOSING TIME:", configuration.closing_time)
    
    working_days = (
        configuration.working_days
        or []
    )

    open_days = set()

    for day_name in working_days:

        day_name = str(day_name).strip().lower()

        day_number = None

        for mapped_day, number in DAY_MAPPING.items():

            if str(mapped_day).strip().lower() == day_name:
                day_number = number
                break

        if day_number is None:
            continue

        open_days.add(day_number)

        BusinessHours.objects.update_or_create(
            tenant=tenant,
            day_of_week=day_number,
            defaults={
                "opening_time": configuration.opening_time,
                "closing_time": configuration.closing_time,
                "is_closed": False,
            },
        )

    # --------------------------------
    # 7. Return Tenant
    # --------------------------------

    return tenant
