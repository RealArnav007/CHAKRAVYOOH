"""
Project Pukar - Incident Briefing & Tactical Resource Dispatch Engine
====================================================================

Overview:
---------
Synthesizes structured extracted entities, severity tier, and priority score into
a crisp, <=18 word actionable headline for dispatch commanders, alongside deterministic
tactical resource recommendations.

Key Guarantees:
---------------
1. Actionable Dispatcher Headline:
   - Strictly <= 18 words, imperative dispatcher tone.
   - Phrased via Groq LLM when available; seamlessly falls back to deterministic template
     when Groq is offline or times out.
2. Deterministic Tactical Resource Recommendation:
   - Grounded strictly in extracted entity needs and hazards (needs -> resources).
   - Resources: `ambulance`, `rescue_team`, `fire_truck`, `evacuation`, `medical_supplies`.
3. Anti-Hallucination Discipline:
   - Grounded strictly in extracted entities — never introduces unsupported facts.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .contracts import (
    Briefing,
    Entities,
    MobilityStatus,
    NeedCategory,
    ResourceCategory,
    Severity,
)
from .groq_client import GroqClient
from .guard import get_guard_system_instruction, sanitize, wrap_untrusted_data

logger = logging.getLogger("pukar.ml.briefing")

# ==========================================
# Deterministic Resource Derivation
# ==========================================

def derive_recommended_resources(
    entities: Entities,
    severity: Severity | str = Severity.WARN,
    priority: int = 50,
) -> list[ResourceCategory]:
    """
    Derives deterministic tactical emergency resources based on extracted needs,
    hazards, injuries, and victim demographics.
    """
    resources: list[ResourceCategory] = []
    sev_enum = Severity(severity) if isinstance(severity, str) else severity

    # 1. Medical Needs & Injuries -> Ambulance / Medical Supplies
    has_medical_need = (
        NeedCategory.MEDICAL in entities.needs
        or len(entities.injuries) > 0
        or any("medical" in str(h).lower() for h in entities.hazards)
    )
    if has_medical_need:
        if ResourceCategory.AMBULANCE not in resources:
            resources.append(ResourceCategory.AMBULANCE)

    # 2. Rescue & Entrapment -> Rescue Team
    has_rescue_need = (
        NeedCategory.RESCUE in entities.needs
        or entities.mobility == MobilityStatus.TRAPPED
        or any(h in entities.hazards for h in ("structural_collapse", "flood", "landslide"))
    )
    if has_rescue_need:
        if ResourceCategory.RESCUE_TEAM not in resources:
            resources.append(ResourceCategory.RESCUE_TEAM)

    # 3. Fire & Gas Hazards -> Fire Truck
    has_fire_need = (
        NeedCategory.FIRE in entities.needs
        or any(h in entities.hazards for h in ("fire", "gas_leak", "electrocution"))
    )
    if has_fire_need:
        if ResourceCategory.FIRE_TRUCK not in resources:
            resources.append(ResourceCategory.FIRE_TRUCK)

    # 4. Large Victim Count / Flood Stranded -> Evacuation Unit
    has_evacuation_need = (
        NeedCategory.EVACUATION in entities.needs
        or (entities.people_count is not None and entities.people_count >= 5)
        or ("flood" in entities.hazards and "roof" in entities.landmarks)
    )
    if has_evacuation_need:
        if ResourceCategory.EVACUATION not in resources:
            resources.append(ResourceCategory.EVACUATION)

    # 5. Shelter / First Aid Supplies -> Medical Supplies
    has_supply_need = (
        NeedCategory.SHELTER in entities.needs
        or len(entities.injuries) >= 2
        or "child" in entities.vulnerable
        or "elderly" in entities.vulnerable
    )
    if has_supply_need:
        if ResourceCategory.MEDICAL_SUPPLIES not in resources:
            resources.append(ResourceCategory.MEDICAL_SUPPLIES)

    # 6. Fallback defaults if no specific entities triggered
    if not resources:
        if sev_enum == Severity.CRITICAL or priority >= 75:
            resources = [ResourceCategory.RESCUE_TEAM, ResourceCategory.AMBULANCE]
        elif sev_enum == Severity.WARN or priority >= 40:
            resources = [ResourceCategory.RESCUE_TEAM]

    return resources


# ==========================================
# Deterministic Templated Headline Generator
# ==========================================

def generate_templated_headline(
    entities: Entities,
    severity: Severity | str = Severity.WARN,
    priority: int = 50,
    canonical_en: str = "",
) -> str:
    """
    Generates a deterministic dispatcher headline (strictly <= 18 words)
    grounded entirely in extracted entities and severity.
    """
    sev_enum = Severity(severity) if isinstance(severity, str) else severity
    parts: list[str] = []

    # 1. Primary Hazard / Incident Descriptor
    if "structural_collapse" in entities.hazards:
        parts.append("Structural collapse")
    elif "fire" in entities.hazards:
        parts.append("Active fire")
    elif "flood" in entities.hazards:
        parts.append("Flash flood")
    elif "gas_leak" in entities.hazards:
        parts.append("Gas leak hazard")
    elif NeedCategory.MEDICAL in entities.needs or len(entities.injuries) > 0:
        parts.append("Medical emergency")
    elif NeedCategory.RESCUE in entities.needs:
        parts.append("Rescue operation")
    else:
        parts.append("Crisis report")

    # 2. People, Entrapment & Vulnerability
    victim_parts = []
    if entities.people_count is not None:
        if entities.mobility == MobilityStatus.TRAPPED:
            if entities.vulnerable:
                victim_parts.append(f"{entities.people_count} trapped incl. {entities.vulnerable[0]}")
            else:
                victim_parts.append(f"{entities.people_count} trapped")
        else:
            if entities.vulnerable:
                victim_parts.append(f"{entities.people_count} people ({entities.vulnerable[0]})")
            else:
                victim_parts.append(f"{entities.people_count} people")
    elif entities.mobility == MobilityStatus.TRAPPED:
        if entities.vulnerable:
            victim_parts.append(f"trapped ({entities.vulnerable[0]})")
        else:
            victim_parts.append("people trapped")
    elif entities.vulnerable:
        victim_parts.append(f"{entities.vulnerable[0]} in distress")

    if victim_parts:
        parts.append(", ".join(victim_parts))

    # 3. Actions / Key Needs
    actions = []
    if NeedCategory.RESCUE in entities.needs:
        actions.append("rescue")
    if NeedCategory.MEDICAL in entities.needs or len(entities.injuries) > 0:
        actions.append("ambulance")
    if NeedCategory.FIRE in entities.needs or "fire" in entities.hazards:
        actions.append("fire truck")
    if NeedCategory.EVACUATION in entities.needs:
        actions.append("evacuation")

    if actions:
        action_str = " + ".join(actions[:2])
    else:
        action_str = "dispatch team"

    # 4. Priority indicator
    priority_str = "critical priority" if sev_enum == Severity.CRITICAL else (
        "high priority" if priority >= 60 else "standard priority"
    )

    full_headline = f"{', '.join(parts)} — {action_str}, {priority_str}"
    
    # Enforce strict <= 18 words constraint
    words = full_headline.split()
    if len(words) > 18:
        full_headline = " ".join(words[:18])

    return full_headline


# ==========================================
# Groq Headline Generator with Resilience
# ==========================================

def _phrase_headline_via_groq(
    entities: Entities,
    severity: Severity | str,
    priority: int,
    canonical_en: str,
    groq_client: GroqClient,
    timeout: float = 2.0,
) -> str:
    """Queries Groq to generate a crisp dispatcher headline <= 18 words."""
    if not groq_client._client:
        return ""

    guard_res = sanitize(canonical_en)

    system_prompt = (
        "You are the Incident Commander Dispatcher for Project Pukar (Emergency Mesh SOS Platform).\n"
        "Generate a crisp, imperative dispatcher briefing headline (STRICTLY MAXIMUM 18 WORDS).\n"
        "Tone: Professional emergency dispatch (e.g. 'Structural collapse, 3 trapped incl. a child — rescue + ambulance, high priority').\n"
        "CRITICAL RULE: Base the headline strictly on the provided extracted entities, severity, and priority. Do NOT hallucinate new facts.\n"
        "Respond with STRICT JSON: {\"headline\": \"<headline string <= 18 words>\"}\n\n"
        f"{get_guard_system_instruction()}"
    )

    entity_summary = (
        f"HAZARDS: {entities.hazards}, PEOPLE_COUNT: {entities.people_count}, "
        f"INJURIES: {entities.injuries}, NEEDS: {[n.value for n in entities.needs]}, "
        f"MOBILITY: {entities.mobility.value}, VULNERABLE: {entities.vulnerable}, "
        f"SEVERITY: {str(severity)}, PRIORITY: {priority}/100, "
        f"MESSAGE DATA:\n{wrap_untrusted_data(guard_res.sanitized_text)}"
    )

    response = groq_client._client.chat.completions.create(
        model=groq_client.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": entity_summary},
        ],
        temperature=0.0,
        max_tokens=80,
        response_format={"type": "json_object"},
        timeout=timeout,
    )

    raw_content = response.choices[0].message.content or "{}"
    data = json.loads(raw_content)
    headline = str(data.get("headline", "")).strip()

    # Enforce <= 18 words
    words = headline.split()
    if len(words) > 18:
        headline = " ".join(words[:18])

    return headline


# ==========================================
# Public Briefing API
# ==========================================

def brief(
    entities: Entities,
    severity: Severity | str = Severity.WARN,
    priority: int = 50,
    canonical_en: str = "",
    groq_client: GroqClient | None = None,
    timeout: float = 2.0,
) -> Briefing:
    """
    Synthesizes extracted entities and triage scores into an actionable dispatcher Briefing.

    Args:
        entities: Structured Entities model.
        severity: Assessed Severity tier (info, warn, critical).
        priority: Calibrated priority integer (0-100).
        canonical_en: Canonical English distress text.
        groq_client: Optional Groq client for phrasing headline.
        timeout: Timeout in seconds for LLM call.

    Returns:
        Validated Briefing Pydantic model with `headline` (<= 18 words),
        `recommended_resources`, and `confidence`.
    """
    # 1. Deterministic resource mapping (needs -> resources)
    recommended_resources = derive_recommended_resources(
        entities=entities,
        severity=severity,
        priority=priority,
    )

    # 2. Headline generation (Groq phrasing with deterministic fallback)
    headline = ""
    if groq_client and groq_client.is_available():
        try:
            headline = _phrase_headline_via_groq(
                entities=entities,
                severity=severity,
                priority=priority,
                canonical_en=canonical_en,
                groq_client=groq_client,
                timeout=timeout,
            )
        except Exception as e:
            logger.warning(f"Groq headline generation failed ({e}); falling back to template")
            headline = ""

    if not headline:
        headline = generate_templated_headline(
            entities=entities,
            severity=severity,
            priority=priority,
            canonical_en=canonical_en,
        )

    # Final sanity check: ensure headline is never empty and <= 18 words
    words = headline.split()
    if len(words) > 18:
        headline = " ".join(words[:18])
    if not headline:
        headline = f"Emergency incident — {str(severity).upper()} priority ({priority}/100)"

    return Briefing(
        headline=headline,
        recommended_resources=recommended_resources,
        confidence=0.92,
    )
