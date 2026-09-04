"""
Project Pukar - Deterministic Regex Engine & Severity Floor
Shared rule evaluator running identical regex configurations across on-device fallback and backend ingestion.
Pure-Python, zero-heavy-ML dependencies, strictly loaded from YAML configuration.
Provides exportable test vectors for cross-language validation (Kotlin on Android).
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

try:
    from .contracts import Category, Severity
except ImportError:
    from services.backend.src.ml.contracts import Category, Severity

logger = logging.getLogger("RegexEngine")


class RegexEngine:
    """
    Deterministic multilingual keyword and pattern scoring engine.
    Acts as the unbreakable severity floor on both origin device and backend dispatch.
    """
    def __init__(self, config_path: str | None = None):
        if config_path is None:
            default_local = Path(__file__).parent / "configs" / "regex_rules.yaml"
            default_ml = Path(__file__).resolve().parents[4] / "ml" / "configs" / "regex_rules.yaml"
            if default_local.exists():
                config_path = str(default_local)
            elif default_ml.exists():
                config_path = str(default_ml)
            else:
                config_path = str(default_local)

        self.config_path = Path(config_path)
        self.rules: list[dict[str, Any]] = []
        self.compiled_rules: list[tuple[dict[str, Any], re.Pattern]] = []
        self._load_rules()

    def _load_rules(self) -> None:
        """
        Loads keyword patterns and scoring rules strictly from the YAML configuration.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Regex configuration file not found at {self.config_path}")

        with open(self.config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            self.rules = data.get("rules", [])

        self.compiled_rules = []
        for r in self.rules:
            try:
                pattern = re.compile(r["pattern"], re.IGNORECASE | re.UNICODE)
                self.compiled_rules.append((r, pattern))
            except Exception as e:
                logger.warning(f"Failed to compile regex rule {r.get('id')}: {e}")

    def evaluate(self, text: str) -> dict[str, Any]:
        """
        Evaluates input text against all compiled regex patterns.
        Returns:
            - score (int 0-100)
            - severity (Severity: info | warn | critical)
            - category (Category: rescue | medical | fire | shelter | other)
            - category_hint (Category: alias for category)
            - matched_rules (list[str]: matched rule IDs)
        """
        if not text or not isinstance(text, str) or not text.strip():
            return {
                "score": 0,
                "severity": Severity.INFO,
                "category": Category.OTHER,
                "category_hint": Category.OTHER,
                "matched_rules": [],
            }

        matched: list[str] = []
        highest_score: int = 0
        selected_category: Category = Category.OTHER
        selected_severity: Severity = Severity.INFO

        for rule, pattern in self.compiled_rules:
            if pattern.search(text):
                rule_score = int(rule.get("score", 0))
                rule_id = rule.get("id", "unknown")
                rule_sev = Severity(rule.get("severity", "info"))
                rule_cat = Category(rule.get("category", "other"))

                matched.append(rule_id)
                if rule_score > highest_score:
                    highest_score = rule_score
                    selected_category = rule_cat
                    selected_severity = rule_sev

        # If no explicit rule matched, set default baseline
        if not matched:
            highest_score = 15
            selected_severity = Severity.INFO
            selected_category = Category.OTHER

        final_score = min(100, max(0, highest_score))

        return {
            "score": final_score,
            "severity": selected_severity,
            "category": selected_category,
            "category_hint": selected_category,
            "matched_rules": matched,
        }

    def score(self, text: str) -> dict[str, Any]:
        """Convenience alias for evaluate()."""
        return self.evaluate(text)


def produce_test_vectors(
    output_path: str = "ml/tokenizer/regex_test_vectors.json",
    config_path: str | None = None,
) -> list[dict[str, Any]]:
    """
    Generates a deterministic suite of multilingual test vectors covering English, Hindi,
    and Hinglish for all severity and category classes.
    Emits JSON file so Arnav can verify his Kotlin regex implementation on Android.
    """
    engine = RegexEngine(config_path=config_path)

    sample_inputs = [
        # --- English Critical ---
        "Roof collapsed in flood 4 people trapped under concrete rubble!",
        "Active building fire on 3rd floor cylinder blast spreading fast!",
        "Severe bleeding from head injury victim unconscious need doctor!",
        "Drowning in flood waters need boat urgently near pillar 14!",
        "Elderly trapped in basement water rising fast!",

        # --- English Warn ---
        "Rising water entering ground floor need rescue evacuation",
        "No drinking water and food rations completely exhausted for 10 people",
        "Shelter needed with blankets power outage since yesterday",
        "Minor cut on arm need first aid bandage",
        "Blocked road due to fallen tree near bridge",

        # --- English Info ---
        "We are safe at community relief camp all okay",
        "Where is the nearest relief camp location update please?",

        # --- Hindi Critical ---
        "मकान की छत गिर गई है 4 लोग मलबे में दबे हैं तुरंत मदद भेजो!",
        "सिलेंडर ब्लास्ट हुआ है और भीषण आग लग गई है लोग फंसे हैं!",
        "सिर में गहरी चोट है और बहुत खून बह रहा है बेहोश हैं!",
        "बाढ़ के पानी में डूब रहे हैं नाव भेजो तुरंत!",
        "गर्भवती महिला प्रसव पीड़ा में है बाढ़ में फंसी है!",

        # --- Hindi Warn ---
        "पानी घर में आ रहा है जलभराव बढ़ रहा है",
        "पीने का पानी नहीं है और खाना खत्म हो गया है",
        "कंबल चाहिए और शेल्टर में जगह चाहिए बिजली नहीं है",
        "बुखार है और दवाई चाहिए पट्टी उपलब्ध कराएं",
        "रास्ता बंद है पेड़ गिर गया है",

        # --- Hindi Info ---
        "हम सब सुरक्षित हैं कैम्प पहुंच गए हैं सब ठीक है",
        "राहत कहाँ है और कैम्प की जानकारी दीजिए",

        # --- Hinglish Critical ---
        "Building gir gaya 3 log fase hue hain jaldi rescue team bhejo!",
        "Ghar me cylinder phat gaya aag lag gayi hai 4 log fase hain!",
        "Bohot khoon beh raha hai victim behosh ho gaya hai ambulance bhejo!",
        "Pani bohot badh gaya hum doob rahe hain jaldi boat bhejo please!",
        "Buzurg fase hain water level dangerous ho gaya hai!",

        # --- Hinglish Warn ---
        "Pani ghar me aaraha hai ground floor par water level rising",
        "Peene ka pani aur khana khatam ho gaya ration chahiye",
        "Shelter chahiye aur kambal chahiye light nahi hai 24h se",
        "Bukhar hai aur dawa chahiye first aid kit bhejo",
        "Deewar me crack aa gaya hai aur rasta band hai",

        # --- Hinglish Info ---
        "Hum log safe hain family surakshit hai sab theek",
        "Camp kahan hai update do relief team kab aayegi?",
    ]

    test_vectors = []
    for text in sample_inputs:
        result = engine.evaluate(text)
        test_vectors.append({
            "input_text": text,
            "expected_score": result["score"],
            "expected_severity": result["severity"].value,
            "expected_category": result["category"].value,
            "expected_matched_rules": result["matched_rules"],
        })

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "version": "1.1.0",
                "description": "Project Pukar Deterministic Regex Test Vectors for Android Kotlin Verification",
                "total_vectors": len(test_vectors),
                "vectors": test_vectors,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"[RegexEngine] Exported {len(test_vectors)} test vectors to {out_file}")
    return test_vectors


if __name__ == "__main__":
    produce_test_vectors()
