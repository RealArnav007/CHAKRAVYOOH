# Project Pukar — Backend ML Ingestion Integration Guide (For Harshit)

**Target Engineer:** Harshit (Cloud Backend & Ingestion Lead)  
**Author:** Rishabh Rana (ML & Intelligence Lead)  
**Primary Seam:** [`services/backend/src/ml/scorer.py`](../../services/backend/src/ml/scorer.py) · [`services/backend/src/ml/contracts.py`](../../services/backend/src/ml/contracts.py)  
**Status:** Frozen Production Spec — Complete & Verified  

---

## 1. Executive Summary & Seam Architecture

When a mesh radio packet arrives at the Cloud Gateway, Harshit's ingestion pipeline:
1. Verifies the cryptographic signature over the packet header and encrypted body.
2. Decrypts the end-to-end encrypted distress text payload.
3. **Calls `score()`**, passing the verified packet dict/header and decrypted plaintext.

```
┌────────────────────────────────────────────────────────────────────────┐
│               HARSHIT'S DOMAIN (Cloud Ingestion Pipeline)              │
│                                                                        │
│ 1. Gateway Mesh Ingestion  ──> Packet arrived via LoRa / BLE Relay     │
│ 2. Signature Verification  ──> Validate Ed25519 origin digital signature│
│ 3. Payload Decryption      ──> AES-GCM Decrypt to Plaintext String     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ Invokes ML Seam:
                                    ▼ score(packet, decrypted_text, ...)
┌────────────────────────────────────────────────────────────────────────┐
│                 RISHABH'S DOMAIN (ML Intelligence Core)                │
│                                                                        │
│ 1. Origin Ingestion        ──> Ingest signed on-device ML telemetry    │
│ 2. Server-side Recompute   ──> Run RegexEngine on decrypted plaintext  │
│ 3. Semantic Triage         ──> Groq Teacher LLM (async, 2s timeout)   │
│ 4. Priority Fusion Engine  ──> Weighted multi-signal fusion (0-100)    │
│ 5. Safe Response Contract  ──> Immutable ScoreResult Pydantic model    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Public Seam Interface: `score()`

### Function Signature
```python
from services.backend.src.ml.scorer import score, score_async
from services.backend.src.ml.contracts import (
    ScoreResult, 
    Severity, 
    Category,
    SignedSOSHeader,
    DecryptedSOSPayload
)

# Synchronous convenience wrapper (runs event loop safely)
result: ScoreResult = score(
    packet: dict | SignedSOSHeader,
    decrypted_text: str | DecryptedSOSPayload,
    corroborating_reports_count: int = 0,
    hours_elapsed: float = 0.0,
    candidates: list[dict] | None = None,
    zone_timestamps: list[float] | None = None,
    time_budget_ms: float = 1500.0,
    correlation_id: str | None = None,
)

