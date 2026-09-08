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
