from ai_assistant.services.gemini import (
    generate_ai_response as gemini_generate_ai_response,
    extract_business_info as gemini_extract_business_info,
    extract_booking_request as gemini_extract_booking_request,
)

from ai_assistant.services.ollama import (
    generate_ai_response as ollama_generate_ai_response,
    extract_business_info as ollama_extract_business_info,
    extract_booking_request as ollama_extract_booking_request,
)


# =========================================================
# AI RESPONSE
# Gemini → Ollama fallback
# =========================================================

def generate_ai_response(conversation_history):

    try:
        print("Trying Gemini...")

        return gemini_generate_ai_response(
            conversation_history
        )

    except Exception as e:

        print("Gemini failed:", e)
        print("Falling back to Ollama...")

        return ollama_generate_ai_response(
            conversation_history
        )


# =========================================================
# BUSINESS INFORMATION EXTRACTION
# Gemini → Ollama fallback
# =========================================================

def extract_business_info(text):

    try:
        print("Trying Gemini business extraction...")

        return gemini_extract_business_info(text)

    except Exception as e:

        print("Gemini failed:", e)
        print("Falling back to Ollama...")

        return ollama_extract_business_info(text)


# =========================================================
# BOOKING REQUEST EXTRACTION
# Gemini → Ollama fallback
# =========================================================

def extract_booking_request(text):

    try:
        print("Trying Gemini booking extraction...")

        return gemini_extract_booking_request(text)

    except Exception as e:

        print("Gemini failed:", e)
        print("Falling back to Ollama...")

        return ollama_extract_booking_request(text)