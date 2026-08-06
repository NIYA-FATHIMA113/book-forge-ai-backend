from django.db import models
from tenants.models import Tenant


class Booking(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15)

    booking_date = models.DateField()
    booking_time = models.TimeField()

    service = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.tenant.business_name}"