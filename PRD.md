# 🌀 Chakravyuh — Cyclone Intelligence Engine
## ML / Intelligence Owner PRD (Rishabh)

**Project:** Project Beacon → *Chakravyuh* (AI Cyclone Intelligence + Pukar Resilience)
**Owner:** Rishabh Rana — Cyclone Brain (ML / Intelligence slice)
**Scope of this document:** The ML engine only. Backend (Harshit) and Frontend (Arnav) consume the frozen contract in §4; this PRD does not specify their work.
**Version:** 1.0 · 8 Sep 2026 · Hackathon execution spec
**Branch:** all work commits to `rishabh/ml`
**Status:** Authoritative engineering spec for the ML slice. Derived from the team master PRD and the Rishabh owner document, with the three strategic decisions below layered on top.

---

## 0. The three strategic decisions (read first, get sign-off)

| # | Decision | Why it matters |
|---|----------|----------------|
| **D1 — Two-tier engine** | Every prediction has a **Tier-0 deterministic fallback** (rules + persistence/CLIPER) *and* a **Tier-1 deep model**. `run_cycle()` uses Tier-1 when its confidence/inputs are valid, else transparently drops to Tier-0. | The demo can never emit an invalid or empty object. Judges probing "what if the model fails?" get a real answer. This is the single biggest de-risking move. |
| **D2 — Intensity CNN is the showpiece, track is secondary** | The crown model is a **multi-modal fusion net** whose most reliable head is **intensity estimation from IR imagery** (automated Dvorak). Track prediction is real but framed as the harder, uncertainty-quantified stretch. | Intensity-from-imagery is the most tractable *impressive* win and directly proves "multi-source satellite data." Track forecasting done shallowly loses; done with honest calibrated uncertainty, it wins. |
| **D3 — Schema: stage ≠ intensity; IMD is primary scale** | `classification.stage` = life-cycle stage. `intensity` = IMD category (basin-correct). Saffir-Simpson mapped into `extra`. Numeric heading/kt/mb kept. **Freeze this with Harshit on Day 0.** | Your source docs contradict each other. Locking this before anyone codes prevents the worst hackathon failure: integration breaking on demo day. |

---

## 1. Mission & non-goals

**Mission:** Produce, for any timestamp of a cyclone (live or replay), a single validated `CycloneIntelligence` JSON object answering: *is there a cyclone, what stage, how intense, where is it going, and how sure are we?* — with quantified, calibrated uncertainty.

**You own:** multi-source ingestion, preprocessing/fusion, identification, classification (stage), intensity, trajectory + uncertainty, historical replay, the frozen output object, contract tests, model card. Keep the existing SOS text-scoring pipeline unbroken.

**You do NOT touch:** dashboard/map (Arnav), risk engine / zone engine / alerts / WebSockets / mesh (Harshit), Pukar SOS core, Android. Your responsibility ends at emitting the object.

**Independence rule:** the moment the schema (§4) is frozen with Harshit, you are unblocked. You produce objects; he ingests them. You never call his APIs except to POST the object (if you run a producer endpoint).

---

## 2. Existing assets — KEEP, do not regress

The current Pukar ML stack is **SOS-text intelligence** and stays. New cyclone work lives in a **new module** `ml/cyclone/`. Do not fold cyclone models into the SOS student network.

| Asset | Location | Action |
|-------|----------|--------|
| SOS severity model (Keras/TFLite) | `ml/model/` | KEEP — do not retrain here |
| Tokenizer + preprocessing | `ml/tokenizer/` | KEEP — SOS only |
| Teacher / Groq fusion for SOS | `ml/model/teacher.py` + backend scorer | KEEP |
| Datasets / rubric / eval | `ml/datasets/`, `ml/eval/` | KEEP |
| Backend seam `score(packet, text)` | `services/backend/src/ml/` | KEEP — SOS path only |

A contract test in `ml/cyclone/tests/` must assert the SOS path still imports and scores a sample packet, so you have a tripwire if the pivot ever touches it.

---

## 3. System architecture (the ML engine)

