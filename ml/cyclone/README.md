# 🌀 Chakravyuh — Cyclone Intelligence Engine (`ml/cyclone/`)

## Mission
The **Chakravyuh Cyclone Intelligence Engine** transforms multi-source satellite observations, atmospheric environmental fields, and historical track sequences into an authoritative, validated `CycloneIntelligence` JSON stream for every operational cycle or replay frame. For any observation point, it determines whether a cyclonic disturbance exists, identifies its life-cycle development stage, estimates maximum sustained winds and central pressure across standard meteorological scales (IMD primary, Saffir-Simpson mapped), forecasts a 72-hour future trajectory, and quantifies spatial uncertainty through calibrated cone radii.

---

## Two-Tier Architecture Overview

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

1. **Tier-0 (Deterministic Safety Net)**:
   - **Rule-based Identification & Stage Classification**: Thresholding on observed convective organization, wind speeds, and pressure trends.
   - **Baseline Intensity**: Direct mapping to basin-accurate IMD classifications.
   - **Persistence + CLIPER Trajectory**: Extrapolation of recent velocity vectors combined with climatological drift models to project 72-hour tracks.
   - **Parametric Error Cone**: Empirically calibrated error growth curve ensuring valid spatial uncertainty boundaries even under sparse sensor coverage.

2. **Tier-1 (Multi-Modal Deep Fusion Network)**:
   - **Satellite IR Backbone**: CNN feature extractor (EfficientNet-B0 / ResNet-18) operating on rotationally-augmented IR brightness temperature patches.
   - **Atmospheric Environmental MLP**: Embedding ERA5 / INCOIS environmental conditions (SST, 850–200 hPa vertical wind shear, 500 hPa relative humidity, vorticity, and ocean heat content).
   - **Track Dynamics GRU**: Temporal recurrent encoding over historical storm trajectory vectors.
   - **Multi-Head Decoder**: Joint estimation of detection probability, life-cycle stage (softmax), maximum sustained wind speed (Huber regression + classification), track displacement vectors, and heteroscedastic Gaussian uncertainty (log-variance) for learned cone geometry.

3. **Dynamic Per-Field Tier Selection (`run_cycle()`)**:
   - Evaluates input validity, head confidence, and predicted variance thresholds per field.
   - Transparently drops to Tier-0 safety fallback if confidence is insufficient, labeling the output payload with `tier: "tier1" | "tier0" | "mixed"`.

---

## Directory Layout

- `config/`: YAML-driven typed configuration for datasets, model architectures, training hyperparameters, and replay simulations.
- `schema/`: JSON schema and Pydantic models enforcing the frozen `CycloneIntelligence` contract.
- `fixtures/`: Golden reference payloads for regression and contract testing.
- `data/`: Sample data and git-ignored local datasets.
- `ingest/`: Parsers for IBTrACS, satellite imagery (INSAT-3D, HURSAT, Digital Typhoon), and atmospheric reanalysis.
- `preprocess/`: Data cleaning, temporal alignment, spatial colocalization, and meteorological scale converters.
- `features/`: Motion vector computation, environmental feature extraction, and fusion tensors.
- `datasets/`: Spatio-temporally blocked PyTorch dataset generators.
- `models/`: Implementations of Tier-0 baselines, Tier-1 neural branches, fusion trunk, and multi-heads.
- `train/`: Multi-task training pipelines with homoscedastic uncertainty weighting and cosine annealing.
- `eval/`: Metrics (great-circle error, wind MAE, ECE), reliability curves, and automated reporting.
- `fusion/`: Runtime orchestration engine executing `run_cycle()`.
- `replay/`: Historical storm playback controller with landfall presets.
- `export/`: Output formatting, JSONL streaming, and backend producer client.
- `serving/`: Production FastAPI endpoints and containerization files.
- `tests/`: End-to-end contract validation, schema compliance, and SOS integrity test suites.
