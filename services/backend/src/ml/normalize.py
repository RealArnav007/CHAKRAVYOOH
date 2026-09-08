"""
Project Pukar - Multilingual Text Normalization & Canonicalization Engine
========================================================================

Overview:
---------
Ensures downstream triage and reasoning engines (PriorityEngine, RegexEngine, GroqClient)
operate on clean, canonical text representations across English (EN), Hindi (HI), and
Code-Mixed Hinglish (HINGLISH).

Key Guarantees:
---------------
1. Verbatim Original Preservation:
   The original user text is ALWAYS preserved verbatim in `original`. User-facing dispatch
   views display the verbatim raw distress call.
2. Canonical English Working Copy:
   Internal reasoning uses `canonical_en` (translated/expanded colloquialisms, e.g.,
   "log fase hue hain" -> "people are trapped").
3. Deterministic-First Language Detection:
   Lightweight, sub-millisecond deterministic heuristics (Devanagari detection and Hinglish
   lexicons) classify language first, using Groq only as a secondary fallback.
4. Hash-Based LRU Caching:
   Responses are cached by SHA-256 text hash to avoid duplicate cloud translations.
5. Zero-Exception Graceful Degradation:
   If Groq is unreachable or times out, `canonical_en` smoothly falls back to `original`
   with language provided by the deterministic detector.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
from typing import Any

from .contracts import Language, NormalizedText
from .groq_client import GroqClient
from .guard import get_guard_system_instruction, sanitize, wrap_untrusted_data

logger = logging.getLogger("pukar.ml.normalize")

# ==========================================
# Deterministic Language Lexicons & Patterns
# ==========================================

# Devanagari Unicode Block: \u0900 to \u097F
DEVANAGARI_PATTERN = re.compile(r"[\u0900-\u097F]")

# Common Hinglish pronouns, verbs, auxiliaries, prepositions, and crisis markers
HINGLISH_KEYWORDS = frozenset({
    # Pronouns & Demonstratives
    "hum", "hume", "humein", "humare", "humari", "mera", "meri", "mere", "mujhe",
    "tera", "teri", "tere", "tujhe", "tum", "tumhe", "aap", "aapko", "unka", "unki",
    "unhe", "yeh", "ye", "woh", "wo", "yahan", "yaha", "wahan", "waha", "idhar", "udhar",
    "kisi", "kisiko", "sab", "sabko", "koi", "kuch", "apna", "apne", "apni",
    
    # Auxiliaries, Verbs & Tenses
    "hai", "hain", "hoon", "hun", "ho", "tha", "thi", "the", "raha", "rahi", "rahe",
    "gaya", "gayi", "gaye", "hua", "hui", "hue", "huye", "kar", "karo", "kare", "karna",
    "karein", "bhejo", "bhejiye", "bhej", "aao", "aaye", "aana", "jao", "jaaye", "jaana",
    "dekho", "suno", "bolo", "chahiye", "chahe", "padega", "sakta", "sakti", "sakte",
    "rakho", "lao", "diya", "diye", "de", "do", "liya", "liye", "le", "lo", "aagaya",
    "hogaya", "ruk", "ruko", "tuta", "toota", "toot", "gir", "gira", "giri", "dhas",
    
    # Prepositions, Conjunctions & Negations
    "aur", "ya", "lekin", "par", "pe", "me", "mein", "se", "ko", "ka", "ki", "ke",
    "nahi", "nahin", "mat", "bhi", "bina", "saath", "tak", "niche", "upar", "andar", "bahar",
    
    # Common Transliterated Crisis / Emergency Nouns
    "bachao", "madad", "madat", "sahayata", "fase", "fasa", "fasi", "phase", "phasa", "phasi",
    "phas", "pani", "paani", "doob", "dooba", "doobi", "chhat", "chath", "ghar", "makan",
    "log", "bachhe", "bacha", "bache", "buddhe", "bujurg", "aurat", "mahila", "aadmi",
    "dawa", "dawain", "dawaein", "ilaj", "dard", "khoon", "chot", "jaldi", "tez",
    "aag", "dhuan", "dhuaan", "band", "raste", "rasta", "sadak", "bheed", "khana", "rashan",
    "bijli", "current", "kripya", "krpya", "plz", "bahut", "bohot", "zyada", "jyada",
    "kam", "thoda",
})

# Hinglish multi-word n-gram patterns
HINGLISH_PHRASE_PATTERNS = [
    re.compile(r"\b(log|pani|hum|madad|bachao|fase|phase|chhat|chath)\s+(hai|hain|me|mein|par|pe|karo|bhejo|hue|huye)\b", re.IGNORECASE),
    re.compile(r"\b(madad\s+karo|bachao\s+hume|pani\s+bhar|chhat\s+par|aa\s+gaya|nahi\s+hai|fase\s+hue)\b", re.IGNORECASE),
    re.compile(r"\b(jaldi\s+aao|boat\s+bhejo|dawa\s+chahiye|ambulance\s+bhejo)\b", re.IGNORECASE),
]

# Common standard English function words for baseline contrast
ENGLISH_STOPWORDS = frozenset({
    "the", "is", "are", "was", "were", "and", "or", "in", "on", "at", "to", "for",
    "with", "of", "from", "by", "about", "we", "they", "our", "my", "your", "he",
    "she", "it", "this", "that", "there", "here", "help", "need", "trapped", "flood",
    "water", "injured", "medical", "fire", "rescue", "emergency", "please", "urgent",
    "people", "building", "collapse", "children", "hospital", "doctor", "ambulance",
})

# ==========================================
# In-Memory Thread-Safe LRU Cache
# ==========================================

_MAX_CACHE_SIZE = 2048
_NORMALIZE_CACHE: dict[str, NormalizedText] = {}
_CACHE_LOCK = threading.Lock()


def get_text_hash(text: str) -> str:
    """Computes SHA-256 hash of normalized text for cache keys."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def clear_cache() -> None:
    """Clears the normalization in-memory cache (useful for tests)."""
    with _CACHE_LOCK:
        _NORMALIZE_CACHE.clear()


