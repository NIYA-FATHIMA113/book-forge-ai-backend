from datetime import datetime, timedelta
from availability.models import BusinessHours


def get_business_hours(tenant, booking_date):
    """
    Returns the BusinessHours object for the booking date.
    Returns None if no schedule exists.
    """

    # Monday = 0, Tuesday = 1, ..., Sunday = 6
    day = booking_date.weekday()

    try:
        return BusinessHours.objects.get(
            tenant=tenant,
            day_of_week=day
        )
    except BusinessHours.DoesNotExist:
        return None

def is_within_business_hours(business_hours, booking_time, duration):
    """
    Returns True if the booking starts and ends
    within business hours.
    """

    booking_start = datetime.combine(
        datetime.today(),
        booking_time
    )

    booking_end = booking_start + timedelta(minutes=duration)

    opening = datetime.combine(
        datetime.today(),
        business_hours.opening_time
    )

    closing = datetime.combine(
        datetime.today(),
        business_hours.closing_time
    )

    return (
        booking_start >= opening and
        booking_end <= closing
    )

from datetime import datetime, timedelta
from bookings.models import Booking


def has_booking_conflict(
    tenant,
    booking_date,
    booking_time,
    duration,
):
    """
    Returns True if the new booking overlaps
    with any existing booking.
    """

    new_start = datetime.combine(
        booking_date,
        booking_time
    )

    new_end = new_start + timedelta(minutes=duration)

    bookings = Booking.objects.filter(
        tenant=tenant,
        booking_date=booking_date
    )

    for booking in bookings:

        existing_start = datetime.combine(
            booking.booking_date,
            booking.booking_time
        )

        existing_end = (
            existing_start +
            timedelta(
                minutes=booking.service.duration
            )
        )

        if (
            new_start < existing_end and
            new_end > existing_start
        ):
            return True

    return False
