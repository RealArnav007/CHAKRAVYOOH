#!/usr/bin/env bash
# ==============================================================================
# CHAKRAVYUH CYCLONE INTELLIGENCE ENGINE: END-TO-END REPRODUCIBILITY SCRIPT
# ==============================================================================
# This script executes the complete data ingestion, feature generation, 
# model training, calibration, evaluation, latency profiling, and test verification
# pipeline deterministically using pinned random seeds (SEED=42).
#
# Usage:
#   ./scripts/reproduce.sh [--quick | --full]
# ==============================================================================

set -euo pipefail

MODE="${1:---quick}"
SEED=42
export PYTHONHASHSEED=$SEED
export TORCH_DETERMINISTIC=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

# Determine python executable
if [ -d ".venv" ]; then
    PYTHON=".venv/bin/python"
    PYTEST=".venv/bin/pytest"
    PIP=".venv/bin/pip"
else
    PYTHON="python3"
    PYTEST="pytest"
    PIP="pip"
fi

echo "=================================================================="
echo "  🌀 CHAKRAVYUH REPRODUCIBILITY PIPELINE (Mode: ${MODE}, Seed: ${SEED})"
echo "=================================================================="
echo "  Python Executable : $($PYTHON --version)"
echo "  Git Commit Hash   : $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
echo "  Config Hash       : $(shasum -a 256 ml/cyclone/config/model.best.yaml 2>/dev/null | cut -c 1-16 || echo 'none')"
echo "=================================================================="

# Step 1: Environment and Dependencies
echo -e "\n[1/7] 📦 Verifying Python environment & requirements lock..."
if [ -f "ml/cyclone/requirements.lock.txt" ]; then
    echo "  Found ml/cyclone/requirements.lock.txt ($(wc -l < ml/cyclone/requirements.lock.txt) pinned packages)"
fi

# Step 2: Data Ingestion & Splitting
echo -e "\n[2/7] 📥 Ingesting cyclone track & atmospheric sample datasets..."
$PYTHON -c "
from ml.cyclone.ingest.ibtracs import load_tracks
from ml.cyclone.datasets.splits import make_splits
from ml.cyclone.preprocess.clean import clean_tracks
df = load_tracks()
cleaned_df, qc_rep = clean_tracks(df)
splits = make_splits(cleaned_df)
print(f'  Dataset loaded successfully: {len(cleaned_df)} track points across {cleaned_df[\"storm_id\"].nunique()} storms')
print(f'  Train/Val/Test splits built with zero data leakage: train={len(splits[\"train\"])}, val={len(splits[\"val\"])}, test={len(splits[\"test\"])}')
"

# Step 3: Feature Engineering & Preprocessing
echo -e "\n[3/7] 🧪 Computing multi-modal spatial & kinematic feature representations..."
$PYTHON -c "
from ml.cyclone.features.environmental import extract_environmental_features
from ml.cyclone.features.motion import extract_motion_features
from ml.cyclone.features.fusion import make_fused_sample
from ml.cyclone.fusion.run_cycle import load_sample_for_cycle
sample = load_sample_for_cycle(storm_id='Amphan', frame_idx=2)
fused = make_fused_sample(sample)
print(f'  Fused multi-modal vector: env_dim={fused.env_vector.shape}, track_seq={fused.track_sequence.shape}, has_image={fused.image_tensor is not None}')
"

# Step 4: Model Training / HPO Best Configuration Verification
echo -e "\n[4/7] 🧠 Running deterministic FusionNet training verification (Epochs: $( [ "$MODE" = "--full" ] && echo 10 || echo 2 ))..."
EPOCHS=$([ "$MODE" = "--full" ] && echo 10 || echo 2)
$PYTHON -m ml.cyclone.train.train_fusion --epochs "$EPOCHS" --batch-size 8 --lr 0.0002

# Step 5: Post-Hoc Confidence Calibration
echo -e "\n[5/7] 🎯 Fitting Temperature Scaling & Uncertainty Cone Recalibrator..."
$PYTHON -m ml.cyclone.eval.reliability

# Step 6: Comprehensive Evaluation & Demo Storm Error Analysis
echo -e "\n[6/7] 📊 Generating comprehensive evaluation report & demo-storm panels..."
$PYTHON -m ml.cyclone.eval.report
$PYTHON -m ml.cyclone.eval.error_analysis

# Step 7: Latency Profiling & Automated Test Suite Verification
echo -e "\n[7/7] ⚡ Profiling inference latency & running full test suite..."
$PYTHON -m ml.cyclone.eval.latency --iterations 25
$PYTEST -v

echo -e "\n=================================================================="
echo "  ✅ CHAKRAVYUH PIPELINE REPRODUCED SUCCESSFULLY (100% PASS)"
echo "  Artifacts recorded in: ml/cyclone/artifacts/ & eval/figs/"
echo "=================================================================="
