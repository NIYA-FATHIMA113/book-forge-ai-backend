import json
import os
import re

from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from google import genai
from google.genai import types

from ai_assistant.schemas import BusinessInfo, BookingRequest, ServiceInfo

load_dotenv()


# =========================================================
# ENVIRONMENT
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-oss-20b",
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)


# =========================================================
# CLIENTS
# =========================================================

groq_client = (
    Groq(api_key=GROQ_API_KEY)
    if GROQ_API_KEY
    else None
)

openrouter_client = (
    OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    if OPENROUTER_API_KEY
    else None
)

gemini_client = (
    genai.Client(api_key=GEMINI_API_KEY)
    if GEMINI_API_KEY
    else None
)


# =========================================================
# GENERAL BOOKFORGE SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are BookForge AI.

BookForge helps small-business owners create and configure
their own online booking platform.

You are assisting the BUSINESS OWNER, not the customer.

Your responsibilities include:

- understanding the owner's business
- collecting business information
- understanding services or facilities
- understanding booking requirements
- understanding business hours
- understanding working days
- understanding bookable resources
- helping configure the booking platform
- answering questions about the owner's configured business

IMPORTANT:

The Django backend is responsible for deciding which information
is still missing and which actions should be performed.

You must NOT invent business information.

You should use the conversation context when answering.