# Native async interface for FastAPI / async ingestion pipelines
result: ScoreResult = await score_async(
    packet=packet,
    decrypted_text=decrypted_text,
    candidates=candidates,
    zone_timestamps=zone_timestamps,
    time_budget_ms=1500.0,
    correlation_id=correlation_id,
)
```

### Parameter Documentation
| Parameter | Type | Required | Description |
| :--- | :---: | :---: | :--- |
| **`packet`** | `dict` or `SignedSOSHeader` | **Yes** | The verified packet header containing on-device telemetry (`severity`, `regex_score`, `local_model_score`, `confidence`, `category`, `language`, `timestamp`). |
| **`decrypted_text`** | `str` or `DecryptedSOSPayload` | **Yes** | The plaintext distress message string (e.g. `"Building collapse 3 people trapped under debris"`). |
| **`corroborating_reports_count`** | `int` | No (default `0`) | Number of other verified distress calls received within the same geospatial cluster. |
| **`hours_elapsed`** | `float` | No (default `0.0`) | Time in hours since message creation at origin (used for temporal decay / urgency escalation). |
| **`candidates`** | `list[dict]` | No (default `None`) | Nearby incident candidate vectors fetched from PostgreSQL `pgvector` (`[{"id": "...", "embedding": [...]}]`) for semantic deduplication. |
| **`zone_timestamps`** | `list[float]` | No (default `None`) | Recent SOS arrival epoch timestamps for the geographic zone, used by `trend.py` to compute `escalation_signal`. |
| **`time_budget_ms`** | `float` | No (default `1500.0`) | Hard execution deadline in milliseconds. Pipeline will return best partial deterministic triage if exceeded. |
| **`correlation_id`** | `str` | No (default `None`) | Unique trace correlation identifier for end-to-end telemetry and logs. |

---

## 3. Data Contracts & Pydantic Schemas

Import all models directly from `services.backend.src.ml.contracts`:

### Output Model: `ScoreResult` (Version 2.0.0)
```python
class ScoreResult(BaseModel):
    # Contract Versioning
    schema_version: str = "2.0.0"       # Semantic contract version (SemVer)
    
    # Baseline Core Triage (Immutable Seam)
    severity: Severity                  # Severity.INFO ("info") | Severity.WARN ("warn") | Severity.CRITICAL ("critical")
    priority: int                       # Calibrated dispatch priority integer: 0 to 100
    category: Category                  # Category.RESCUE | MEDICAL | FIRE | SHELTER | OTHER
    confidence: float                   # Unified triage confidence score: 0.0 to 1.0
    reasoning: dict                     # Fully transparent auditable reasoning payload
    
    # Dispatch Intelligence & Tactical Briefing (Arnav's Incident Screen)
    entities: Entities | None           # Extracted people_count, hazards, needs, landmarks, mobility, vulnerable
    briefing: Briefing | None           # Dispatcher headline (<=18 words), recommended_resources, synthesis confidence
    recommended_resources: list[str]    # Derived tactical units: ambulance, rescue_team, fire_truck, evacuation, medical_supplies
    
    # Incident Correlation & Dense Vectors (Harshit's pgvector Seam)
    correlation: CorrelationVerdict     # match_id, similarity (0-1), is_duplicate (bool), cluster_hint
    embedding: list[float] | None       # 384-dimensional dense semantic vector for PostgreSQL pgvector storage
    
    # Zone Escalation & False-Alarm Analysis
    escalation_signal: float            # Zone distress escalation multiplier: 0.0 to 1.0 (from trend.py)
    false_alarm_likelihood: float       # Content-based false-alarm / drill probability: 0.0 to 1.0
    false_alarm_reasons: list[str]      # Diagnostic triggers explaining false-alarm score
    
    # Operational Safety & Security Telemetry
    needs_human_review: bool            # Commander review badge trigger: true if confidence < 0.65 or severe conflict
    injection_suspected: bool           # Flag: prompt injection pattern detected and neutralized
    injection_reasons: list[str]        # Neutralized injection pattern categories
    correlation_id: str | None          # Trace correlation ID