def get_cache_size() -> int:
    """Returns the current number of cached items."""
    with _CACHE_LOCK:
        return len(_NORMALIZE_CACHE)


# ==========================================
# Deterministic & Fallback Language Detector
# ==========================================

def detect_language(text: str, groq_client: GroqClient | None = None) -> Language:
    """
    Detects whether the crisis message is in English (EN), Hindi (HI), or Hinglish (HINGLISH).
    
    Execution Strategy:
    1. Deterministic Devanagari script detection -> HI.
    2. Deterministic Hinglish token & n-gram lexical analysis -> HINGLISH.
    3. English vocabulary & stopword heuristic -> EN.
    4. Fallback to Groq client if available and ambiguous, else default to EN.
    """
    if not text or not str(text).strip():
        return Language.EN

    raw = str(text).strip()

    # 1. Check for Devanagari characters (Hindi script)
    if DEVANAGARI_PATTERN.search(raw):
        return Language.HI

    # Extract clean ASCII lowercase words
    words = re.findall(r"\b[a-zA-Z]+\b", raw.lower())
    if not words:
        return Language.EN

    # 2. Check for Hinglish multi-word phrases
    for pattern in HINGLISH_PHRASE_PATTERNS:
        if pattern.search(raw):
            return Language.HINGLISH

    # 3. Check lexical overlap with Hinglish vocabulary
    hinglish_matches = sum(1 for w in words if w in HINGLISH_KEYWORDS)
    english_matches = sum(1 for w in words if w in ENGLISH_STOPWORDS)

    if hinglish_matches > 0 and hinglish_matches >= english_matches:
        return Language.HINGLISH
    
    if hinglish_matches >= 2:
        return Language.HINGLISH

    # If pure English stopwords dominate
    if english_matches > 0 and hinglish_matches == 0:
        return Language.EN

    # 4. If ambiguous and single word / short token, check if it's in Hinglish keywords
    if len(words) <= 3 and hinglish_matches >= 1:
        return Language.HINGLISH

    # 5. Groq fallback for edge / ambiguous cases (if client provided & active)
    if groq_client and groq_client.is_available():
        try:
            return _detect_language_via_groq(raw, groq_client)
        except Exception as e:
            logger.debug(f"Groq language detection fallback skipped: {e}")

    return Language.EN


def _detect_language_via_groq(text: str, groq_client: GroqClient) -> Language:
    """Queries Groq with strict JSON output for language classification."""
    if not groq_client._client:
        return Language.EN

    guard_res = sanitize(text)
    system_prompt = (
        "You are a linguistic language detector for Project Pukar. "
        "Classify the disaster message into one of: 'en' (English), 'hi' (Hindi in Devanagari), "
        "or 'hinglish' (Hindi transliterated into Latin script / Code-mixed). "
        "Return strictly valid JSON: {\"language\": \"en\" | \"hi\" | \"hinglish\"}\n\n"
        f"{get_guard_system_instruction()}"
    )

    response = groq_client._client.chat.completions.create(
        model=groq_client.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"MESSAGE DATA:\n{wrap_untrusted_data(guard_res.sanitized_text)}"},
        ],
        temperature=0.0,
        max_tokens=60,
        response_format={"type": "json_object"},
        timeout=1.5,
    )
    raw_content = response.choices[0].message.content or "{}"
    data = json.loads(raw_content)
    lang_str = str(data.get("language", "en")).strip().lower()
    
    if lang_str == "hi":
        return Language.HI
    if lang_str == "hinglish":
        return Language.HINGLISH
    return Language.EN


# ==========================================
# Core Normalization & Canonicalization
# ==========================================

