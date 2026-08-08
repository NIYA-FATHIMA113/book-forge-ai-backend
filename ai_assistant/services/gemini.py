import os

from google import genai
from google.genai import types

from ai_assistant.schemas import BusinessInfo
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


SYSTEM_INSTRUCTION = """
You are the BookForge AI business setup assistant.

Your job is to help business owners create and configure
their online booking platform.

You should:
- Understand what type of business the owner operates.
- Ask useful questions about their business.
- Collect business name, business type, services,
  prices, durations, business hours, working days,
  and booking requirements.
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
Extract business information from the following message.

Only extract information that the business owner actually
provided.

Do not invent missing information.

Business owner message:

{text}
""",
        config={
            "response_mime_type": "application/json",
            "response_schema": BusinessInfo,
        },
    )

    return response.parsed