Keep responses concise, natural and helpful.
"""


# =========================================================
# MESSAGE NORMALIZATION
# =========================================================

def normalize_messages(messages):
    """
    Convert BookForge/Gemini-style conversation messages
    into OpenAI-compatible chat messages.
    """

    normalized = []

    for message in messages:

        role = message.get("role", "user")

        if role == "model":
            role = "assistant"

        content = message.get("content")

        if content is None:

            parts = message.get("parts", [])

            text_parts = []

            for part in parts:

                if isinstance(part, dict):
                    text = part.get("text")

                    if text:
                        text_parts.append(text)

            content = "\n".join(text_parts)

        if not content:
            continue

        normalized.append(
            {
                "role": role,
                "content": str(content),
            }
        )

    return normalized


# =========================================================
# GROQ CHAT
# =========================================================

def groq_generate(messages):

    if not groq_client:
        raise RuntimeError("Groq API key is not configured.")

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=(
            [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                }
            ]
            + normalize_messages(messages)
        ),
        temperature=0.2,
        max_tokens=1000,
    )

    return response.choices[0].message.content


# =========================================================
# OPENROUTER CHAT
# =========================================================

def openrouter_generate(messages):

    if not openrouter_client:
        raise RuntimeError(
            "OpenRouter API key is not configured."
        )

    response = openrouter_client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=(
            [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                }
            ]
            + normalize_messages(messages)
        ),
        temperature=0.2,
        max_tokens=1000,
    )

    return response.choices[0].message.content


# =========================================================
# GEMINI CHAT
# =========================================================

def gemini_generate(messages):

    if not gemini_client:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    gemini_messages = []

    for message in messages:

        role = message.get("role", "user")

        if role == "assistant":
            role = "model"

        content = message.get("content")

        if content is None:

            parts = message.get("parts", [])

            text_parts = []

            for part in parts:

                if isinstance(part, dict):

                    text = part.get("text")

                    if text:
                        text_parts.append(text)

            content = "\n".join(text_parts)

        if not content:
            continue

        gemini_messages.append(
            types.Content(
                role=role,
                parts=[
                    types.Part(
                        text=str(content)
                    )
                ],
            )
        )

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=gemini_messages,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
        ),
    )

    return response.text


# =========================================================
# JSON / TIME / DAY / EXTRACTION HELPERS
# =========================================================

def parse_json_response(raw):
    """
    Parse and normalize a provider JSON blob into a dictionary that
    the Pydantic BusinessInfo model can validate.
    """
    if isinstance(raw, dict):
        return raw

    if isinstance(raw, (str, bytes)):
        text = raw.strip() if isinstance(raw, str) else raw.decode("utf-8")
        if not text:
            return {}
        if text.startswith("```"):
            text = re.sub(r"```(?:json)?", "", text).strip()

        try:
            return json.loads(text)
        except Exception:
            try:
                # Some providers wrap JSON in a descriptive envelope.
                return json.loads(text.split("{", 1)[1].rsplit("}", 1)[0])
            except Exception:
                return {}

    return {}


DAY_MAP = {
    "monday": "Monday",
    "tuesday": "Tuesday",
    "wednesday": "Wednesday",
    "thursday": "Thursday",
    "friday": "Friday",
    "saturday": "Saturday",
    "sunday": "Sunday",
}


def normalize_day_name(value):
    key = str(value).strip().lower()
    return DAY_MAP.get(key, str(value).strip().title())


def normalize_time_text(value):
    """Convert common AI-extracted time strings into 24-hour HH:MM."""
    if not value:
        return None

    text = str(value).strip().lower()
    text = text.replace(".", "").replace(";", "")

    # If already a pure HH:MM expression.
    if re.fullmatch(r"\d{1,2}:\d{2}", text):
        pieces = text.split(":")
        hour = int(pieces[0])
        minute = int(pieces[1])
        if hour > 23 or minute > 59:
            return None
        return f"{hour:02d}:{minute:02d}"

    match = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        meridian = match.group(3)
        if meridian == "am":
            if hour == 12:
                hour = 0
        else:
            if hour != 12:
                hour += 12
        if hour > 23 or minute > 59:
            return None
        return f"{hour:02d}:{minute:02d}"

    # Fallback for parser output that has a different layout.
    try:
        from datetime import datetime
        parsed = datetime.strptime(text, "%I:%M %p")
        return parsed.strftime("%H:%M")
    except Exception:
        return None


def extract_time_range(text):
    """Return (opening_time, closing_time) from a message with a natural time range."""
    if not text:
        return (None, None)

    value = str(text).strip()
    patterns = [
        r"(?P<open>\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\s*(?:to|-|–)\s*(?P<close>\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)",
        r"(?P<open>\d{1,2}:\d{2})\s*(?:to|-|–)\s*(?P<close>\d{1,2}:\d{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, value, flags=re.I)
        if not match:
            continue

        open_text = match.group("open")
        close_text = match.group("close")
        open_24 = normalize_time_text(open_text)
        close_24 = normalize_time_text(close_text)
        if open_24 and close_24:
            return open_24, close_24

    # Otherwise capture first two explicit HH:MM values in the message.
    hms = re.findall(r"\d{1,2}:\d{2}", value)
    if len(hms) >= 2:
        return hms[0], hms[1]

    return (None, None)


def expand_working_days_from_text(text):
    """Return a day list expanded from day range or list text in the owner message."""
    if not text:
        return []

    raw = str(text)
    lower = raw.lower()
    ordered = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    range_match = re.search(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b\s*(?:to|-)\s*\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", lower, flags=re.I)
    if range_match:
        start = normalize_day_name(range_match.group(1))
        end = normalize_day_name(range_match.group(2))
        try:
            start_idx = ordered.index(start)
            end_idx = ordered.index(end)
            if end_idx < start_idx:
                end_idx += len(ordered)
            days = ordered[start_idx:end_idx + 1]
            # Keep a simple week view and remove duplicates from the same range.
            return [d for d in days if d]
        except ValueError:
            pass

    # For a list like 'Monday, Wednesday and Friday', recover explicit matches.
    explicit_days = []
    for day in ordered:
        if re.search(rf"\b{day}\b", raw, flags=re.I):
            explicit_days.append(day)

    return explicit_days


def normalize_business_type(value):
    """Normalize the stored business type for the project bookkeeping."""
    if not value:
        return ""

    text = str(value).strip().lower()
    mapping = {
        "football turf": "sports_turf",
        "sports turf": "sports_turf",
        "turf": "sports_turf",
        "football ground": "sports_turf",
        "football pitch": "sports_turf",
        "sports facility": "sports_turf",
    }

    return mapping.get(text, text)


def assert_fallback_business_info(text):
    """
    Deterministic fallback parser for the message currently being processed.
    It safely extracts fields even when all LLM providers fail or return
    an empty structured object.
    """
    info = BusinessInfo()
    message = str(text or "")
    lower = message.lower()

    # Preserve the business name by taking the exact phrase after 'called'.
    match = re.search(
        r"\b(?:called|named|known as)\s+([A-Za-z0-9][A-Za-z0-9\s&'\-\.]+?)(?:[.?!,]|$)",
        message,
        flags=re.I,
    )
    if match:
        candidate = match.group(1).strip()
        if candidate:
            info.business_name = candidate

    # Business type from football turf / sport turf wording.
    if re.search(r"\bfootball\s+turf\b|\bsports\s+turf\b|\bturf\b|\bfootball\s+ground\b|\bfootball\s+pitch\b", lower):
        info.business_type = "sports_turf"

    # Services: parse the sentence after the intro and preserve each service token in order.
    service_text = message
    service_text = re.sub(r"\b(?:I run|We run|I own|We own|My business|Our business)\b.*?\b(?:called|named|known as)\b.*?", "", service_text, flags=re.I)
    service_text = re.sub(r"\b(?:I run|We run|I own|We own|My business|Our business)\b.*?", "", service_text, flags=re.I)
    service_text = re.sub(r"\b(?:we offer|we provide|we have|our services include|services include|our service include)\b", "", service_text, flags=re.I)

    chunks = re.split(r"[,;]+|\band\b|\bplus\b", service_text, flags=re.I)
    candidates = []
    for chunk in chunks:
        raw = re.sub(r"[^A-Za-z0-9\-\s]", "", chunk).strip()
        if not raw:
            continue
        lowered = raw.lower()
        if lowered in {"football turf", "sports turf", "turf", ""}:
            continue
        if any(token in lowered for token in ["opening", "closing", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "business", "time", "hours", "days"]):
            continue
        raw = re.sub(r"\b(?:offer|offers|provided|provide|service|services|facility|facilities|include|includes)\b", "", raw, flags=re.I)
        raw = re.sub(r"\s+", " ", raw).strip()
        if raw and raw.lower() not in {"football turf", "sports turf", "turf", ""}:
            candidates.append(raw)

    seen = set()
    service_infos = []
    for name in candidates:
        key = name.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        service_infos.append(ServiceInfo(name=name.strip(), price=None, duration_minutes=None))

    if service_infos:
        info.services = service_infos

    # Time range.
    opening, closing = extract_time_range(message)
    if opening:
        info.opening_time = opening
    if closing:
        info.closing_time = closing

    # Working days.
    days = expand_working_days_from_text(message)
    if days:
        info.working_days = days

    # Number of resources if a natural phrase like 'We have 2 football pitches' appears.
    resources = re.search(r"\b(?:have|offer|offers|with|including)\s+(\d+)\s+(?:football\s+pitches?|pitches?|resources?|courts?|tables?|chairs?|rooms?)\b", message, flags=re.I)
    if resources:
        info.number_of_resources = int(resources.group(1))

    return info


# =========================================================
# GENERAL AI RESPONSE WITH FALLBACK
# =========================================================

def generate_ai_response(messages):

    if not messages:
        raise RuntimeError("No valid user message")

    normalized = normalize_messages(messages)
    valid_user_message = any(
        item.get("role") == "user" and str(item.get("content", "")).strip()
        for item in normalized
    )

    if not valid_user_message:
        raise RuntimeError("No valid user message")

    providers = [
        ("Gemini", gemini_generate),
        ("Groq", groq_generate),
        ("OpenRouter", openrouter_generate),
    ]

    errors = []

    for provider_name, provider_function in providers:

        try:

            print(f"Trying {provider_name}...")

            response = provider_function(messages)

            if response:
                print(
                    f"{provider_name} succeeded."
                )

                return response

        except Exception as error:

            print(
                f"{provider_name} failed: {error}"
            )

            errors.append(
                f"{provider_name}: {error}"
            )

    return (
        "I'm having trouble connecting to the AI service "
        "right now. Please try again."
    )


# =========================================================
# BUSINESS EXTRACTION PROMPT
# =========================================================

BUSINESS_EXTRACTION_PROMPT = """
You are the structured information extraction engine
for BookForge AI.

