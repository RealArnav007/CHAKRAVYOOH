# Beacon v4 — Owner PRD: Rishabh (ML / Intelligence)

**Owner:** Rishabh Rana · **Domain:** ML / Intelligence · **Reads with:** `Beacon_v4_Master_PRD.md`
**One-line mission:** own **severity end-to-end** — from the offline on-device model to the cloud Priority Engine.

---

## 1. Where you fit

Beacon grades every SOS twice, and you own both graders. The encryption boundary forces a two-tier design: because the payload is end-to-end encrypted, nothing in the middle can read it — so scoring happens **on the origin phone (before encryption)** and **in the cloud (after decryption)**. There is no edge scoring.

```
ORIGIN PHONE (offline)                 BACKEND (online)
[R] Regex + TFLite  ──signed packet──▶ [H] decrypt ──▶ [R] Regex + Groq ──▶ [R] Priority Engine
   ↑ you train/export                                    ↑ you build            ↑ you build
   [A] runs your model                                 (fused, auditable)
```

You hand **[A]** a model + spec to run on-device. You expose a scoring function **[H]** calls after decrypt. You never touch transport, auth, or UI.

---

## 2. Your deliverables

**A. On-device (in `ml/` + shipped to `apps/android`):**
1. **Regex rule set** — configurable keyword/pattern → `regex_score` (0–100). Lives as shared config so [A] runs the identical rules on-device and you run them on backend.
2. **TFLite severity classifier** — compact (<10 MB) text model → `local_model_score` (0–100) + `severity` (info|warn|critical) + `category`.
3. **Preprocessing spec** — exact tokenization/normalization so [A]'s runtime produces identical inputs to your training.
4. **Model card + test vectors** — sample inputs → expected scores, so [A] can verify integration.

**B. Backend (in `services/backend/src/ml/`):**
5. **Backend regex engine** (same rules as on-device).
6. **Groq (Llama-3) integration** — prompt design + structured-output parsing.
7. **Severity scoring + Priority Engine** — the fusion formula (configurable, auditable).
8. **AI-transparency output** — the reasoning breakdown [A] renders on the incident screen.

---

## 3. On-device model spec  **[P0]**

- **Dataset** (`ml/datasets/`): disaster-message corpus (public crisis-text sets + synthetic augmentation). Label to your severity classes. Keep the labeling rubric in `ml/datasets/RUBRIC.md`.
- **Model:** small text classifier (e.g. distilled/embedding + classifier head or a lightweight CNN/TextVectorization) exported to TFLite. **Hard cap <10 MB and benchmark load+inference time on the real demo phone in Phase 0** — if it stalls the SOS flow, shrink it.
- **Output contract** (rides inside the **signed** immutable region — so it can't be tampered):
  ```
  severity: "info" | "warn" | "critical"
  regex_score: int 0..100
  local_model_score: int 0..100
  confidence: float 0..1
  category: enum (rescue|medical|fire|shelter|other)
  ```
- **Fallback:** if the model fails to load, regex alone must still produce a usable `severity`. Deterministic floor always available.

---

## 4. Backend intelligence spec  **[P0 core / P1 fusion]**

- **Regex engine** — identical rules to on-device; fast deterministic baseline.
- **Groq integration** — send decrypted text; get back structured `{severity, category, urgency, entities, rationale}`. **Groq never directly dispatches** — it's one input.
- **Priority Engine (fusion):**
  ```
  Final Priority = normalize(
      w1·severity + w2·regex + w3·local_model + w4·groq
      + corroboration + location_weight + time_weight + escalation_trend )
  ```
  Weights in config, not code. Every output **auditable** — emit the per-factor breakdown.
- **Severity vs priority discipline:** individual-report severity (this section) stays distinct from incident/zone priority (owned by [H]'s correlation, which *consumes* your per-report scores). This prevents "100 duplicate reports = severity 1000."

---

## 5. Interfaces / seams (freeze these)

| Seam | Direction | Contract |
| :-- | :-- | :-- |
| Severity fields | [R] → **protocol** | `severity`, `regex_score`, `local_model_score`, `confidence`, `category` in the **signed** region (§5.1 master). |
| On-device model | [R] → **[A]** | TFLite artifact + preprocessing spec + test vectors. [A] loads and runs; you own the numbers. |
| Backend scoring | [R] → **[H]** | Expose `score(packet, decrypted_payload) → {severity, priority, reasoning}`. [H]'s ingestion calls it after decrypt; you never touch decrypt/auth. |
| Reasoning | [R] → **[A]** | JSON breakdown (`{regex, groq, corroboration, location, trend}`) rendered on incident detail. |

---

## 6. Your phase slice

| Phase | You build | Tag |
| :-- | :-- | :-- |
| 0 | Dataset sourced + labeling rubric + model-size/latency benchmark on real phone | P0 gate |
| 7 | Train + export TFLite + regex rules + preprocessing spec + test vectors → hand to [A] | P0 |
| 9 | Backend regex + Groq + Severity + Priority Engine + `score()` interface for [H] | P0 |
| 9b | Priority fusion tuning + AI-transparency output | P1 |

---

## 7. Risks (yours)

- **Model too big/slow on demo phones** → <10 MB cap, benchmark in Phase 0, regex fallback.
- **Groq offline/latency during demo** → rule-based scoring must fully cover if Groq is unavailable (graceful degrade).
- **Score tampering** → your scores must sit inside the signed region; confirm with [A] that they're covered by `sig`.
- **On-device vs backend regex drift** → single shared rule file, not two copies.

## 8. Definition of done
On-device model exported <10 MB with passing test vectors and a regex fallback; [A] integration verified; backend `score()` live and called by [H]'s pipeline; Priority Engine produces normalized, auditable output with a per-factor reasoning breakdown that renders on the incident screen.

*IIC 3.0 · Beacon v4 · owner: Rishabh · ML/Intelligence*