```

### Full JSON Output Structure (Version 2.0.0)
```json
{
  "schema_version": "2.0.0",
  "severity": "critical",
  "priority": 88,
  "category": "rescue",
  "confidence": 0.89,
  "needs_human_review": false,
  "injection_suspected": false,
  "injection_reasons": [],
  "false_alarm_likelihood": 0.0,
  "false_alarm_reasons": [],
  "escalation_signal": 0.75,
  "correlation_id": "trace-8f92-a1b4",
  "briefing": {
    "headline": "Structural collapse, 3 trapped — deploy rescue team and ambulance immediately",
    "recommended_resources": ["rescue_team", "ambulance"],
    "confidence": 0.92
  },
  "recommended_resources": ["rescue_team", "ambulance"],
  "entities": {
    "people_count": 3,
    "injuries": ["trauma"],
    "hazards": ["structural_collapse"],
    "needs": ["rescue", "medical"],
    "landmarks": ["near market square"],
    "mobility": "trapped",
    "vulnerable": ["child"]
  },
  "correlation": {
    "match_id": "inc_delhi_041",
    "similarity": 0.8924,
    "is_duplicate": true,
    "cluster_hint": "North Delhi Flood Collapse"
  },
  "embedding": [0.0342, -0.0512, 0.0891, "/* 384 floats */"],
  "reasoning": {
    "regex_contribution": 18.0,
    "local_model_contribution": 17.0,
    "groq_contribution": 31.5,
    "corroboration_bonus": 8.0,
    "vulnerability_bonus": 10.0,
    "location_modifier": 0.0,
    "trend_modifier": 0.75,
    "time_decay_factor": 1.0,
    "origin_severity": "critical",
    "origin_regex_score": 90,
    "origin_local_model_score": 85,
    "origin_confidence": 0.88,
    "origin_category": "rescue",
    "server_regex_score": 90,
    "disagreement_detected": false,
    "groq": "active",
    "groq_rationale": "High-urgency flood rescue request with physical entrapment.",
    "explanation_bullets": [
      "High density of emergency/rescue keywords in message body",
      "On-device neural model evaluated high distress level (score: 85/100)",
      "Groq cloud triage engine confirmed critical operational urgency (level: 5/5)",
      "🔗 Corroborated by existing incident cluster (match: inc_delhi_041)"
    ],
    "factors": {
      "regex": 18.0,
      "local_model": 17.0,
      "groq": 31.5,
      "corroboration": 8.0,
      "vulnerability": 10.0
    }
  }
}
```

---

## 4. Key Guarantees & SLAs for Backend Engineering

### Guarantee 1: Confidence-Aware Fusion & Life-Safety Disagreement Policy
- **Dynamic Weighting**: Signal weights scale by source confidence dynamically rather than static constants ($W_i = w_{base, i} \times c_i$).
- **Safer-Side Bias**: When source scores conflict beyond $\Delta > 30$, priority is biased towards the SAFER (higher) severity tier (Life-Safety Policy: False negatives in search-and-rescue are fatal).
- **Abstention**: If aggregate confidence drops below `0.65`, `needs_human_review` is set to `true` (surfaced in UI badge).

### Guarantee 2: Content-Based False Alarm Detection (Never Auto-Suppresses)
- Complements envelope-level cryptographic signatures and mesh rate limiting.
- Analyzes message body for test/drill language ("test", "testing 123", "mock drill", "parikshan", "ignore this"), contradictory disclaimers, or empty/garbage payloads.
- **Safety Guarantee**: `score()` **NEVER auto-drops or auto-suppresses packets**. It emits `false_alarm_likelihood` (0.0 to 1.0) and `false_alarm_reasons` for the command center dispatcher to review.

### Guarantee 3: The Zero-Exception SLA (Never Raises)
`score()` is guaranteed to **never raise an unhandled exception into Harshit's pipeline**:
- Corrupted inputs, unexpected keys, or missing headers are automatically assigned safe fallbacks.
- If Groq cloud API experiences network timeouts, 5xx errors, or rate limits, `score()` transparently falls back to on-device + rule-based fusion in $< 5\text{ ms}$.
- Fallback status is recorded cleanly in `reasoning["groq"] = "unavailable — rules-only"`.

### Guarantee 4: Trusted-but-Reverified Origin Telemetry
The on-device ML outputs (`severity`, `regex_score`, `local_model_score`, `category`) were generated on the victim's phone and signed at origin. The backend treats them as high-integrity baseline signals, while immediately re-verifying them against:
- High-precision server-side regex keyword rules (`RegexEngine`).
- Deep semantic triage from Groq.
- **Disagreement Detection:** If the on-device `local_model_score` significantly diverges from the server regex score (delta $\ge 30$ points), `disagreement_detected` is flagged `true` with diagnostic explanations in `disagreement_reason`.

### Guarantee 5: Anti-Inflation Corroboration Guard
- When Harshit's clustering layer groups multiple packets from the same incident, pass `corroborating_reports_count=N`.
- Duplicate reports do **not** linearly inflate priority: `PriorityEngine` applies logarithmic scaling capped at a maximum of $+15.0$ points (`max_corroboration_bonus` in `priority.yaml`).

---

## 5. End-to-End Ingestion Calling Example

Here is how Harshit integrates `score()` in the ingestion handler:

```python
from services.backend.src.ml.scorer import score
from services.backend.src.ml.contracts import ScoreResult, Severity

def process_decrypted_packet(
    packet_header: dict, 
    decrypted_body: str, 
    nearby_candidate_incidents: list[dict] = None,
    zone_recent_timestamps: list[float] = None
):
    """
    Called by Harshit's pipeline after Ed25519 signature verification 
    and AES-GCM payload decryption succeed.
    """
    # 1. Invoke the ML Scoring Seam with candidates and zone timestamps
    score_result: ScoreResult = score(
        packet=packet_header,
        decrypted_text=decrypted_body,
        candidates=nearby_candidate_incidents,
        zone_timestamps=zone_recent_timestamps,
        time_budget_ms=1500.0,
    )

    # 2. Access baseline triage fields
    print(f"Assigned Severity: {score_result.severity}")      # 'critical', 'warn', 'info'
    print(f"Dispatch Priority: {score_result.priority}/100")   # e.g., 88
    print(f"Assigned Category: {score_result.category}")      # 'rescue', 'medical', etc.

    # 3. Check for deduplication / correlation with existing cluster
    if score_result.correlation and score_result.correlation.is_duplicate:
        print(f"Attaching to existing cluster: {score_result.correlation.match_id}")

    # 4. Save 384-dimensional dense vector directly into PostgreSQL pgvector
    if score_result.embedding:
        save_to_pgvector(incident_id=packet_header.get("packet_id"), vector=score_result.embedding)

    # 5. Check for telemetry disagreements or review badges
    if score_result.needs_human_review:
        mark_for_manual_dispatcher_review(score_result.correlation_id)

    # 6. Persist to Postgres / Dispatch Queue
    save_to_database(score_result.model_dump())
