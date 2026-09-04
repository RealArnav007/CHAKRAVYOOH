"""
Project Pukar - Groq LLM Cloud Intelligence Client
Provides deep semantic triage, entity extraction, and structured classification using Llama-3 on Groq.
Includes graceful fallback if Groq API is unconfigured or unavailable.
"""

import json
import os
from typing import Any

from dotenv import load_dotenv

from .contracts import EmergencyCategory, SeverityLevel

load_dotenv()


class GroqClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "llama3-70b-8192")
        self._client = None

        if self.api_key:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"[GroqClient] Notice: Groq SDK initialization deferred/failed: {e}")

    def is_available(self) -> bool:
        return bool(self._client and self.api_key)

    def analyze_message(self, text: str) -> dict[str, Any]:
        """
        Sends decrypted crisis text to Groq Llama-3 for structured triage.
        Returns parsed dictionary with urgency, severity, category, entities, and rationale.
        Degrades gracefully if Groq is unavailable.
        """
        if not self.is_available() or not text or not text.strip():
            return self._fallback_response("Groq API unavailable or unconfigured - fallback to rule scoring")

        system_prompt = (
            "You are the Crisis Intelligence Triage Engine for Project Pukar (Emergency Mesh SOS Platform). "
            "Analyze the given emergency message (which may be in English, Hindi, or Hinglish). "
            "You must return ONLY valid JSON matching this exact schema:\n"
            "{\n"
            '  "severity": "info" | "warn" | "critical",\n'
            '  "urgency_score": <int 0 to 100>,\n'
            '  "category": "rescue" | "medical" | "fire" | "shelter" | "hazard" | "other",\n'
            '  "confidence": <float 0.0 to 1.0>,\n'
            '  "is_trapped": <bool>,\n'
            '  "has_medical_need": <bool>,\n'
            '  "vulnerable_victims": <bool (children, pregnant, elderly)>,\n'
            '  "entities": [<list of strings, e.g. location, casualty count, hazard>],\n'
            '  "rationale": "<brief 1-sentence explanation of why this severity and priority was chosen>"\n'
            "}"
        )

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"EMERGENCY SOS MESSAGE:\n'''{text}'''"}
                ],
                temperature=0.1,
                max_tokens=256,
                response_format={"type": "json_object"}
            )
            
            raw_content = response.choices[0].message.content
            parsed = json.loads(raw_content)
            
            # Sanitize and validate fields
            sev_str = str(parsed.get("severity", "warn")).lower()
            if sev_str not in ["info", "warn", "critical"]:
                sev_str = "warn"

            cat_str = str(parsed.get("category", "other")).lower()
            valid_cats = ["rescue", "medical", "fire", "shelter", "hazard", "other"]
            if cat_str not in valid_cats:
                cat_str = "other"

            urgency = int(parsed.get("urgency_score", 50))
            urgency = max(0, min(100, urgency))

            conf = float(parsed.get("confidence", 0.8))
            conf = max(0.0, min(1.0, conf))

            return {
                "severity": SeverityLevel(sev_str),
                "urgency_score": urgency,
                "category": EmergencyCategory(cat_str),
                "confidence": conf,
                "is_trapped": bool(parsed.get("is_trapped", False)),
                "has_medical_need": bool(parsed.get("has_medical_need", False)),
                "vulnerable_victims": bool(parsed.get("vulnerable_victims", False)),
                "entities": list(parsed.get("entities", [])),
                "rationale": str(parsed.get("rationale", "Semantic evaluation completed")),
            }

        except Exception as e:
            return self._fallback_response(f"Groq invocation failed ({e!s}) - graceful fallback active")

    def _fallback_response(self, reason: str) -> dict[str, Any]:
        return {
            "severity": SeverityLevel.WARN,
            "urgency_score": 50,
            "category": EmergencyCategory.OTHER,
            "confidence": 0.5,
            "is_trapped": False,
            "has_medical_need": False,
            "vulnerable_victims": False,
            "entities": [],
            "rationale": reason,
        }
