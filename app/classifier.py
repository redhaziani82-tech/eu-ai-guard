import json
from google import genai
from google.genai import types
from app.config import settings


class EUAIActClassifier:
    def __init__(self):
        self.client = (
            genai.Client(api_key=settings.gemini_api_key)
            if settings.gemini_api_key
            else None
        )

    def evaluate(self, prompt: str) -> dict:
        if not self.client:
            return {
                "risk_level": "MINIMAL_RISK",
                "article_reference": "N/A",
                "reason": "API key not configured; running in local redaction mode.",
            }

        system_instruction = """
        You are an EU AI Act Compliance Engine (Regulation (EU) 2024/1689).
        Classify the user prompt strictly into one of four categories:
        1. PROHIBITED (Article 5: social scoring, subliminal manipulation, emotion recognition in workplace/education, untargeted facial scraping).
        2. HIGH_RISK (Annex III: biometric ID, critical infrastructure, education/vocational scoring, employment/HR screening, creditworthiness, law enforcement, medical triage).
        3. LIMITED_RISK (Article 50: chatbots, deepfakes, synthetic content requiring transparency disclosure).
        4. MINIMAL_RISK (General productivity, coding, summarization, standard business queries).

        Return valid JSON only:
        {"risk_level": "...", "article_reference": "...", "reason": "..."}
        """

        response = self.client.models.generate_content(
            model=settings.classifier_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )

        try:
            return json.loads(response.text)
        except Exception:
            return {
                "risk_level": "MINIMAL_RISK",
                "article_reference": "Fallback",
                "reason": "Unable to parse classifier output.",
            }