Extract ONLY information explicitly provided by the
business owner.

NEVER invent values.

Return JSON matching the BusinessInfo schema.

Extract these fields when present:

business_name
business_type
services
booking_deposit
opening_time
closing_time
working_days
location
contact_phone
contact_email
booking_length_minutes
number_of_resources

IMPORTANT TIME RULES:

If the owner says:

"6 AM to 11 PM"

return:

opening_time = "06:00"
closing_time = "23:00"

If the owner says:

"9 AM to 7 PM"

return:

opening_time = "09:00"
closing_time = "19:00"

NEVER put the entire time range into one field.

Convert times to 24-hour HH:MM format.

Examples:

"6 in the morning" -> "06:00"
"6:30 AM" -> "06:30"
"11 PM" -> "23:00"
"10:30 PM" -> "22:30"

WORKING DAYS:

"Monday to Saturday"
should become:

["Monday", "Tuesday", "Wednesday",
 "Thursday", "Friday", "Saturday"]

"Monday, Wednesday and Friday"
should become:

["Monday", "Wednesday", "Friday"]

SERVICES:

If the owner says:

"5-a-side football, 7-a-side football,
birthday matches and tournaments"

extract all of them as separate services.

Do not ask questions.

Do not generate conversational text.

Return ONLY structured JSON.