```
                        MULTI-SOURCE DATA
        ┌───────────────────┼───────────────────────┐
        ▼                   ▼                       ▼
  Satellite IR         Atmospheric (ERA5)     Historical track
  (INSAT-3D /          SST, shear, RH,        (IBTrACS / IMD:
   HURSAT /            vorticity, OHC          lat,lon,wind,pres,
   Digital Typhoon)                            stage sequence)
        │                   │                       │
        └───────────────────┼───────────────────────┘
                            ▼
                 PREPROCESS · NORMALIZE · TIME-ALIGN · COLOCALIZE
                            ▼
                     FUSED SAMPLE
        { image_tensor, env_vector, track_sequence, meta }
                            ▼
        ┌───────────────── CYCLONE BRAIN ─────────────────┐
        │                                                  │
        │   TIER-1 (deep, primary)   TIER-0 (fallback)     │
        │   ┌─────────────────────┐  ┌──────────────────┐  │
        │   │ Image branch (CNN)  │  │ Rule identify    │  │
        │   │ Env branch (MLP)    │  │ Threshold stage  │  │
        │   │ Track branch (GRU)  │  │ Observed intens. │  │
        │   │   → fusion trunk    │  │ Persistence +    │  │
        │   │   → multi-head      │  │  CLIPER track    │  │
        │   │  (detect/stage/     │  │ Parametric cone  │  │
        │   │   intensity/track/  │  └──────────────────┘  │
        │   │   uncertainty)      │                        │
        │   └─────────────────────┘   confidence gate ─────┘
        │                            selects tier per field │
        └──────────────────────────┬───────────────────────┘
                                   ▼
                         CALIBRATION LAYER
              (temperature scaling; variance recalibration)
                                   ▼
                    run_cycle() → CycloneIntelligence JSON
                                   ▼
                 REPLAY DRIVER  ·  PRODUCER (files + POST)
```

**Module layout** (`ml/cyclone/`):

```
ml/cyclone/
  README.md
  pyproject.toml / requirements.txt
  config/                     # YAML configs (data, model, train, replay)
  schema/
    cyclone_intelligence.schema.json
    models.py                 # Pydantic models mirroring the schema
  fixtures/                   # golden JSON: no_detect / early / landfall_imminent
  data/                       # small committed subset (git-lfs); full data ignored
  ingest/
    ibtracs.py  satellite.py  era5.py  registry.py
  preprocess/
    clean.py  normalize.py  align.py  colocalize.py  scales.py
  features/
    motion.py  environmental.py  fusion.py
  datasets/
    splits.py  torch_dataset.py
  models/
    baseline_identify.py  baseline_classify.py  baseline_intensity.py
    baseline_track.py     # persistence + CLIPER
    image_branch.py  env_branch.py  track_branch.py
    fusion_net.py         # the multi-modal crown model
    heads.py  uncertainty.py  calibration.py
  train/
    trainer.py  losses.py  augment.py  schedule.py  track_experiment.py
  eval/
    metrics.py  evaluate.py  reliability.py  report.py
  fusion/
    run_cycle.py          # orchestrates tier selection → object
  replay/
    replay.py             # CLI + HTTP, jump-to-landfall preset
  export/
    producer.py           # JSONL writer + POST + file-drop
  serving/
    Dockerfile  service.py # optional FastAPI producer endpoint
  tests/
    test_schema.py  test_replay.py  test_sos_unbroken.py  test_contract.py
  MODEL_CARD.md
```

---

## 4. FROZEN OUTPUT CONTRACT (lock Day 0 with Harshit)

This object is the **only** thing Harshit and Arnav depend on. No required field added after freeze without a `schema_version` bump. Optional additions go under `extra`.

```json
{
  "schema_version": "1.0",
  "cyclone_id": "CYC-2026-BAY-001",
  "name": "Replay-Amphan",
  "timestamp": "2026-09-08T10:00:00Z",
  "basin": "North Indian Ocean",

  "identification": { "detected": true, "confidence": 0.94 },

  "classification": {
    "stage": "MATURE_TROPICAL_CYCLONE",
    "confidence": 0.89
  },

  "intensity": {
    "level": "VERY_SEVERE_CYCLONIC_STORM",
    "scale": "IMD",
    "max_wind_kt": 105,
    "min_pressure_mb": 960,
    "confidence": 0.82
  },

  "prediction": {
    "current_position": { "lat": 18.50, "lon": 84.20 },
    "heading_deg": 320,
    "speed_kt": 12,
    "forecast_hours": 72,
    "predicted_path": [
      { "t_plus_h": 0,  "lat": 18.50, "lon": 84.20 },
      { "t_plus_h": 6,  "lat": 18.83, "lon": 83.95 },
      { "t_plus_h": 12, "lat": 19.10, "lon": 83.70 },
      { "t_plus_h": 24, "lat": 19.80, "lon": 83.10 },
      { "t_plus_h": 48, "lat": 21.20, "lon": 81.90 },
      { "t_plus_h": 72, "lat": 22.40, "lon": 80.60 }
    ],
    "confidence": 0.78,
    "uncertainty": { "cone_radius_km": [0, 46, 78, 132, 205, 290] }
  },

  "sources": ["ibtracs_replay", "insat3d_ir", "era5"],
  "model_version": "chakravyuh-brain-0.1",
  "tier": "tier1",
  "extra": {
    "saffir_simpson": "Category 3",
    "intensity_class_probs": { "VSCS": 0.71, "ESCS": 0.18, "SCS": 0.11 }
  }
}
```

