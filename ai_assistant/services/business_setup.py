
from django.db import transaction

from tenants.models import Tenant
from services.models import Service, Resource
from availability.models import BusinessHours


# --------------------------------
# Business type mapping
# --------------------------------

BUSINESS_TYPE_MAPPING = {
    "football turf": "sports_turf",
    "sports turf": "sports_turf",
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

    Creates:

        Tenant
        Services
        Resources
        Business Hours
    """

    # --------------------------------
    # 1. Validate business type
    # --------------------------------

    business_type = BUSINESS_TYPE_MAPPING.get(
        configuration.business_type.lower()
    )

    if not business_type:
        raise ValueError(
            f"Unsupported business type: "
            f"{configuration.business_type}"
        )

    # --------------------------------
    # 2. Create Tenant
    # --------------------------------

    tenant, created = Tenant.objects.get_or_create(
        owner=owner,
        business_name=configuration.business_name,
        defaults={
            "business_type": business_type,
            "is_active": True,
        },
    )

    # --------------------------------
    # 3. Create Services
    # --------------------------------

    for service_data in services_data:

        service, _ = Service.objects.update_or_create(
            tenant=tenant,
            name=service_data.name,
            defaults={
                "duration": (
                    service_data.duration_minutes
                    or configuration.booking_length_minutes
                    or 60
                ),
                "price": service_data.price or 0,
                "is_active": True,
            },
        )

        # --------------------------------
        # 4. Create Resources
        # --------------------------------

        number_of_resources = (
            configuration.number_of_resources
            or 1
        )

        for resource_number in range(
            1,
            number_of_resources + 1,
        ):

            Resource.objects.get_or_create(
                service=service,
                name=f"Resource {resource_number}",
                defaults={
                    "is_active": True,
                },
            )

    # --------------------------------
    # 5. Create Business Hours
    # --------------------------------

    working_days = (
        configuration.working_days
        or []
    )

    open_days = set()

    for day_name in working_days:

        day_number = DAY_MAPPING.get(
            day_name
        )

        if day_number is None:
            continue

        open_days.add(day_number)

        BusinessHours.objects.update_or_create(
            tenant=tenant,
            day_of_week=day_number,
            defaults={
                "opening_time": (
                    configuration.opening_time
                ),
                "closing_time": (
                    configuration.closing_time
                ),
                "is_closed": False,
            },
        )

    # --------------------------------
    # 6. Create Closed Days
    # --------------------------------

    all_days = set(
        DAY_MAPPING.values()
    )

    closed_days = all_days - open_days

    for day_number in closed_days:

        BusinessHours.objects.update_or_create(
            tenant=tenant,
            day_of_week=day_number,
            defaults={
                "opening_time": (
                    configuration.opening_time
                ),
                "closing_time": (
                    configuration.closing_time
                ),
                "is_closed": True,
            },
        )

    # --------------------------------
    # 7. Return Tenant
    # --------------------------------

    return tenant

