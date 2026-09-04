"""
Project Pukar - Test Vectors & Model Card Generator
Produces deterministic sample input/output vectors for Android [Arnav] integration verification.
"""

import json
from pathlib import Path

from services.backend.src.ml.regex_engine import RegexEngine


def generate_test_vectors(output_path: str = "ml/eval/test_vectors.json") -> None:
    regex_engine = RegexEngine()
    
    samples = [
        {
            "id": "vector_01_trapped_debris",
            "text": "Roof collapsed in flood, 4 people trapped under debris!",
            "language": "English",
        },
        {
            "id": "vector_02_hindi_cylinder_blast",
            "text": "सिलेंडर ब्लास्ट हुआ है और आग फैल रही है, तुरंत मदद भेजो",
            "language": "Hindi",
        },
        {
            "id": "vector_03_hinglish_flood_rescue",
            "text": "Pani chhat tak aa gaya hai, hum 4 log fase hain bachao",
            "language": "Hinglish",
        },
        {
            "id": "vector_04_warn_food_water",
            "text": "Drinking water exhausted and rationing food for 2 days",
            "language": "English",
        },
        {
            "id": "vector_05_info_safe_checkin",
            "text": "Hum log safe school camp me pahunch gaye hain",
            "language": "Hinglish",
        }
    ]

    results = []
    for s in samples:
        reg_res = regex_engine.evaluate(s["text"])
        results.append({
            "vector_id": s["id"],
            "input_text": s["text"],
            "language": s["language"],
            "expected_regex_score": reg_res["score"],
            "expected_severity": reg_res["severity"].value,
            "expected_category": reg_res["category"].value,
            "matched_rules": reg_res["matched_rules"],
        })

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"version": "1.0.0", "test_vectors": results}, f, indent=2, ensure_ascii=False)

    print(f"[Eval] Test vectors generated at {out_file} ({len(results)} vectors).")


if __name__ == "__main__":
    generate_test_vectors()