def _translate_to_canonical_en(
    text: str,
    language: Language,
    groq_client: GroqClient,
    timeout: float = 2.0,
) -> tuple[str, Language]:
    """
    Translates/expands Hindi or Hinglish message into canonical English via Groq.
    Returns (canonical_en, refined_language).
    """
    if not groq_client._client:
        return text, language

    guard_res = sanitize(text)
    system_prompt = (
        "You are a disaster message translator and canonicalizer for Project Pukar (Crisis SOS Platform).\n"
        "Translate the input Hindi or Hinglish emergency message into clear, concise, standard English.\n"
        "Expand colloquial Hinglish terms into precise operational meaning "
        "(e.g. 'log fase hue hain' -> 'people are trapped', "
        "'paani chhat tak aa gaya' -> 'floodwater has reached the roof', "
        "'bache behosh hain' -> 'children are unconscious').\n"
        "Respond with strictly valid JSON:\n"
        "{\n"
        '  "canonical_en": "<clear standard English translation>",\n'
        '  "language": "hi" | "hinglish" | "en"\n'
        "}\n\n"
        f"{get_guard_system_instruction()}"
    )

    response = groq_client._client.chat.completions.create(
        model=groq_client.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"EMERGENCY TEXT DATA:\n{wrap_untrusted_data(guard_res.sanitized_text)}"},
        ],
        temperature=0.0,
        max_tokens=150,
        response_format={"type": "json_object"},
        timeout=timeout,
    )

    raw_content = response.choices[0].message.content or "{}"
    data = json.loads(raw_content)

    canonical_en = str(data.get("canonical_en", "")).strip()
    if not canonical_en:
        canonical_en = text

    lang_str = str(data.get("language", language.value)).strip().lower()
    refined_lang = language
    if lang_str in ("en", "hi", "hinglish"):
        refined_lang = Language(lang_str)

    return canonical_en, refined_lang


def normalize(
    text: str,
    groq_client: GroqClient | None = None,
    timeout: float = 2.0,
) -> NormalizedText:
    """
    Produces a canonical English working copy of the message while preserving
    the verbatim original text.
    
    Args:
        text: Raw distress message string.
        groq_client: Optional GroqClient instance for LLM translation.
        timeout: Timeout in seconds for LLM call (default 2.0s).

    Returns:
        NormalizedText containing:
        - original: Verbatim untouched input string.
        - canonical_en: Standard English working copy (expanded/translated).
        - language: Detected Language enum (EN, HI, HINGLISH).
    """
    verbatim_original = str(text) if text is not None else ""
    clean_text = verbatim_original.strip()

    if not clean_text:
        return NormalizedText(
            original=verbatim_original,
            canonical_en="",
            language=Language.EN,
        )

    # 1. Check in-memory hash cache
    text_key = get_text_hash(verbatim_original)
    with _CACHE_LOCK:
        if text_key in _NORMALIZE_CACHE:
            return _NORMALIZE_CACHE[text_key]

    # 2. Deterministic language detection
    detected_lang = detect_language(clean_text, groq_client=groq_client)

    # 3. Canonical English Resolution
    canonical_en = clean_text
    resolved_lang = detected_lang

    if detected_lang == Language.EN:
        # English text is already canonical
        canonical_en = clean_text
    else:
        # Hindi or Hinglish requires translation/expansion to canonical English
        if groq_client and groq_client.is_available():
            try:
                translated_en, refined_lang = _translate_to_canonical_en(
                    text=clean_text,
                    language=detected_lang,
                    groq_client=groq_client,
                    timeout=timeout,
                )
                canonical_en = translated_en
                resolved_lang = refined_lang
            except Exception as e:
                logger.warning(
                    "Groq translation failed/timed out (%s); falling back to original verbatim: %s",
                    e,
                    clean_text[:40],
                )
                canonical_en = clean_text
                resolved_lang = detected_lang
        else:
            # Graceful fallback: canonical_en = original
            canonical_en = clean_text
            resolved_lang = detected_lang

    result = NormalizedText(
        original=verbatim_original,
        canonical_en=canonical_en,
        language=resolved_lang,
    )

    # 4. Save to LRU cache
    with _CACHE_LOCK:
        if len(_NORMALIZE_CACHE) >= _MAX_CACHE_SIZE:
            # Evict oldest entry
            _NORMALIZE_CACHE.pop(next(iter(_NORMALIZE_CACHE)))
        _NORMALIZE_CACHE[text_key] = result

    return result


class TextNormalizer:
    """
    Stateful normalizer instance with custom Groq client and cache management.
    """

    def __init__(
        self,
        groq_client: GroqClient | None = None,
        timeout: float = 2.0,
    ):
        self.groq_client = groq_client or GroqClient()
        self.timeout = timeout

    def detect_language(self, text: str) -> Language:
        """Detects language for given text."""
        return detect_language(text, groq_client=self.groq_client)

    def normalize(self, text: str) -> NormalizedText:
        """Normalizes and canonicalizes given text."""
        return normalize(text, groq_client=self.groq_client, timeout=self.timeout)

    def clear_cache(self) -> None:
        """Clears cache."""
        clear_cache()
