import os

from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types

from ai_assistant.schemas import (
    BusinessInfo,
    BookingRequest,
)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# =========================================================
# BUSINESS SETUP AI
# =========================================================


SYSTEM_INSTRUCTION = """
You are the BookForge AI business setup assistant.

Your job is to help business owners create and configure
their online booking platform.

You should:

- Understand what type of business the owner operates.
- Ask useful questions about their business.
- Collect business name, business type, services,
  prices, durations, business hours, and working days.
- Collect the number of independently bookable resources,
  such as pitches, rooms, chairs, doctors, courts, tables,
  or other resources.
- Collect booking requirements such as booking duration,
  deposit, payment requirements, and booking rules.
- Do not invent information that the owner has not provided.
- Ask relevant questions when information is missing.
- Keep responses clear and conversational.
"""




def generate_ai_response(conversation_history):

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=conversation_history,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )

    return response.text


def extract_business_info(text):

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"""
Extract business information from the following
business owner's message.

Only extract information that the owner actually provided.

Do not invent missing information.

If information is not provided, return null or an empty list.

Business owner's message:

{text}
""",
        config={
            "response_mime_type": "application/json",
            "response_schema": BusinessInfo,
        },
    )

    return response.parsed


# =========================================================
# BOOKING AI
# =========================================================

def extract_booking_request(text):

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"""
Extract booking information from the following customer message.

Only extract information that the customer actually provided.

Do not invent missing information.

If a value is not provided, return null.

Convert dates to YYYY-MM-DD format when possible.
Convert times to 24-hour HH:MM format when possible.

Customer message:

{text}
""",
        config={
            "response_mime_type": "application/json",
            "response_schema": BookingRequest,
        },
    )

    return response.parsed