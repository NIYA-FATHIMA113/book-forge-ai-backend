from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from tenants.models import Tenant
from services.models import Service, Resource
from availability.models import BusinessHours
from bookings.models import Booking


User = get_user_model()


class BookingCreateAPITest(APITestCase):

    def setUp(self):

        # -----------------------------
        # Create owner
        # -----------------------------

        self.user = User.objects.create_user(
            username="testowner",
            password="testpassword123"
        )

        # -----------------------------
        # Create business
        # -----------------------------

        self.tenant = Tenant.objects.create(
            owner=self.user,
            business_name="Test Turf",
            business_type="sports_turf",
            slug="test-turf",
            is_active=True,
        )

        # -----------------------------
        # Create service
        # -----------------------------

        self.service = Service.objects.create(
            tenant=self.tenant,
            name="5-a-side pitch",
            price=800,
            duration=60,
            is_active=True,
        )

        # -----------------------------
        # Create resource
        # -----------------------------

        self.resource = Resource.objects.create(
            service=self.service,
            name="Resource 1",
            is_active=True,
        )

        # -----------------------------
        # Create business hours
        # -----------------------------

        # Monday -> 0
        BusinessHours.objects.create(
            tenant=self.tenant,
            day_of_week=0,
            opening_time=time(9, 0),
            closing_time=time(22, 0),
            is_closed=False,
        )

        # -----------------------------
        # API URL
        # -----------------------------

        self.url = reverse(
            "create-booking",
            kwargs={"slug": self.tenant.slug}
        )

    def test_create_booking_successfully(self):

        # Find next Monday
        today = date.today()

        days_until_monday = (
            7 - today.weekday()
        ) % 7

        if days_until_monday == 0:
            days_until_monday = 7

        booking_date = today + timedelta(
            days=days_until_monday
        )

        data = {
            "customer_name": "Rahul",
            "customer_phone": "9876543210",
            "booking_date": booking_date,
            "booking_time": "18:00",
            "service": self.service.id,
        }

        response = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            201
        )

        self.assertEqual(
            Booking.objects.count(),
            1
        )

        booking = Booking.objects.first()

        self.assertEqual(
            booking.customer_name,
            "Rahul"
        )

        self.assertEqual(
            booking.service,
            self.service
        )

        self.assertEqual(
            booking.resource,
            self.resource
        )

        self.assertEqual(
            booking.status,
            "PENDING"
        )
    def test_booking_outside_business_hours(self):

        today = date.today()

        days_until_monday = (
            7 - today.weekday()
        ) % 7

        if days_until_monday == 0:
            days_until_monday = 7

        booking_date = today + timedelta(
            days=days_until_monday
        )

        data = {
            "customer_name": "Rahul",
            "customer_phone": "9876543210",
            "booking_date": booking_date,
            "booking_time": "23:00",
            "service": self.service.id,
        }

        response = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertIn(
            "Booking is outside business hours.",
            str(response.data)
        )

        self.assertEqual(
            Booking.objects.count(),
            0
        )
    def test_double_booking_is_rejected(self):

        today = date.today()

        days_until_monday = (
            7 - today.weekday()
        ) % 7

        if days_until_monday == 0:
            days_until_monday = 7

        booking_date = today + timedelta(
            days=days_until_monday
        )

        data = {
            "customer_name": "Rahul",
            "customer_phone": "9876543210",
            "booking_date": booking_date,
            "booking_time": "18:00",
            "service": self.service.id,
        }

        # First booking
        response1 = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response1.status_code,
            201
        )

        # Second booking for the SAME resource/time
        data["customer_name"] = "Arjun"
        data["customer_phone"] = "9999999999"

        response2 = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response2.status_code,
            400
        )

        self.assertIn(
            "All resources are booked for this time slot.",
            str(response2.data)
        )

        # Only one booking should exist
        self.assertEqual(
            Booking.objects.count(),
            1
        )