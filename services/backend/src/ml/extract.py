"""
Project Pukar - SOS Free-Text Entity Extraction Engine
======================================================

Overview:
---------
Turns unstructured distress free-text (English, Hindi, Hinglish) into dispatch-ready
structured intelligence (`Entities` Pydantic model).

Key Capabilities:
-----------------
1. Structured Extraction:
   - `people_count`: int | None (accurate headcount without hallucinations)
   - `injuries`: list[str] (bleeding, fracture, burns, unconscious, head trauma)
   - `hazards`: list[str] (structural_collapse, fire, flood, gas_leak, electrocution)
   - `needs`: list[NeedCategory] (rescue, medical, fire, shelter, evacuation)
   - `landmarks`: list[str] (roof, basement, near hospital, metro station, etc.)
   - `mobility`: MobilityStatus (trapped, mobile, unknown)
   - `vulnerable`: list[str] (child, elderly, disabled, pregnant)
2. Per-Field Graceful Degradation:
   - Queries Groq with strict JSON output.
   - If Groq fails, times out, or returns malformed fields, degrades each field to
     multilingual deterministic regex / keyword extraction from `extract_rules.yaml`.
3. Anti-Fabrication Principle:
   - Absent information resolves to `None`, `[]`, or `MobilityStatus.UNKNOWN` — never guesses.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

from .contracts import Entities, MobilityStatus, NeedCategory
from .groq_client import GroqClient
from .guard import get_guard_system_instruction, sanitize, wrap_untrusted_data

logger = logging.getLogger("pukar.ml.extract")


class RuleBasedEntityExtractor:
    """
    Deterministic multilingual entity extractor using regex patterns from extract_rules.yaml.
    """

    def __init__(self, rules_path: str | Path | None = None):
        self.rules_path = self._resolve_rules_path(rules_path)
        self.rules = self._load_rules()
        self._compiled_patterns = self._compile_rules()

    def _resolve_rules_path(self, custom_path: str | Path | None) -> Path:
        if custom_path:
            return Path(custom_path)

        candidates = [
            Path(__file__).parent / "configs" / "extract_rules.yaml",
            Path(__file__).resolve().parents[4] / "ml" / "configs" / "extract_rules.yaml",
            Path("ml/configs/extract_rules.yaml"),
        ]
        for c in candidates:
            if c.exists():
                return c
        return candidates[0]

    def _load_rules(self) -> dict[str, Any]:
        if self.rules_path and self.rules_path.exists():
            try:
                with open(self.rules_path, encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load extract_rules.yaml from {self.rules_path}: {e}")
        return {}

    def _compile_rules(self) -> dict[str, Any]:
        compiled: dict[str, Any] = {
            "people_count_patterns": [],
            "word_numbers": self.rules.get("people_count", {}).get("word_numbers", {}),
            "injuries": [],
            "hazards": [],
            "needs": [],
            "landmarks_structural": [],
            "landmarks_patterns": [],
            "mobility_trapped": [],
            "mobility_mobile": [],
            "vulnerable": [],
        }

        # People count patterns
        for p in self.rules.get("people_count", {}).get("patterns", []):
            try:
                compiled["people_count_patterns"].append(re.compile(p["regex"]))
            except Exception as e:
                logger.error(f"Error compiling people_count pattern {p}: {e}")

        # Injuries
        for r in self.rules.get("injuries", {}).get("rules", []):
            try:
                compiled["injuries"].append((re.compile(r["regex"]), r.get("label", r["id"])))
            except Exception as e:
                logger.error(f"Error compiling injury rule {r}: {e}")

        # Hazards
        for r in self.rules.get("hazards", {}).get("rules", []):
            try:
                compiled["hazards"].append((re.compile(r["regex"]), r.get("label", r["id"])))
            except Exception as e:
                logger.error(f"Error compiling hazard rule {r}: {e}")

        # Needs
        for r in self.rules.get("needs", {}).get("rules", []):
            try:
                compiled["needs"].append((re.compile(r["regex"]), r.get("category", r["id"])))
            except Exception as e:
                logger.error(f"Error compiling need rule {r}: {e}")

        # Landmarks
        for s in self.rules.get("landmarks", {}).get("structural_locations", []):
            try:
                compiled["landmarks_structural"].append((re.compile(s["regex"]), s.get("label", "landmark")))
            except Exception as e:
                logger.error(f"Error compiling structural landmark {s}: {e}")

        for p in self.rules.get("landmarks", {}).get("patterns", []):
            try:
                compiled["landmarks_patterns"].append(re.compile(p["regex"]))
            except Exception as e:
                logger.error(f"Error compiling landmark pattern {p}: {e}")

        # Mobility
        for p in self.rules.get("mobility", {}).get("trapped_patterns", []):
            try:
                compiled["mobility_trapped"].append(re.compile(p))
            except Exception as e:
                logger.error(f"Error compiling trapped pattern {p}: {e}")

        for p in self.rules.get("mobility", {}).get("mobile_patterns", []):
            try:
                compiled["mobility_mobile"].append(re.compile(p))
            except Exception as e:
                logger.error(f"Error compiling mobile pattern {p}: {e}")

        # Vulnerable
        for r in self.rules.get("vulnerable", {}).get("rules", []):
            try:
                compiled["vulnerable"].append((re.compile(r["regex"]), r.get("label", r["id"])))
            except Exception as e:
                logger.error(f"Error compiling vulnerable rule {r}: {e}")

        return compiled

    def extract_people_count(self, text: str) -> int | None:
        """Extracts explicit headcount from text."""
        if not text:
            return None

        # 1. Regex with capture group (?P<count>\d+)
        for pat in self._compiled_patterns["people_count_patterns"]:
            match = pat.search(text)
            if match and "count" in match.groupdict():
                try:
                    count = int(match.group("count"))
                    if count > 0:
                        return count
                except (ValueError, TypeError):
                    pass

        # 2. Word numbers + context e.g. "teen log", "three people", "ek bacche"
        word_numbers = self._compiled_patterns["word_numbers"]
        for word, val in word_numbers.items():
            pattern = rf"(?i)\b{word}\s+(?:people|persons?|members?|log|bachhe|bache|jan|vyakti|baccha|bacche|victims?)\b"
            if re.search(pattern, text):
                return val

        # 3. Direct single number mention near emergency tokens
        direct_match = re.search(r"(?i)\b(?P<count>[1-9]\d?)\s+(?:fase|trapped|dabe|injured|ghayal)\b", text)
        if direct_match:
            try:
                return int(direct_match.group("count"))
            except (ValueError, TypeError):
                pass

        return None

    def extract_injuries(self, text: str) -> list[str]:
        """Extracts physical injuries and trauma conditions."""
        if not text:
            return []

        injuries = []
        for pat, label in self._compiled_patterns["injuries"]:
            if pat.search(text) and label not in injuries:
                injuries.append(label)
        return injuries

    def extract_hazards(self, text: str) -> list[str]:
        """Extracts active disaster hazards."""
        if not text:
            return []

        hazards = []
        for pat, label in self._compiled_patterns["hazards"]:
            if pat.search(text) and label not in hazards:
                hazards.append(label)
        return hazards

    def extract_needs(self, text: str) -> list[NeedCategory]:
        """Extracts required operational capabilities."""
        if not text:
            return []

        needs = []
        for pat, category in self._compiled_patterns["needs"]:
            if pat.search(text):
                try:
                    need_enum = NeedCategory(category.lower())
                    if need_enum not in needs:
                        needs.append(need_enum)
                except ValueError:
                    pass
        return needs

    def extract_landmarks(self, text: str) -> list[str]:
        """Extracts physical and structural location references."""
        if not text:
            return []

        landmarks = []
        for pat, label in self._compiled_patterns["landmarks_structural"]:
            if pat.search(text) and label not in landmarks:
                landmarks.append(label)

        for pat in self._compiled_patterns["landmarks_patterns"]:
            match = pat.search(text)
            if match:
                matched_str = match.group(1).strip()
                if len(matched_str) >= 3 and matched_str not in landmarks:
                    landmarks.append(matched_str)

        return landmarks

    def extract_mobility(self, text: str) -> MobilityStatus:
        """Extracts victim mobility / entrapment status."""
        if not text:
            return MobilityStatus.UNKNOWN

        for pat in self._compiled_patterns["mobility_trapped"]:
            if pat.search(text):
                return MobilityStatus.TRAPPED

        for pat in self._compiled_patterns["mobility_mobile"]:
            if pat.search(text):
                return MobilityStatus.MOBILE

        return MobilityStatus.UNKNOWN

    def extract_vulnerable(self, text: str) -> list[str]:
        """Extracts presence of vulnerable demographics."""
        if not text:
            return []

        vulnerable = []
        for pat, label in self._compiled_patterns["vulnerable"]:
            if pat.search(text) and label not in vulnerable:
                vulnerable.append(label)
        return vulnerable

    def extract_all(self, canonical_en: str, original: str) -> Entities:
        """Combines extraction across canonical English and verbatim original."""
        combined_text = f"{canonical_en} {original}".strip()

        people_count = self.extract_people_count(canonical_en) or self.extract_people_count(original)
        injuries = self.extract_injuries(combined_text)
        hazards = self.extract_hazards(combined_text)
        needs = self.extract_needs(combined_text)
        landmarks = self.extract_landmarks(combined_text)
        mobility = self.extract_mobility(combined_text)
        vulnerable = self.extract_vulnerable(combined_text)

        return Entities(
            people_count=people_count,
            injuries=injuries,
            hazards=hazards,
            needs=needs,
            landmarks=landmarks,
            mobility=mobility,
            vulnerable=vulnerable,
        )


# Global default rule-based extractor
_DEFAULT_RULE_EXTRACTOR = RuleBasedEntityExtractor()


# ==========================================
# Groq-Powered Structured Intelligence Extractor
# ==========================================

def _extract_via_groq(
    canonical_en: str,
    original: str,
    groq_client: GroqClient,
    timeout: float = 2.0,
) -> dict[str, Any]:
    """Queries Groq with strict JSON output schema."""
    if not groq_client._client:
        return {}

    guard_canonical = sanitize(canonical_en)
    guard_original = sanitize(original)

    system_prompt = (
        "You are the Crisis SOS Entity Extraction Engine for Project Pukar (Emergency Mesh Platform).\n"
        "Extract structured, dispatch-ready intelligence from the emergency distress message.\n"
        "Input text may be in English, Hindi, or Hinglish.\n"
        "CRITICAL RULE: Never fabricate or guess. If an entity or attribute is not explicitly mentioned, "
        "set people_count to null, lists to empty [], and mobility to 'unknown'.\n"
        "\n"
        "Respond with STRICT JSON matching this schema:\n"
        "{\n"
        '  "people_count": <integer count or null>,\n'
        '  "injuries": [<list of strings e.g. "bleeding", "fracture", "head_injury", "burns", "unconscious">],\n'
        '  "hazards": [<list of strings e.g. "structural_collapse", "fire", "flood", "gas_leak", "electrocution", "landslide">],\n'
        '  "needs": [<list of strings from: "rescue", "medical", "fire", "shelter", "evacuation">],\n'
        '  "landmarks": [<list of strings e.g. "roof", "basement", "near temple", "bridge">],\n'
        '  "mobility": "trapped" | "mobile" | "unknown",\n'
        '  "vulnerable": [<list of strings e.g. "child", "elderly", "disabled", "pregnant">]\n'
        "}\n\n"
        f"{get_guard_system_instruction()}"
    )

    user_message = (
        f"CANONICAL ENGLISH DATA:\n{wrap_untrusted_data(guard_canonical.sanitized_text)}\n\n"
        f"ORIGINAL TEXT DATA:\n{wrap_untrusted_data(guard_original.sanitized_text)}"
    )

    response = groq_client._client.chat.completions.create(
        model=groq_client.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.0,
        max_tokens=250,
        response_format={"type": "json_object"},
        timeout=timeout,
    )

    raw_content = response.choices[0].message.content or "{}"
    return json.loads(raw_content)


def extract(
    canonical_en: str,
    original: str,
    groq_client: GroqClient | None = None,
    timeout: float = 2.0,
    rule_extractor: RuleBasedEntityExtractor | None = None,
) -> Entities:
    """
    Extracts structured dispatch-ready intelligence from free-text distress calls.

    Execution Flow:
    1. Tries high-fidelity Groq LLM extraction.
    2. Validates each field against Pydantic constraints.
    3. On any field failure or if Groq is unavailable, seamlessly degrades to
       multilingual regex / keyword fallback rules from extract_rules.yaml.

    Args:
        canonical_en: Canonical English working text.
        original: Verbatim raw distress message.
        groq_client: Optional GroqClient instance.
        timeout: Timeout for LLM call.
        rule_extractor: Optional custom RuleBasedEntityExtractor.

    Returns:
        Validated Entities model.
    """
    rules = rule_extractor or _DEFAULT_RULE_EXTRACTOR
    combined_text = f"{canonical_en} {original}".strip()

    groq_data: dict[str, Any] = {}
    if groq_client and groq_client.is_available():
        try:
            groq_data = _extract_via_groq(
                canonical_en=canonical_en,
                original=original,
                groq_client=groq_client,
                timeout=timeout,
            )
        except Exception as e:
            logger.warning(f"Groq entity extraction failed or timed out: {e} - falling back to regex rules")
            groq_data = {}

    # 1. Resolve people_count
    people_count: int | None = None
    raw_count = groq_data.get("people_count")
    if raw_count is not None:
        try:
            val = int(raw_count)
            if val >= 0:
                people_count = val
        except (ValueError, TypeError):
            people_count = None
    if people_count is None:
        people_count = rules.extract_people_count(canonical_en) or rules.extract_people_count(original)

    # 2. Resolve injuries
    injuries: list[str] = []
    raw_injuries = groq_data.get("injuries")
    if isinstance(raw_injuries, list):
        injuries = [str(item).strip().lower() for item in raw_injuries if str(item).strip()]
    if not injuries:
        injuries = rules.extract_injuries(combined_text)

    # 3. Resolve hazards
    hazards: list[str] = []
    raw_hazards = groq_data.get("hazards")
    if isinstance(raw_hazards, list):
        hazards = [str(item).strip().lower() for item in raw_hazards if str(item).strip()]
    if not hazards:
        hazards = rules.extract_hazards(combined_text)

    # 4. Resolve needs
    needs: list[NeedCategory] = []
    raw_needs = groq_data.get("needs")
    if isinstance(raw_needs, list):
        for n in raw_needs:
            try:
                need_enum = NeedCategory(str(n).strip().lower())
                if need_enum not in needs:
                    needs.append(need_enum)
            except ValueError:
                pass
    if not needs:
        needs = rules.extract_needs(combined_text)

    # 5. Resolve landmarks
    landmarks: list[str] = []
    raw_landmarks = groq_data.get("landmarks")
    if isinstance(raw_landmarks, list):
        landmarks = [str(item).strip() for item in raw_landmarks if str(item).strip()]
    if not landmarks:
        landmarks = rules.extract_landmarks(combined_text)

    # 6. Resolve mobility
    mobility: MobilityStatus = MobilityStatus.UNKNOWN
    raw_mobility = str(groq_data.get("mobility", "")).strip().lower()
    try:
        if raw_mobility in ("trapped", "mobile", "unknown"):
            mobility = MobilityStatus(raw_mobility)
        else:
            mobility = rules.extract_mobility(combined_text)
    except ValueError:
        mobility = rules.extract_mobility(combined_text)
    if mobility == MobilityStatus.UNKNOWN:
        mobility = rules.extract_mobility(combined_text)

    # 7. Resolve vulnerable
    vulnerable: list[str] = []
    raw_vulnerable = groq_data.get("vulnerable")
    if isinstance(raw_vulnerable, list):
        vulnerable = [str(item).strip().lower() for item in raw_vulnerable if str(item).strip()]
    if not vulnerable:
        vulnerable = rules.extract_vulnerable(combined_text)

    return Entities(
        people_count=people_count,
        injuries=injuries,
        hazards=hazards,
        needs=needs,
        landmarks=landmarks,
        mobility=mobility,
        vulnerable=vulnerable,
    )
