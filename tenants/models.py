from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Tenant(models.Model):

    BUSINESS_TYPES = [
        ("restaurant", "Restaurant"),
        ("salon", "Salon"),
        ("clinic", "Clinic"),
        ("sports_turf", "Sports Turf"),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tenants"
    )

    business_name = models.CharField(max_length=255)

    slug = models.SlugField(unique=True)

    business_type = models.CharField(
        max_length=30,
        choices=BUSINESS_TYPES
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.business_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.business_name