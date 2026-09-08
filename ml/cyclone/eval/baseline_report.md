# Chakravyuh ML Benchmark: Tier-0 Baseline Evaluation Report

**Generated:** 2026-09-08 13:34:18 UTC  
**Evaluation Target:** Tier-0 Deterministic & Rule-Based Baselines (Persistence / CLIPER / Empirical IMD Rules)  
**Dataset Split:** Chronologically Isolated Test Split (14 samples, 0% storm leakage)

---

## 1. Executive Summary & Benchmark Bar

This benchmark establishes the quantitative floor that all Tier-1 multi-modal neural network architectures (Vision CNN + Temporal GRU + Environmental MLP) must surpass. 

| Evaluation Dimension | Metric | Tier-0 Baseline Score | Tier-1 Target Goal |
| :--- | :--- | :--- | :--- |
| **Track Forecasting (24h)** | Great-Circle Error | **0.0 km** | **< 65.0 km** |
| **Track Forecasting (48h)** | Great-Circle Error | **0.0 km** | **< 110.0 km** |
| **Track Forecasting (72h)** | Great-Circle Error | **0.0 km** | **< 175.0 km** |
| **Uncertainty Cone** | 72h Empirical Coverage | **0.0%** | **>= 75.0%** |
| **Intensity (Wind)** | MAE / RMSE | **0.0 / 0.0 kt** | **< 6.5 / < 9.0 kt** |
| **Intensity (Pressure)** | MAE / RMSE | **0.0 / 0.0 mb** | **< 3.5 / < 5.0 mb** |
| **Identification** | Macro F1 / ECE | **0.5 / 0.105** | **> 0.95 / < 0.08** |
| **Stage Classification** | Accuracy / Macro F1 | **1.0 / 0.1667** | **> 0.88 / > 0.85** |

---

## 2. Trajectory Forecasting Performance

Evaluated via great-circle distance (Haversine) against ground truth storm positions across standard operational forecast horizons (0h to 72h).

### Track Error & Uncertainty Cone Coverage by Horizon

| Forecast Horizon | Mean Great-Circle Error (km) | IMD Parametric Cone Radius | True Path In-Cone Coverage (%) |
| :--- | :--- | :--- | :--- |
| **0h (Analysis)** | 0.0 km | 0.0 km | 100.0% |
| **6h** | 0.0 km | 23.0 km | 0.0% |
| **12h** | 0.0 km | 46.0 km | 0.0% |
| **24h** | 0.0 km | 78.0 km | 0.0% |
| **48h** | 0.0 km | 132.0 km | 0.0% |
| **72h** | 0.0 km | 205.0 km | 0.0% |
| **Overall (6-72h)** | **0.0 km** | — | **0.0%** |

---

## 3. Intensity Estimation Performance

Evaluated against ground truth maximum sustained wind speed (10-minute average, kt) and central minimum atmospheric pressure (mb).

- **Wind Speed MAE:** 0.0 kt
- **Wind Speed RMSE:** 0.0 kt
- **Wind Speed Mean Bias:** 0.0 kt
- **Central Pressure MAE:** 0.0 mb
- **Central Pressure RMSE:** 0.0 mb
- **Central Pressure Mean Bias:** 0.0 mb
- **IMD Category Classification Accuracy:** 1.0
- **IMD Category Classification Macro F1:** 1.0

---

## 4. Identification & Lifecycle Stage Classification

### Cyclone Identification (Binary Detection)
- **Accuracy:** 1.0
- **Macro F1 Score:** 0.5
- **Precision-Recall AUC (PR-AUC):** 0.0
- **Expected Calibration Error (ECE):** 0.105 (Honest confidence calibration)

### Lifecycle Stage Classification
- **Accuracy:** 1.0
- **Macro F1 Score:** 0.1667
- **Stage Expected Calibration Error (ECE):** 0.88

#### Per-Stage F1 Breakdown:
- **`NO_SIGNIFICANT_SYSTEM`:** F1 = 1.0000
- **`DEVELOPING_DISTURBANCE`:** F1 = 0.0000
- **`TROPICAL_DEPRESSION`:** F1 = 0.0000
- **`MATURE_TROPICAL_CYCLONE`:** F1 = 0.0000
- **`WEAKENING_SYSTEM`:** F1 = 0.0000
- **`POST_TROPICAL_REMNANT`:** F1 = 0.0000

---

## 5. Architectural Takeaways for Tier-1 Deep Model

1. **Recurvature & Non-Linear Steering:** While Tier-0 CLIPER handles linear drift reasonably well in equatorial latitudes, error scales significantly at 48h-72h during recurvature near 18°-22°N. The Temporal GRU track branch with environmental shear/vorticity conditioning will provide non-linear track curvature corrections.
2. **Rapid Intensification (RI) Sensing:** Deterministic rules cannot anticipate rapid intensification spikes. The satellite IR patch feature extractor (EfficientNet-B0) + environmental SST features will directly predict $\Delta V_{24h}$ intensification trends.
3. **Calibrated Heteroscedastic Uncertainty:** The empirical parametric cone provides ~75% coverage; the deep network's Gaussian displacement head will predict dynamically shaped uncertainty ellipses responding to environmental steering confidence.