**Invariants (enforced by `schema/models.py` + `tests/test_schema.py`):**
- Timestamps ISO-8601 UTC.
- Lat/lon WGS84 decimal degrees, ≥2 dp.
- All confidences float in `[0,1]` — never percentages.
- `predicted_path` time-ordered; index 0 is current position.
- `cone_radius_km` is **parallel** to `predicted_path` (same length); index 0 = 0.
- If `identification.detected == false`, still emit the object with `prediction: null` (never drop the key).
- `cyclone_id` stable across all replay frames of one storm.
- `tier` ∈ {`tier1`, `tier0`, `mixed`} so the team can see which engine produced each object.

**Controlled vocabularies:**

`classification.stage` (life-cycle):
`NO_SIGNIFICANT_SYSTEM · DEVELOPING_DISTURBANCE · TROPICAL_DEPRESSION · MATURE_TROPICAL_CYCLONE · WEAKENING_SYSTEM · POST_TROPICAL_REMNANT`

`intensity.level` (IMD scale) with 3-min sustained wind thresholds (kt):

| Level (enum) | Wind (kt) |
|---|---|
| `DEPRESSION` | 17–27 |
| `DEEP_DEPRESSION` | 28–33 |
| `CYCLONIC_STORM` | 34–47 |
| `SEVERE_CYCLONIC_STORM` | 48–63 |
| `VERY_SEVERE_CYCLONIC_STORM` | 64–89 |
| `EXTREMELY_SEVERE_CYCLONIC_STORM` | 90–119 |
| `SUPER_CYCLONIC_STORM` | ≥120 |

Saffir-Simpson mapping lives in `preprocess/scales.py` and is emitted only in `extra.saffir_simpson`.

---

## 5. Data resources (concrete, downloadable)

Start the two large downloads (Digital Typhoon, DrivenData) on **Day 0** — they gate the impressive models.

### Backbone — labels & tracks
- **IBTrACS** (NOAA NCEI) — global best-track CSV; pull the **North Indian Ocean** subset. Columns you need: `SID, ISO_TIME, LAT, LON, USA_WIND/WMO_WIND, USA_PRES/WMO_PRES, STORM_SPEED, STORM_DIR, NATURE`. This is your label + track source. `ncei.noaa.gov/products/international-best-track-archive`.
- **IMD RSMC New Delhi** best track / Cyclone e-Atlas — Bay of Bengal & Arabian Sea authority; use to cross-validate IMD intensity labels. `rsmcnewdelhi.imd.gov.in`.

### Satellite imagery — the model's eyes
- **Digital Typhoon** (NII, Japan) — ⭐ the power dataset: 40+ yrs of 512×512 IR images with best-track metadata (grade, pressure, wind, position). Mostly Western North Pacific. **Strategy: pretrain the image branch here, fine-tune on North Indian Ocean.** `digital-typhoon.github.io`.
- **DrivenData "Wind-Dependent Variables: Predict Wind Speeds of Tropical Storms"** — ⭐ single-band satellite images labeled with wind speed; a clean intensity-regression benchmark with a public leaderboard to sanity-check against. Great second pretraining/fine-tune source.
- **HURSAT-B1** (NOAA NCEI) — pre-cropped IR patches centered on TCs, already aligned to best-track. Fastest labeled image dataset if you want to skip scraping. `ncei.noaa.gov/products/hurricane-satellite-data`.
- **MOSDAC (ISRO-SAC)** — INSAT-3D/3DR IR imagery + cyclone archive; **domestic data judges reward**. Registration required. Pull your demo storms here. `mosdac.gov.in`.