```

---

## 6. Integration Checklist for Harshit

- [ ] Import `score` and `ScoreResult` from `services.backend.src.ml`.
- [ ] Ensure `GROQ_API_KEY` is set in the backend `.env` (system gracefully falls back if unset).
- [ ] Pass `corroborating_reports_count` from spatial clustering engine.
- [ ] Feed `score_result.reasoning["why_critical_bullets"]` directly to the dispatcher incident view.
- [ ] Run backend unit tests: `pytest services/backend/tests/` to verify ingestion integration.

---

## 7. Semantic Incident Correlation & Deduplication (`correlate.py`)

Harshit's correlation pipeline queries PostgreSQL (`pgvector`) for nearby recent candidate incidents within a spatial/temporal bounding box, and calls `correlate()` to determine if the new report belongs to an existing incident cluster:

```python
from services.backend.src.ml.correlate import embed, correlate
from services.backend.src.ml.contracts import CorrelationVerdict

# 1. Compute 384-dimensional dense semantic vector for storage in pgvector
vector: list[float] = embed(decrypted_text)

# 2. Harshit queries spatial/temporal candidates from PostgreSQL:
candidates = [
    {"id": "inc-001", "embedding": existing_vector_1, "category": "rescue"},
    {"id": "inc-002", "embedding": existing_vector_2, "category": "medical"},
]

# 3. Call correlate() to obtain semantic verdict
verdict: CorrelationVerdict = correlate(new_embedding=vector, candidates=candidates)

if verdict.is_duplicate:
    # Attach report to existing incident match_id (e.g. "inc-001")
    # Increases incident corroborating report counter: 1 -> 3 -> 7
    attach_report_to_incident(incident_id=verdict.match_id, vector=vector)
else:
    # Create new incident record with pgvector column
    create_new_incident(vector=vector, category=score_result.category)
```

---

## 8. Real-Time Zone Escalation & Trend Analysis (`trend.py`)

Powers the **"Zone Ignites"** tactical demo beat and feeds zone severity multipliers in Harshit's zone aggregation engine:

- **Division of Ownership**:
  - Harshit owns zone state, geospatial boundaries, and database persistence.
  - Rishabh (`trend.py`) owns the pure sliding-window mathematics (arrival rate, acceleration, burst detection, and normalized escalation signal $0.0 \dots 1.0$).
- **Integration Call**:
  Harshit passes recent report timestamps per zone and multiplies base zone severity by `escalation_signal`:

```python
from services.backend.src.ml.trend import escalation
from services.backend.src.ml.contracts import EscalationResult, EscalationState

# Harshit retrieves recent report timestamps for a geographic rescue zone
zone_timestamps = [1700000100, 1700000150, 1700000180, 1700000210]

# Compute zone escalation dynamics
trend: EscalationResult = escalation(reports_in_zone=zone_timestamps)

print(trend.rate_per_min)       # e.g. 3.2 reports/min
print(trend.acceleration)       # e.g. +2.1 (positive indicates accelerating crisis)
print(trend.escalation_signal)  # 0.0 to 1.0 multiplier (e.g. 0.88 -> "zone ignites")
print(trend.state_hint)         # "quiet" | "steady" | "escalating" | "surging" | "ignited"

# Harshit applies escalation multiplier to zone severity & UI heatmaps:
zone_severity_score = base_zone_severity * (1.0 + trend.escalation_signal)
if trend.state_hint == EscalationState.IGNITED:
    trigger_commander_zone_surge_alert(zone_id="ZONE_DELHI_NORTH")
```

---

## 9. Performance Under Load: Concurrency, Caching & Time Budgets

Project Pukar backend ML runs asynchronously with sub-step concurrency, response caching, token/cost metering, and hard time budgets:

### 1. Async & Concurrent Scoring (`score_async`)
Run `score_async` directly within FastAPI / asyncio event loops for high-throughput concurrency:
```python
from services.backend.src.ml import score_async