Business owner's message:

"""


# =========================================================
# EXTRACTION USING GROQ
# =========================================================

def extract_business_info_with_groq(text):

    if not groq_client:
        raise RuntimeError("Groq API key is not configured.")

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": BUSINESS_EXTRACTION_PROMPT,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        temperature=0,
        max_tokens=1500,
        response_format={
            "type": "json_object"
        },
    )

    content = response.choices[0].message.content

    data = json.loads(content)

    return BusinessInfo.model_validate(data)


# =========================================================
# EXTRACTION USING OPENROUTER
# =========================================================

def extract_business_info_with_openrouter(text):

    if not openrouter_client:
        raise RuntimeError(
            "OpenRouter API key is not configured."
        )

    response = openrouter_client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {
                "role": "system",
                "content": BUSINESS_EXTRACTION_PROMPT,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        temperature=0,
        max_tokens=1500,
        response_format={
            "type": "json_object"
        },
    )

    content = response.choices[0].message.content

    data = json.loads(content)

    return BusinessInfo.model_validate(data)


# =========================================================
# EXTRACTION USING GEMINI
# =========================================================

def extract_business_info_with_gemini(text):

    if not gemini_client:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=(
            BUSINESS_EXTRACTION_PROMPT
            + "\n\n"
            + text
        ),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BusinessInfo,
            temperature=0,
        ),
    )

    if response.parsed:

        return BusinessInfo.model_validate(
            response.parsed
        )

    data = json.loads(response.text)

    return BusinessInfo.model_validate(data)


# =========================================================
# BUSINESS EXTRACTION WITH FALLBACK
# =========================================================

def extract_business_info(text):

    providers = [
        (
            "Groq",
            extract_business_info_with_groq,
        ),
        (
            "Gemini",
            extract_business_info_with_gemini,
        ),
        (
            "OpenRouter",
            extract_business_info_with_openrouter,
        ),
    ]

    for provider_name, provider_function in providers:

        try:

            print(
                f"Trying {provider_name} "
                f"for business extraction..."
            )

            result = provider_function(text)

            print(
                f"{provider_name} extraction succeeded."
            )

            return result

        except Exception as error:

            print(
                f"{provider_name} extraction failed: "
                f"{error}"
            )

    return BusinessInfo()


# =========================================================
# BOOKING EXTRACTION
# =========================================================

def extract_booking_request(text):

    prompt = """
Extract booking information from the customer message.

Only extract information explicitly provided.

Do not invent information.

Return JSON matching BookingRequest.

Convert exact dates to YYYY-MM-DD when possible.

Convert explicit times to HH:MM 24-hour format.

If information is missing, return null.

Customer message:
"""

    providers = []

    if groq_client:
        providers.append(
            ("Groq", groq_client)
        )

    if openrouter_client:
        providers.append(
            ("OpenRouter", openrouter_client)
        )

    for provider_name, client in providers:

        try:

            response = client.chat.completions.create(
                model=(
                    GROQ_MODEL
                    if provider_name == "Groq"
                    else OPENROUTER_MODEL
                ),
                messages=[
                    {
                        "role": "system",
                        "content": prompt,
                    },
                    {
                        "role": "user",
                        "content": text,
                    },
                ],
                temperature=0,
                max_tokens=1000,
                response_format={
                    "type": "json_object"
                },
            )

            data = json.loads(
                response.choices[0]
                .message.content
            )

            return BookingRequest.model_validate(
                data
            )

        except Exception as error:

            print(
                f"{provider_name} booking extraction "
                f"failed: {error}"
            )

    return BookingRequest()