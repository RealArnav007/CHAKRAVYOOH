"""
Project Pukar - Groq Dataset Generator & Multilingual Synthesizer
Generates labeled training samples across English, Hindi, and Hinglish for the lightweight student model.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Seed samples for deterministic bootstrapping without API key
# Categories frozen to: rescue | medical | fire | shelter | other
SEED_DATASET = [
    # Critical - English
    {"text": "Building roof collapsed in floods, 4 family members trapped under debris!", "severity": "critical", "category": "rescue", "local_score": 95, "lang": "en"},
    {"text": "Severe arterial bleeding from deep laceration, need immediate tourniquet and ambulance", "severity": "critical", "category": "medical", "local_score": 92, "lang": "en"},
    {"text": "LPG gas cylinder exploded on 2nd floor, active fire spreading fast!", "severity": "critical", "category": "fire", "local_score": 96, "lang": "en"},
    {"text": "Water level reaching 2nd floor, grandmother and infant trapped inside house", "severity": "critical", "category": "rescue", "local_score": 94, "lang": "en"},
    
    # Critical - Hindi
    {"text": "मकान की छत गिर गई है, 3 लोग मलबे के नीचे दबे हुए हैं, तुरंत मदद भेजो!", "severity": "critical", "category": "rescue", "local_score": 96, "lang": "hi"},
    {"text": "सिलेंडर ब्लास्ट हुआ है और आग फैल रही है, लोग अंदर फंसे हैं", "severity": "critical", "category": "fire", "local_score": 95, "lang": "hi"},
    {"text": "गंभीर रूप से घायल हैं, बहुत खून बह रहा है और सांस लेने में दिक्कत है", "severity": "critical", "category": "medical", "local_score": 93, "lang": "hi"},
    
    # Critical - Hinglish
    {"text": "Pani bohot zyada badh gaya hai, hum 5 log chhat par fase hain, doobne ka khatra hai", "severity": "critical", "category": "rescue", "local_score": 93, "lang": "hinglish"},
    {"text": "Ghar ki deewar gir gayi, uncle dab gaye hain niche, jaldi rescue team bhejo please", "severity": "critical", "category": "rescue", "local_score": 95, "lang": "hinglish"},
    {"text": "Aag lag gayi hai pure godam me, cylinder phat gaya hai, bachao!", "severity": "critical", "category": "fire", "local_score": 94, "lang": "hinglish"},
    
    # Warn - English
    {"text": "Flood water entering the ground floor, power cut since 12 hours", "severity": "warn", "category": "rescue", "local_score": 60, "lang": "en"},
    {"text": "Drinking water exhausted, only dry snacks left for 6 people", "severity": "warn", "category": "shelter", "local_score": 52, "lang": "en"},
    {"text": "Elderly father running out of blood pressure and diabetes medicine", "severity": "warn", "category": "medical", "local_score": 58, "lang": "en"},
    {"text": "Large tree fell across main road, vehicles completely blocked", "severity": "warn", "category": "other", "local_score": 45, "lang": "en"},
    
    # Warn - Hindi
    {"text": "पानी घर के अंदर भर रहा है, कल सुबह तक बोट की जरूरत होगी", "severity": "warn", "category": "rescue", "local_score": 58, "lang": "hi"},
    {"text": "राशन और पीने का साफ पानी खत्म हो गया है, राहत सामग्री चाहिए", "severity": "warn", "category": "shelter", "local_score": 54, "lang": "hi"},
    {"text": "बुजुर्ग मरीज को इंसुलिन की जरूरत है, मेडिकल सहायता चाहिए", "severity": "warn", "category": "medical", "local_score": 56, "lang": "hi"},
    
    # Warn - Hinglish
    {"text": "Ghar ke samne pani 3 feet ho gaya hai, light nahi hai 24 ghante se", "severity": "warn", "category": "rescue", "local_score": 55, "lang": "hinglish"},
    {"text": "Peene ka pani khatam ho chuka hai, rationing kar rahe hain", "severity": "warn", "category": "shelter", "local_score": 50, "lang": "hinglish"},
    {"text": "Mummy ko tez bukhar hai aur dawa nahi hai yahan", "severity": "warn", "category": "medical", "local_score": 48, "lang": "hinglish"},
    
    # Info - English
    {"text": "We have evacuated safely to the municipal community hall", "severity": "info", "category": "other", "local_score": 15, "lang": "en"},
    {"text": "Water level is receding slowly in our sector, all family safe", "severity": "info", "category": "other", "local_score": 10, "lang": "en"},
    {"text": "Is relief camp offering phone charging near station?", "severity": "info", "category": "other", "local_score": 20, "lang": "en"},
    
    # Info - Hindi
    {"text": "हम सब सुरक्षित स्कूल के शेल्टर में पहुंच गए हैं", "severity": "info", "category": "other", "local_score": 12, "lang": "hi"},
    {"text": "यहां पानी उतर रहा है, कोई खतरा नहीं है", "severity": "info", "category": "other", "local_score": 10, "lang": "hi"},
    
    # Info - Hinglish
    {"text": "Hum log safe camp me pahunch gaye hain, sab theek hai", "severity": "info", "category": "other", "local_score": 12, "lang": "hinglish"},
    {"text": "Water level kam ho raha hai idhar, koi emergency nahi hai abhi", "severity": "info", "category": "other", "local_score": 10, "lang": "hinglish"},
]


def generate_dataset(output_path: str = "ml/datasets/crisis_train.jsonl") -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    records = list(SEED_DATASET)
    
    # Check if Groq API key is present for additional synthesis
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        print("[DataGen] Groq API key detected. Synthesizing additional multilingual pairs...")
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            prompt = (
                "Generate 20 diverse disaster SOS messages for India disaster relief in JSON format. "
                "Languages: Hindi (Devanagari), Hinglish (Romanized Hindi), English. "
                "Include severities ('critical', 'warn', 'info') and categories ('rescue', 'medical', 'fire', 'shelter', 'other'). "
                "Return JSON with key 'samples': list of objects with fields {text, severity, category, local_score, lang}"
            )
            response = client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            samples = data.get("samples", [])
            print(f"[DataGen] Successfully generated {len(samples)} synthetic samples from Groq.")
            records.extend(samples)
        except Exception as e:
            print(f"[DataGen] Groq augmentation skipped: {e}")

    # Write JSONL
    with open(path, "w", encoding="utf-8") as f:
        for item in records:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"[DataGen] Dataset saved to {path} ({len(records)} total records).")


if __name__ == "__main__":
    generate_dataset()