# Runs regex, normalization, Groq triage, entity extraction concurrently
result: ScoreResult = await score_async(
    packet=packet_dict,
    decrypted_text=distress_text,
    time_budget_ms=1500.0, # Configurable per-report deadline (default 1500ms)
)
```

### 2. Response Cache Keyed by Text Hash
Duplicate/identical SOS texts (common in disaster scenarios) hit the in-memory SHA-256 text-hash cache in $<1\text{ms}$ with `result.reasoning["cache_hit"] = True`.
```python
from services.backend.src.ml import get_cache_stats, clear_response_cache

stats = get_cache_stats()
# {"size": 42, "hits": 189, "misses": 42, "hit_rate_pct": 81.82, "ttl_seconds": 300.0}
```

### 3. Central Groq Usage & Cost Meter
Real-time tracking of token consumption, estimated USD cost, and latency per operation:
```python
from services.backend.src.ml import get_usage_summary

summary = get_usage_summary()
# Returns:
# {
#   "total_calls": 250,
#   "successful_calls": 240,
#   "cached_calls": 10,
#   "token_usage": {"prompt_tokens": 36000, "completion_tokens": 12000, "total_tokens": 48000},
#   "cost_telemetry": {"total_estimated_cost_usd": 0.0384, "currency": "USD"},
#   "latency_telemetry_ms": {"avg_ms": 145.2, "min_ms": 42.1, "max_ms": 520.4},
#   "by_operation": {"triage": {...}, "extraction": {...}, "briefing": {...}}
# }
```

### 4. Global Per-Report Time Budget
If upstream latency or Groq API delays threaten the SLA, the pipeline aborts pending remote calls at the deadline (`per_report_time_budget_ms: 1500`) and returns the best partial deterministic result with `time_budget_exceeded: True` and documented `skipped_steps`.

---

## 10. Intelligence Observability & Admin Health Endpoint (`intelligence_health`)

Harshit can query and expose live intelligence layer health metrics over an admin endpoint (e.g. `GET /admin/health/ml`):

```python
from services.backend.src.ml import intelligence_health, get_recent_traces

# Callable returns simple JSON-serializable dictionary:
health_dict: dict = intelligence_health()
```

### JSON Response Schema:
```json
{
  "status": "healthy",
  "uptime_seconds": 3600.0,
  "total_reports_processed": 1420,
  "latency_telemetry_ms": {
    "p50_total_ms": 1.2,
    "p95_total_ms": 3.4,
    "avg_total_ms": 1.5,
    "stages": {
      "guard_ms": {"p50_ms": 0.1, "p95_ms": 0.3, "avg_ms": 0.15},
      "regex_ms": {"p50_ms": 0.2, "p95_ms": 0.4, "avg_ms": 0.22},
      "groq_ms": {"p50_ms": 0.0, "p95_ms": 0.0, "avg_ms": 0.0},
      "fusion_ms": {"p50_ms": 0.3, "p95_ms": 0.5, "avg_ms": 0.35},
      "briefing_ms": {"p50_ms": 0.1, "p95_ms": 0.2, "avg_ms": 0.12}
    }
  },
  "groq_health": {
    "availability_pct": 100.0,
    "total_calls": 250,
    "successful_calls": 250,
    "failed_calls": 0,
    "cached_calls": 12,
    "total_tokens": 48000,
    "total_cost_usd": 0.0384,
    "estimated_cost_per_hour_usd": 0.0384
  },
  "cache_health": {
    "hit_rate_pct": 82.5,
    "hits": 189,
    "misses": 40,
    "size": 40
  },
  "triage_metrics": {
    "abstention_rate_pct": 2.1,
    "injection_rate_pct": 0.2,
    "false_alarm_rate_pct": 1.4,
    "time_budget_exceeded_rate_pct": 0.0,
    "severity_distribution": {"critical": 412, "warn": 650, "info": 358},
    "category_distribution": {"rescue": 520, "medical": 310, "fire": 140, "shelter": 350, "other": 100}
  }
}
```

### Correlation ID & Structured Tracing
Every scored report generates a `correlation_id` (either provided by Harshit as `score(packet, text, correlation_id="...")` or auto-generated) and emits a structured trace containing per-stage latencies, Groq token/cost telemetry, and injection flags. All secrets (API keys, bearer tokens) are strictly redacted.