### Atmospheric / ocean context — the fusion story
- **ERA5** via Copernicus CDS (`cdsapi`) — SST, wind shear (850–200 hPa), RH (500 hPa), relative vorticity (850 hPa). 0.25°, hourly. `cds.climate.copernicus.eu`.
- **INCOIS** — Indian Ocean SST / Ocean Heat Content / TC Heat Potential; basin-specific, MoES-aligned. `incois.gov.in`.
- **CMEMS** (Copernicus Marine) — SST + OHC alternative. `marine.copernicus.eu`.

### Demo storms (pick 1 primary + 1 backup)
Recommended primary: **Amphan (2020)** or **Biparjoy (2023)** — well-documented, dramatic genesis→landfall arc, INSAT imagery available. Backup: **Fani (2019)** / **Tauktae (2021)** / **Remal (2024)**. Document *why* in `MODEL_CARD.md`.

> **Environment note:** these portals are not reachable from Claude's sandbox — all downloads run on *your* machine via the Antigravity prompts. IBTrACS/DrivenData are direct downloads; Digital Typhoon and MOSDAC need a (free) account; ERA5 needs a CDS API key.

---

## 6. Model strategy (the "industry-level" core)

### 6.1 Tier-0 — deterministic safety net (build first)
- **Identify:** track-based + convective thresholds → real confidence (never a constant 1.0). E.g. confidence = f(wind, organization proxy, persistence of detection).
- **Classify (stage):** rules on wind/pressure/Δ24h wind → life-cycle stage.
- **Intensity:** use observed wind/pressure in replay; map to IMD level via §4 table.
- **Track:** **persistence + CLIPER-style climatology** (linear extrapolation of recent motion, damped toward climatological drift). Emit 72 h polyline.
- **Cone:** parametric `r(t) = a + b·t` (documented constants from historical IMD track-error tables).

This tier alone satisfies the owner doc's P0 and guarantees a valid object every frame.

### 6.2 Tier-1 — multi-modal fusion net (the star)

**Branches**
- **Image branch:** EfficientNet-B0 (or ResNet-18) backbone, ImageNet-pretrained, first conv adapted for single-channel IR (or 3× channel repeat). Input 224×224 (or 256×256) IR patch centered on the storm. → 512-d embedding. *Rotation augmentation is critical — cyclones are quasi-rotationally-symmetric, so random rotation is a free, physically-valid augmentation and a big accuracy lever.*
- **Env branch:** MLP over ERA5 scalars (SST, shear, RH, vorticity, OHC) → 64-d.
- **Track branch:** GRU over last N=4–8 steps of `[lat, lon, wind, pres, u, v, Δt]` → 128-d.

**Fusion trunk:** concat `[512+64+128]` → 2-layer MLP with dropout → shared representation.

**Heads**
1. **Detection** — sigmoid → `identification.confidence`.
2. **Stage** — softmax over 6 life-cycle classes → `classification`.
3. **Intensity** — dual head: (a) regression → `max_wind_kt` (and pressure), (b) softmax over IMD classes → `extra.intensity_class_probs`; derive `intensity.level` from regressed wind via §4 table.
4. **Track** — decoder predicting Δposition at each horizon {6,12,24,48,72 h}.
5. **Uncertainty** — per-horizon **Gaussian log-variance** head → learned `cone_radius_km` (e.g. `1.96·σ` converted to km via great-circle). *This is the differentiator: a learned cone, not a formula.*

**Loss:** multi-task weighted sum with **learnable homoscedastic task weights (Kendall & Gal 2018)** — the model learns how much to trust each head. Detection = BCE; stage/intensity-class = cross-entropy; intensity-reg = Huber; track = great-circle (haversine) regression; uncertainty = Gaussian NLL.

**Training realism:** pretrain image branch on Digital Typhoon + DrivenData, then fine-tune the full net on the North Indian Ocean subset (small-data mitigation via transfer learning). Mixed precision, cosine LR schedule with warmup, early stopping on val track-error, checkpoint best.

### 6.3 Tier selection (in `run_cycle()`)
Per-field gate: use Tier-1 output when (inputs present) AND (head confidence ≥ threshold OR predicted variance ≤ ceiling); else fall back to Tier-0 for that field. Set the object's `tier` to `tier1` / `tier0` / `mixed` accordingly. Log which fields fell back.

### 6.4 Calibration (do not skip — judges probe confidence)
- Classification: **temperature scaling** on a held-out set so a stated 0.9 means ~90% correct.
- Track/uncertainty: check **empirical cone coverage** (does the 95% cone contain truth ~95% of the time?) and rescale variance if over/under-confident.
- Ship a **reliability diagram** in the eval report — few teams do this; it reads as genuine rigor.

