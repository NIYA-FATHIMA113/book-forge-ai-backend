from django.db import transaction

from tenants.models import Tenant
from services.models import Service
from availability.models import BusinessHours


BUSINESS_TYPE_MAPPING = {
    "football turf": "sports_turf",
    "sports turf": "sports_turf",
}


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
    Convert confirmed AI configuration
    into the actual booking-system records.
    """

    # -------------------------
    # 1. Map business type
    # -------------------------

    business_type = BUSINESS_TYPE_MAPPING.get(
        configuration.business_type.lower()
    )

    if not business_type:
        raise ValueError(
            f"Unsupported business type: "
            f"{configuration.business_type}"
        )

    # -------------------------
    # 2. Create Tenant
    # -------------------------

    tenant, created = Tenant.objects.get_or_create(
        owner=owner,
        business_name=configuration.business_name,
        defaults={
            "business_type": business_type,
            "is_active": True,
        },
    )

    # -------------------------
    # 3. Create Services
    # -------------------------

    for service_data in services_data:

        Service.objects.update_or_create(
            tenant=tenant,
            name=service_data.name,
            defaults={
                "duration": service_data.duration_minutes or 60,
                "price": service_data.price or 0,
                "is_active": True,
            },
        )

    # -------------------------
    # 4. Create Business Hours
    # -------------------------

    working_days = configuration.working_days or []

    open_days = set()

    for day_name in working_days:

        day_number = DAY_MAPPING.get(day_name)

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

    # -------------------------
    # 5. Create closed days
    # -------------------------

    all_days = set(DAY_MAPPING.values())

    closed_days = all_days - open_days

    for day_number in closed_days:

        BusinessHours.objects.update_or_create(
            tenant=tenant,
            day_of_week=day_number,
            defaults={
                "opening_time": configuration.opening_time,
                "closing_time": configuration.closing_time,
                "is_closed": True,
            },
        )

    return tenant