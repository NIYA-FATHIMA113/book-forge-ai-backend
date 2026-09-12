from datetime import time
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from ai_assistant.services.ai_provider import extract_time_range
from ai_assistant.schemas import BookingRequest, BusinessInfo
from ai_assistant.services.ai_provider import (
	extract_booking_request,
	generate_ai_response,
	normalize_messages,
	parse_json_response,
	assert_fallback_business_info,
)
from ai_assistant.models import AIConversation, BusinessConfiguration
from ai_assistant.services.business_setup import create_business_from_configuration
from ai_assistant.views import get_onboarding_question
from services.models import Service, Resource
from availability.models import BusinessHours


class AIProviderTests(TestCase):

	def test_normalize_messages_accepts_gemini_parts(self):
		messages = normalize_messages([
			{
				"role": "user",
				"parts": [{"text": "hello"}],
			},
			{
				"role": "model",
				"parts": [{"text": "hi"}],
			},
		])

		self.assertEqual(messages[-2:], [
			{"role": "user", "content": "hello"},
			{"role": "assistant", "content": "hi"},
		])

	def test_provider_fallback_continues_after_gemini_failure(self):
		with patch(
			"ai_assistant.services.ai_provider.gemini_generate",
			side_effect=RuntimeError("quota"),
		), patch(
			"ai_assistant.services.ai_provider.groq_generate",
			return_value="Groq response",
		) as groq:
			result = generate_ai_response([
				{"role": "user", "content": "hello"},
			])

		self.assertEqual(result, "Groq response")
		groq.assert_called_once()

	def test_empty_history_is_rejected(self):
		with self.assertRaisesRegex(
			RuntimeError,
			"No valid user message",
		):
			generate_ai_response([
				{"role": "user", "parts": [{"text": "  "}]},
			])

	def test_extraction_contracts_are_typed(self):
		business = BusinessInfo.model_validate(
			parse_json_response('{"business_name": "BookForge"}')
		)
		booking = extract_booking_request("")

		self.assertEqual(business.business_name, "BookForge")
		self.assertIsInstance(booking, BookingRequest)

	def test_onboarding_asks_one_next_required_field(self):
		configuration = BusinessInfo()
		configuration.business_name = "Niya Turf"

		question = get_onboarding_question(
			configuration,
			["business_type", "services", "working_days"],
		)

		self.assertEqual(
			question,
			"Great! I'll help you set up Niya Turf. "
			"What type of business do you run?",
		)

	def test_services_answer_advances_authenticated_onboarding(self):
		user = User.objects.create_user(
			username="onboarding-owner",
			password="test-password",
		)
		client = APIClient()
		client.force_authenticate(user=user)
		business_info = BusinessInfo(
			business_name="Hightown Turf",
			business_type="sports_turf",
		)
		services_info = BusinessInfo(
			services=[
				{"name": "Service One"},
				{"name": "Service Two"},
			],
		)

		with patch(
			"ai_assistant.views.extract_business_info",
			side_effect=[business_info, services_info],
		):
			first = client.post(
				"/api/ai/chat/",
				{"message": "I run a business called Hightown Turf."},
				format="json",
			)
			conversation_id = first.data["conversation_id"]
			second = client.post(
				"/api/ai/chat/",
				{
					"conversation_id": conversation_id,
					"message": "Service One and Service Two.",
				},
				format="json",
			)

		self.assertEqual(first.status_code, 200)
		self.assertEqual(second.status_code, 200)
		self.assertEqual(
			second.data["business_configuration"]["services"],
			[
				{"name": "Service One", "price": None, "duration_minutes": None},
				{"name": "Service Two", "price": None, "duration_minutes": None},
			],
		)
		self.assertNotIn(
			"services",
			second.data["business_configuration"]["missing_fields"],
		)

	def test_create_business_from_configuration_supports_sports_turf(self):
		user = User.objects.create_user(
			username="sports-owner",
			password="test-password",
		)
		conversation = AIConversation.objects.create(
			owner=user,
			title="Sports Turf Setup",
		)
		configuration = BusinessConfiguration.objects.create(
			conversation=conversation,
			business_name="Hightown Turf",
			business_type="sports_turf",
			services=[
				{"name": "5-a-side football"},
				{"name": "7-a-side football"},
				{"name": "birthday matches"},
				{"name": "tournament bookings"},
			],
			opening_time=time(6, 0),
			closing_time=time(23, 0),
			working_days=[
				"Monday",
				"Tuesday",
				"Wednesday",
				"Thursday",
				"Friday",
				"Saturday",
			],
			number_of_resources=2,
		)

		tenant = create_business_from_configuration(
			configuration,
			user,
			configuration.services,
		)

		self.assertEqual(tenant.business_name, "Hightown Turf")
		self.assertEqual(tenant.business_type, "sports_turf")
		self.assertEqual(Service.objects.filter(tenant=tenant).count(), 4)
		self.assertEqual(Resource.objects.filter(service__tenant=tenant).count(), 8)
		self.assertEqual(BusinessHours.objects.filter(tenant=tenant).count(), 6)

	def test_extract_time_range(self):
		self.assertEqual(
			extract_time_range("6:00 AM to 11:00 PM"),
			("06:00", "23:00"),
		)

		self.assertEqual(
			extract_time_range("6 AM - 11 PM"),
			("06:00", "23:00"),
		)

		self.assertEqual(
			extract_time_range("06:00 - 23:00"),
			("06:00", "23:00"),
		)

	def test_assert_fallback_business_info_preserves_name_and_services(self):
		business = assert_fallback_business_info(
			"I run a football turf called Hightown Turf."
		)
		self.assertEqual(business.business_name, "Hightown Turf")
		self.assertEqual(business.business_type, "sports_turf")

		services = assert_fallback_business_info(
			"We offer 5-a-side football, 7-a-side football, birthday matches, and tournament bookings."
		)
		names = [s.name for s in services.services]
		self.assertEqual(names, [
			"5-a-side football",
			"7-a-side football",
			"birthday matches",
			"tournament bookings",
		])

		time_info = assert_fallback_business_info("6 AM to 11 PM")
		self.assertEqual(time_info.opening_time, "06:00")
		self.assertEqual(time_info.closing_time, "23:00")