---

## 7. Evaluation & benchmarking

**Splits:** temporally **and** spatially blocked — never let the same storm appear in train and test (leakage kills credibility). Hold out entire storms, and reserve the demo storms for qualitative eval only.

**Metrics** (`eval/metrics.py`):
- Track: mean great-circle error (km) at 12/24/48/72 h.
- Intensity: MAE / RMSE (kt) and pressure error (mb).
- Stage/detection: F1, confusion matrix, PR-AUC.
- Calibration: ECE (classification), cone coverage % (track).

**Beat-the-baseline proof:** Tier-1 must beat Tier-0 (persistence/CLIPER) on held-out track error and intensity RMSE. Report the delta. *If it doesn't beat the baseline on track, that's fine — say so, keep track on Tier-0, and let the intensity CNN carry the "AI" story.* Honesty here is a feature.

**Deliverable:** `eval/report.py` produces a one-file HTML/Markdown report: metric tables, reliability diagram, per-horizon error curve, confusion matrix, and side-by-side predicted-vs-actual track on the demo storm.

---

## 8. Historical replay (P0 — this drives the demo)

- Pick one demo storm; precompute a sequence of `CycloneIntelligence` objects at 3 h or 6 h steps, genesis → landfall.
- `replay(storm_id, start, speed)` yields the next frame on demand (CLI + optional HTTP).
- Every frame must **visibly evolve** position, intensity, path, cone, confidences.
- Provide a **`--jump landfall-24h`** preset so the demo skips genesis and lands on the dramatic window.
- Demo beats your frames must populate (not placeholder): Step 2 "Pattern Detected + confidence", Step 3 classification, Step 4 predicted path + cone.

---

## 9. Handoff seams

| Seam | Direction | Artifact | When |
|------|-----------|----------|------|
| Schema freeze | You ↔ Harshit | `cyclone_intelligence.schema.json` + Pydantic | **Day 0** |
| Fixtures | You → Harshit + Arnav | 3 golden JSON: no-detect / early / landfall-imminent | Day 0 / Day 1 AM |
| Replay sequence | You → Harshit | JSONL of one storm's frames | Day 1 |
| Producer | You → Harshit | POST each frame to `/api/v1/cyclone/intelligence` **or** file-drop he watches | Day 1–2 |
| Model card | You → team | `MODEL_CARD.md`: sources, limits, why confidence is trustworthy | Before demo |
| SOS `score()` | unchanged | Harshit keeps calling existing SOS scorer | Always |

You need from Harshit: endpoint URL + auth header (if any). You need from Arnav: nothing blocking (viz field requests go into `extra`).

---

## 10. Priorities

| Priority | Items | Impact if missing |
|----------|-------|-------------------|
| **P0** | Schema, Tier-0 identify/classify/intensity/track, 72 h path + cone, confidences, one-storm replay, fixtures, producer handoff, SOS tripwire | Demo story dies at step 2 |
| **P1** | Tier-1 fusion net, intensity CNN beating baseline, learned cone, calibration, second storm, transfer-learning pretraining | "AI" claim gets thin |
| **P2** | Live satellite feed, full data-fusion stack, automated landfall-error validation, SOS×cyclone correlation | Roadmap slide only |

---

## 11. Definition of done

- [ ] Valid `CycloneIntelligence` object for **every** replay frame; golden tests pass.
- [ ] Identification, stage, intensity, path, cone, confidences all populated for the demo storm.
- [ ] Tier-1 evaluated against Tier-0 with a written delta; calibration reported.
- [ ] Harshit ingests one full replay with **zero** manual JSON edits.
- [ ] Existing SOS ML path unbroken (`test_sos_unbroken.py` green).
- [ ] `MODEL_CARD.md` complete — no overclaiming.
- [ ] You can narrate in 60 s: *data in → identify → classify → intensity → predict → uncertainty → this JSON*.
- [ ] You built **no** UI, alerts, or mesh code.

---

## 12. Pitch language

**Use:** *"The Cyclone Brain fuses multi-source satellite, atmospheric, and historical data to identify a cyclone, classify its life-cycle stage, estimate intensity, and predict its trajectory with a learned, calibrated cone of uncertainty."*

**Never:** *"We added cyclone prediction to our SOS app."*

Closing line for the team demo: *"We didn't just predict the storm — we ensured the warning survived it."*
