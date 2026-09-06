# Project Pukar — Backend ML Triage Ingestion Seam

**Target Audience:** Harshit (Cloud Backend & Ingestion Lead)  
**Author:** Rishabh Rana (ML / Intelligence)  
**Status:** Frozen Production Interface  
**Primary Entrypoint:** [`services/backend/src/ml/scorer.py`](scorer.py) · [`services/backend/src/ml/contracts.py`](contracts.py)

---

## 1. Architectural Boundary & Ownership

```
┌─────────────────────────────────────────────────────────┐
│            HARSHIT'S DOMAIN (Ingestion Pipeline)        │
│                                                         │
│ 1. Ingest Raw Mesh Radio Packet from Relay Gateway      │
│ 2. Verify Cryptographic Signature (Ed25519 / ECDSA)     │
│ 3. Decrypt End-to-End Encrypted Distress Text (AES-GCM) │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼ Invokes ML Seam:
                             │ `score(packet: dict, decrypted_text: str) -> ScoreResult`
┌────────────────────────────┴────────────────────────────┐
│              RISHABH'S DOMAIN (ML Intelligence)         │
│                                                         │
│ 1. Parse & validate on-device header telemetry          │
│ 2. Re-verify text via deterministic RegexEngine         │
│ 3. Semantic triage via Groq Llama-3 (async/cached)      │
│ 4. Fuse signals in PriorityEngine using priority.yaml   │
│ 5. Return immutable, typed ScoreResult Pydantic model   │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Public Seam Interface: `score()`

Harshit's ingestion pipeline imports and calls `score()` after verifying signatures and decrypting the text.

### Function Signature
```python
from services.backend.src.ml.scorer import score
from services.backend.src.ml.contracts import ScoreResult, Severity, Category

result: ScoreResult = score(
    packet=packet_dict,
    decrypted_text=decrypted_string,
    corroborating_reports_count=0, # optional cluster density count
    hours_elapsed=0.0              # optional time since origin creation
)
```

---

## 3. Input & Output Contract Specifications

### Input Contract

1. **`packet` (`dict` or `SignedSOSHeader`)**:  
   The verified header payload. Common fields include:
   ```python
   {
       "packet_id": "pkt-8f3a-9921",
       "device_id": "dev-hash-8821",
       "timestamp": 1725439821000,
       "hop_count": 3,
       "severity": "critical",       # On-device assessed severity ('info' | 'warn' | 'critical')
       "regex_score": 90,            # On-device regex score (0-100)
       "local_model_score": 85,      # On-device TFLite model score (0-100)
       "confidence": 0.88,           # Model confidence (0.0 - 1.0)
       "category": "rescue",         # On-device emergency category
       "language": "hinglish"        # Detected language ('en' | 'hi' | 'hinglish')
   }
   ```
   *Note: If any fields are missing, the scorer assigns safe defaults automatically.*

2. **`decrypted_text` (`str` or `DecryptedSOSPayload`)**:  
   The decrypted plaintext message string (e.g. `"Ghar me 4 feet pani hai jaldi boat bhejo"`).

---

### Output Contract: `ScoreResult`

```python
class ScoreResult(BaseModel):
    severity: Severity       # Severity.INFO | Severity.WARN | Severity.CRITICAL
    priority: int            # Integer score from 0 to 100 (calibrated dispatch priority)
    category: Category       # Category.RESCUE | MEDICAL | FIRE | SHELTER | OTHER
    confidence: float        # Aggregated confidence score (0.0 to 1.0)
    reasoning: dict          # Multi-factor auditable transparency breakdown
```

#### Example Output Object
```json
{
  "severity": "critical",
  "priority": 88,
  "category": "rescue",
  "confidence": 0.89,
  "reasoning": {
    "regex_contribution": 18.0,
    "local_model_contribution": 17.0,
    "groq_contribution": 31.5,
    "corroboration_bonus": 8.0,
    "vulnerability_bonus": 10.0,
    "time_decay_factor": 1.0,
    "extracted_entities": ["flood", "boat", "entrapment"],
    "groq_rationale": "High-urgency flood rescue request with physical entrapment.",
    "matched_rules": ["crit_flood_level", "crit_rescue_boat"],
    "origin_severity": "critical",
    "origin_regex_score": 90,
    "origin_local_model_score": 85,
    "origin_confidence": 0.88,
    "origin_category": "rescue",
    "server_regex_score": 90,
    "disagreement_detected": false,
    "disagreement_reason": null
  }
}
```

---

## 4. Guarantees & Operational Principles

### 1. Trusted-but-Reverified & Origin Ingestion
The on-device ML assessment (`severity`, `regex_score`, `local_model_score`, `confidence`, `category`) was signed at origin. The backend **trusts** this assessment as a foundational signal, inlining them as features in `reasoning`, but immediately **re-verifies** it against:
- High-precision server-side deterministic regex rules (via `regex_engine.py` / `regex_rules.yaml`).
- Semantic triage and entity extraction.
- **Disagreement Detection:** If the origin `local_model_score` significantly diverges from the server-recomputed `regex_score` (e.g. delta $\ge 30$ points configurable in `priority.yaml`), `disagreement_detected` is set to `true` with explanatory diagnostic notes in `disagreement_reason` to flag possible degraded on-device execution.


### 2. Graceful Degradation SLA (Never Raises)
- **Zero Ingestion Disruption:** `score()` is wrapped with resilient exception safety nets.
- If the Groq Cloud API experiences rate limits, network timeouts, or 5xx outages, the system **degrades gracefully to rule-based + on-device fusion**.
- `score()` **will never raise an unhandled exception** into Harshit's ingestion pipeline.

### 3. Configurable Fusion Weights (`ml/configs/priority.yaml`)
Priority fusion weights ($w_{\text{severity}}, w_{\text{regex}}, w_{\text{local\_model}}, w_{\text{groq}}$), corroboration multipliers, and severity thresholds are loaded dynamically from [`ml/configs/priority.yaml`](../../../../ml/configs/priority.yaml). No magic numbers exist in code.

### 4. Per-Report Severity vs Incident Priority
- **Per-Report Severity (`info`, `warn`, `critical`):** The isolated, intrinsic classification of an individual distress packet.
- **Incident Priority (`0 - 100`):** The operational triage score driving dispatcher queues, incorporating multi-modal fusion, vulnerability flags, and incident layer modifiers.

### 5. Anti-Inflation Corroboration Guard
- Multiple duplicate reports from the same location do **NOT** linearly inflate priority.
- Harshit's correlation engine clusters packets, while [`PriorityEngine`](priority_engine.py) applies a strict saturation cap (`max_corroboration_bonus: 15.0`) to prevent duplicate report flooding from hijacking dispatcher queues.


---

## 5. Integration Verification Example

```python
from services.backend.src.ml.scorer import score
from services.backend.src.ml.contracts import Severity, Category

def test_ingestion_seam():
    packet = {
        "severity": "critical",
        "regex_score": 95,
        "local_model_score": 90,
        "category": "rescue",
    }
    text = "Trapped in basement during flash flood, oxygen low please help!"
    
    result = score(packet=packet, decrypted_text=text)
    
    assert isinstance(result.priority, int)
    assert 0 <= result.priority <= 100
    assert result.severity in [Severity.INFO, Severity.WARN, Severity.CRITICAL]
    assert result.category in [Category.RESCUE, Category.MEDICAL, Category.FIRE, Category.SHELTER, Category.OTHER]
```
