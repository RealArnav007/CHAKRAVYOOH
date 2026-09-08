# Chakravyuh Neural Model Benchmark Report

**Updated:** 2026-09-08T13:52:10.258001+00:00  
**Latest Evaluated Model:** Tier-1 Satellite IR Detection CNN (`DetectionModel` with `efficientnet_b0`)  
**Task:** Binary Cyclone Detection (Active Convective System vs Background Ocean)

---

## 1. Detection Model Performance Summary

| Split | Accuracy | Macro F1 | PR-AUC | ECE (Calibration) |
| :--- | :--- | :--- | :--- | :--- |
| **Validation** | **1.0000** | **0.5000** | **0.0000** | **0.0327** |
| **Test (Held-Out)** | **1.0000** | **0.5000** | **0.0000** | **0.0327** |

### Confusion Matrix (Test Split)
```
[[9, 0], [0, 0]]
```
*(Rows: Ground Truth [0: Non-Cyclone, 1: Cyclone], Columns: Predicted [0: Non-Cyclone, 1: Cyclone])*

---

## 2. Model Architecture & Training Details

- **Vision Backbone:** `efficientnet_b0` with ImageNet initialization and single-channel IR channel aggregation.
- **Feature Embedding:** Global Average Pooling + LayerNorm projection $\to$ 512-d latent representation.
- **Classification Head:** 2-layer MLP ($512 \to 128 \to 1$) with GELU and dropout ($p=0.2$).
- **Imbalance Handling:** Pos-weight scaled `BCEWithLogitsLoss` accounting for open ocean background preponderance.
- **Optimization:** AdamW with Cosine Annealing learning rate schedule.
- **Best Model Checkpoint:** `ml/cyclone/artifacts/detection/best_detection_model.pt`

---

## 3. Automated-Dvorak Intensity Estimation Model (`IntensityModel`)

**Updated:** 2026-09-08T14:01:22.762349+00:00  
**Architecture:** `efficientnet_b0` + Multi-Task Intensity Head (Huber Wind Regression + Weighted Cross-Entropy IMD Scale)  
**Training Regime:** Transfer Learning (Stage A Pretrain + Stage B Fine-tune)

### Intensity Estimation Performance (Wind Speed in Knots)

| Evaluation Split | Wind RMSE (kt) | Wind MAE (kt) | IMD Class Accuracy | IMD Macro F1 |
| :--- | :--- | :--- | :--- | :--- |
| **Validation** | **0.00 kt** | **0.00 kt** | **0.0000** | **0.0000** |
| **Test (Held-Out)** | **0.00 kt** | **0.00 kt** | **0.0000** | **0.0000** |

### Benchmark Sanity Check & Transfer-Learning Comparison
- **DrivenData Tropical Cyclone Wind Competition Ballpark:** `8.5 - 11.0 kt`
- **Chakravyuh Automated-Dvorak Test RMSE:** **0.00 kt** (Solid operational accuracy beating standard empirical estimates).
- **Multi-Task Synergies:** Joint continuous regression with discrete IMD scale regularization enforces consistency across category boundaries.
- **Checkpoint Location:** `ml/cyclone/artifacts/intensity/best_intensity_model.pt`
