"""
Project Pukar - Synthetic Emergency SOS Dataset Generator
Uses the Groq API (Llama-3.1) to generate realistic, noisy, multilingual crisis SOS messages
across the full 3D grid: Severity (3) x Category (5) x Language (en, hi, hinglish) = 45 cells.
Includes hard boundary examples, rate limiting, retry with exponential backoff, and token/cost logging.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from dotenv import load_dotenv

from services.backend.src.ml.contracts import Category, Language, Severity

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DataGen")


class SyntheticCrisisGenerator:
    def __init__(self, config_path: str = "ml/configs/data_gen.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

        gen_cfg = self.config.get("generation", {})
        self.model = os.getenv("GROQ_MODEL", gen_cfg.get("model", "llama-3.1-8b-instant"))
        self.samples_per_cell = int(gen_cfg.get("samples_per_cell", 4))
        self.temperature = float(gen_cfg.get("temperature", 0.85))
        self.max_retries = int(gen_cfg.get("max_retries", 4))
        self.backoff_factor = float(gen_cfg.get("backoff_factor", 1.8))
        self.delay_between_calls = float(gen_cfg.get("delay_between_calls_sec", 1.0))

        out_cfg = self.config.get("output", {})
        self.parquet_path = Path(out_cfg.get("parquet_path", "ml/datasets/processed/corpus_synth.parquet"))
        self.append_mode = bool(out_cfg.get("append_mode", False))

        pricing_cfg = self.config.get("pricing", {})
        self.cost_prompt_1m = float(pricing_cfg.get("cost_per_1m_prompt_tokens", 0.05))
        self.cost_comp_1m = float(pricing_cfg.get("cost_per_1m_completion_tokens", 0.08))

        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")

        # Metrics
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {}
        with open(self.config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _build_prompt(self, severity: Severity, category: Category, language: Language, n: int) -> tuple[str, str]:
        system_prompt = (
            "You are an expert synthetic dataset generator for Project Pukar (an offline emergency mesh SOS platform in India). "
            "You generate realistic, raw, authentic disaster text messages that real victims or witnesses send during life-or-death emergencies. "
            "You must return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "messages": [\n'
            '    {"text": "<raw text>", "is_boundary_case": <bool>}\n'
            "  ]\n"
            "}\n"
            "Strictly avoid robotic, generic, or AI-sounding boilerplate. Emulate real human typing under extreme panic."
        )

        lang_instruction = {
            Language.EN: "Language: English (authentic Indian English, short SMS style, typos, occasional abbreviations, direct statements).",
            Language.HI: "Language: Hindi in Devanagari script (हिंदी लिपि, व्याकरण की छोटी गलतियां, व्याकुलता, वास्तविक आपदा शब्दावली).",
            Language.HINGLISH: (
                "Language: Hinglish (Romanized / Latin script Hindi mixed with colloquial English, e.g. "
                "'pani chhat tak aa gaya hai, 3 log fase hue hain, jaldi boat bhejo please', 'wall gir gayi hai auntie dab gayi')."
            ),
        }[language]

        severity_instruction = {
            Severity.CRITICAL: "Severity: CRITICAL (Direct, immediate threat to life: trapped under debris, drowning, arterial bleeding, active fire, infants/elderly in mortal peril).",
            Severity.WARN: "Severity: WARN (Urgent distress without instant death: rising water entering house, food/drinking water exhausted, power outage >24h with sick person, road blocked).",
            Severity.INFO: "Severity: INFO (Informational / safe status: reached relief camp, safe on high ground, water level receding, logistics/camp inquiry).",
        }[severity]

        category_instruction = {
            Category.RESCUE: "Category: RESCUE (Entrapment, flood rescue, collapsed building, boat/rope needed, evacuation).",
            Category.MEDICAL: "Category: MEDICAL (Severe injury, fractures, head trauma, hemorrhage, insulin/oxygen exhaustion, burns).",
            Category.FIRE: "Category: FIRE (Structural fire, cylinder explosion, electrical short-circuit blaze, gas leak).",
            Category.SHELTER: "Category: SHELTER (Dry ration shortage, potable water exhausted, blankets, displaced family camp).",
            Category.OTHER: "Category: OTHER (Safe check-in, fallen trees on road, cracked bridge, general status update).",
        }[category]

        user_prompt = (
            f"Generate exactly {n} distinct, diverse emergency text messages with the following requirements:\n"
            f"1. {severity_instruction}\n"
            f"2. {category_instruction}\n"
            f"3. {lang_instruction}\n"
            f"4. Diversity Guidelines: Vary message length (8 to 35 words). Include realistic panic (e.g. exclamation marks, typos, abbreviations, local landmark names like 'pillar 14', 'drain', 'near Hanuman temple').\n"
            f"5. Boundary Cases: Ensure at least one message is a subtle boundary case (e.g. high-warn bordering on critical) to challenge classifier calibration.\n"
            f"Output must be valid JSON with key 'messages'."
        )

        return system_prompt, user_prompt

    def _call_groq_with_retry(self, system_prompt: str, user_prompt: str) -> list[str]:
        if not self.client:
            return []

        delay = self.delay_between_calls
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                    response_format={"type": "json_object"},
                    max_tokens=600,
                )

                # Track token usage
                if hasattr(response, "usage") and response.usage:
                    self.total_prompt_tokens += response.usage.prompt_tokens or 0
                    self.total_completion_tokens += response.usage.completion_tokens or 0

                content = response.choices[0].message.content
                data = json.loads(content)
                raw_msgs = data.get("messages", [])

                extracted = []
                for item in raw_msgs:
                    if isinstance(item, dict) and "text" in item:
                        txt = str(item["text"]).strip()
                        if len(txt) > 5:
                            extracted.append(txt)
                    elif isinstance(item, str) and len(item.strip()) > 5:
                        extracted.append(item.strip())

                if extracted:
                    return extracted

            except Exception as e:
                logger.warning(f"Groq API call attempt {attempt}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(delay)
                    delay *= self.backoff_factor

        return []

    def _generate_fallback_cell_samples(self, severity: Severity, category: Category, language: Language, n: int) -> list[str]:
        """
        High-quality seed synthesis fallback for offline test environments or when API key is unconfigured.
        """
        fallbacks = {
            (Severity.CRITICAL, Category.RESCUE, Language.EN): [
                "Roof collapsed in flash flood 4 people trapped under concrete debris hurry!",
                "Water reaching 2nd floor balcony grandmother and baby stuck inside send boat!",
                "Trapped inside basement parking flash flood rising rapidly cannot open door!",
                "Landslide hit our house 2 people buried under mud near main road!",
            ],
            (Severity.CRITICAL, Category.RESCUE, Language.HI): [
                "मकान की छत गिर गई है 4 लोग मलबे में दबे हैं तुरंत रेस्क्यू टीम भेजो!",
                "पानी दूसरी मंजिल तक आ गया है बुजुर्ग और बच्चा फंसे हैं नाव भेजो!",
                "तहखाने में पानी भर गया है दरवाजा नहीं खुल रहा हम 3 लोग फंसे हैं!",
                "पहाड़ खिसकने से घर दब गया है लोग नीचे फंसे हैं जल्दी मदद करो!",
            ],
            (Severity.CRITICAL, Category.RESCUE, Language.HINGLISH): [
                "Building gir gayi hai uncle aur 2 bachhe dab gaye hain niche jaldi aao!",
                "Pani bohot badh gaya hai chhat par 5 log phase hain doobne ka darr hai!",
                "Ghar ke andar 4 feet pani hai aur door jam ho gaya hai rescue team bhejo!",
                "Bridge ke pass road beh gayi humari car fass gayi hai madad chahiye!",
            ],
            (Severity.CRITICAL, Category.MEDICAL, Language.EN): [
                "Severe arterial bleeding from deep leg cut after wall fell need tourniquet!",
                "Elderly patient having acute chest pain and breathing failure need ambulance!",
                "Head injury from falling brick victim unconscious bleeding profusely!",
                "Pregnant woman in active severe labor during flood no medical staff!",
            ],
            (Severity.CRITICAL, Category.MEDICAL, Language.HI): [
                "दीवार गिरने से सिर में गहरी चोट लगी है बहुत खून बह रहा है बेहोश हैं!",
                "सीने में तेज दर्द है और सांस नहीं आ रही एम्बुलेंस तुरंत चाहिए!",
                "मरीज को ऑक्सीजन की सख्त जरूरत है सिलेंडर खत्म हो चुका है!",
                "गंभीर चोट है खून नहीं रुक रहा तुरंत डॉक्टर की मदद चाहिए!",
            ],
            (Severity.CRITICAL, Category.MEDICAL, Language.HINGLISH): [
                "Head injury hui hai bohot khoon beh raha hai victim behosh ho gaya!",
                "Chest pain ho raha hai aur saans nahi aa rahi oxygen khatam hai jaldi!",
                "Deewar girne se pair toot gaya hai severe bleeding ho rahi hai!",
                "Mummy ko heart attack jaise symptoms hain flood me ambulance nahi aa rahi!",
            ],
            (Severity.CRITICAL, Category.FIRE, Language.EN): [
                "LPG cylinder blast on 2nd floor active fire spreading to adjacent apartments!",
                "Commercial factory caught fire heavy toxic chemical fumes spreading fast!",
                "Transformer exploded near school building fire spreading towards staircase!",
                "Gas pipeline leakage caught massive fire 3 people trapped on terrace!",
            ],
            (Severity.CRITICAL, Category.FIRE, Language.HI): [
                "सिलेंडर ब्लास्ट हुआ है और मकान में भीषण आग लग गई है लोग फंसे हैं!",
                "दुकान में आग फैल रही है जहरीला धुआं भर गया है दमकल भेजो!",
                "ट्रांसफार्मर में धमाका हुआ है और आग फैल रही है तुरंत फायर ब्रिगेड भेजो!",
                "गैस रिसाव के बाद आग लग गई है 2 लोग कमरे के अंदर फंसे हैं!",
            ],
            (Severity.CRITICAL, Category.FIRE, Language.HINGLISH): [
                "Ghar me cylinder phat gaya hai aag fail rahi hai bachao!",
                "Transformer blast hua aur building me aag lag gayi 4 log fase hain!",
                "Godam me aag lag chuki hai smoke bohot zyada hai fire brigade bhejo!",
                "Gas leak ke baad blast hua hai balcony me log fase hue hain!",
            ],
            (Severity.WARN, Category.SHELTER, Language.EN): [
                "Drinking water exhausted for 15 people in community hall need tanker by evening",
                "Only dry biscuits left for 2 days need emergency food rations for children",
                "Ground floor flooded power cut since 24 hours need dry shelter",
                "Blankets and potable water urgently required at government school camp",
            ],
            (Severity.WARN, Category.SHELTER, Language.HI): [
                "पीने का साफ पानी और राशन खत्म हो गया है 20 लोगों के लिए मदद चाहिए",
                "2 दिन से बिजली नहीं है और बच्चों के लिए दूध और खाना नहीं है",
                "घर में पानी भर गया है शेल्टर में जगह चाहिए राहत सामग्री भेजो",
                "पीने का पानी नहीं है कृपया राहत कैम्प में पानी का टैंकर भेजिए",
            ],
            (Severity.WARN, Category.SHELTER, Language.HINGLISH): [
                "Peene ka pani aur ration bilkul khatam ho gaya hai 10 log hain",
                "Light nahi hai 2 din se aur khana khatam ho gaya shelter chahiye",
                "Ghar me pani aa raha hai ground floor par rationing kar rahe hain",
                "Bachhon ke liye dudh aur drinking water bhej do camp me",
            ],
            (Severity.INFO, Category.OTHER, Language.EN): [
                "We have safely evacuated to the community shelter at town hall all okay",
                "Flood waters receding slowly in sector 4 road starting to clear",
                "Is mobile charging facility available at the railway station camp?",
                "Family of 5 reached high ground safely no urgent medical needs",
            ],
            (Severity.INFO, Category.OTHER, Language.HI): [
                "हम सब सुरक्षित स्कूल के शेल्टर में पहुंच गए हैं सब ठीक है",
                "यहां पानी उतर रहा है रास्ता धीरे धीरे साफ हो रहा है",
                "क्या रेलवे स्टेशन कैम्प में भोजन की व्यवस्था है?",
                "हमारा परिवार सुरक्षित स्थान पर पहुंच चुका है कोई खतरा नहीं है",
            ],
            (Severity.INFO, Category.OTHER, Language.HINGLISH): [
                "Hum log safe shelter me pahunch gaye hain family safe hai",
                "Sector 12 me water level niche ja raha hai road khul rahi hai",
                "Station wale camp me charging point open hai kya update do",
                "Sab theek hai hum log safe high ground par hain koi dikkat nahi",
            ],
        }

        # Match exact key or generate procedural fallback
        key = (severity, category, language)
        if key in fallbacks:
            return fallbacks[key][:n]

        # Generic procedural fallback for any other cell
        if language == Language.HI:
            return [
                f"{category.value} के संबंध में {severity.value} स्थिति है, सूचना दर्ज करें (नमूना {i+1})।"
                for i in range(n)
            ]
        elif language == Language.HINGLISH:
            return [
                f"{category.value} situation update hai, severity is {severity.value}, please record this (sample {i+1})."
                for i in range(n)
            ]
        else:
            return [
                f"Emergency status report for {category.value} with {severity.value} priority level, message index {i+1}."
                for i in range(n)
            ]

    def generate_full_grid(self) -> pd.DataFrame:
        severities = [Severity(s) for s in self.config.get("grid", {}).get("severities", ["info", "warn", "critical"])]
        categories = [Category(c) for c in self.config.get("grid", {}).get("categories", ["rescue", "medical", "fire", "shelter", "other"])]
        languages = [Language(lang_id) for lang_id in self.config.get("grid", {}).get("languages", ["en", "hi", "hinglish"])]

        total_cells = len(severities) * len(categories) * len(languages)
        logger.info(f"Starting synthetic generation across {total_cells} grid cells (N={self.samples_per_cell} per cell)...")
        logger.info(f"Model: {self.model} | Groq Client Active: {bool(self.client)}")

        rows = []
        cell_idx = 0

        for sev in severities:
            for cat in categories:
                for lang in languages:
                    cell_idx += 1
                    cell_id = f"[{cell_idx}/{total_cells}] ({sev.value}, {cat.value}, {lang.value})"

                    messages = []
                    if self.client:
                        sys_p, usr_p = self._build_prompt(sev, cat, lang, self.samples_per_cell)
                        messages = self._call_groq_with_retry(sys_p, usr_p)
                        time.sleep(self.delay_between_calls)

                    if not messages:
                        logger.info(f"{cell_id} Using baseline synthesis generator.")
                        messages = self._generate_fallback_cell_samples(sev, cat, lang, self.samples_per_cell)
                    else:
                        logger.info(f"{cell_id} Generated {len(messages)} samples via Groq.")

                    for text in messages:
                        rows.append({
                            "text": text,
                            "severity": sev.value,
                            "category": cat.value,
                            "language": lang.value,
                            "source": "groq_gen",
                        })

        new_df = pd.DataFrame(rows)

        # Merge or overwrite
        self.parquet_path.parent.mkdir(parents=True, exist_ok=True)
        if self.append_mode and self.parquet_path.exists():
            try:
                existing_df = pd.read_parquet(self.parquet_path)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=["text"]).reset_index(drop=True)
            except Exception as e:
                logger.warning(f"Failed to read existing parquet at {self.parquet_path}: {e}")
                combined_df = new_df
        else:
            combined_df = new_df

        combined_df.to_parquet(self.parquet_path, index=False, engine="pyarrow")
        logger.info(f"Saved {len(combined_df):,} total synthetic samples to {self.parquet_path}")

        self._print_summary(combined_df)
        return combined_df

    def _print_summary(self, df: pd.DataFrame) -> None:
        # Calculate cost estimate
        est_cost_prompt = (self.total_prompt_tokens / 1_000_000.0) * self.cost_prompt_1m
        est_cost_comp = (self.total_completion_tokens / 1_000_000.0) * self.cost_comp_1m
        total_est_cost = est_cost_prompt + est_cost_comp

        print("\n" + "=" * 70)
        print(" PROJECT PUKAR — SYNTHETIC SOS CORPUS GENERATION REPORT")
        print("=" * 70)
        print(f"Total Synthetic Records : {len(df):,}")
        print(f"Target Parquet File     : {self.parquet_path}")
        print(f"Total Prompt Tokens     : {self.total_prompt_tokens:,}")
        print(f"Total Completion Tokens : {self.total_completion_tokens:,}")
        print(f"Estimated Groq Cost     : ${total_est_cost:.5f} USD")
        print("=" * 70)

        # 3D Grid Distribution Breakdown
        print("\n--- Grid Counts by (Severity x Category x Language) ---")
        grid_pivot = pd.pivot_table(
            df,
            index=["severity", "category"],
            columns="language",
            values="text",
            aggfunc="count",
            fill_value=0,
        )
        print(grid_pivot.to_string())

        print("\n--- Summary by Severity ---")
        print(df["severity"].value_counts().to_string())

        print("\n--- Summary by Category ---")
        print(df["category"].value_counts().to_string())

        print("\n--- Summary by Language ---")
        print(df["language"].value_counts().to_string())
        print("=" * 70 + "\n")


def generate(config_path: str = "ml/configs/data_gen.yaml") -> pd.DataFrame:
    generator = SyntheticCrisisGenerator(config_path=config_path)
    return generator.generate_full_grid()


if __name__ == "__main__":
    generate()
