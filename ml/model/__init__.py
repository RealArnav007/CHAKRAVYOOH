"""
Project Pukar - ML Model Package
"""

from ml.model.architecture import (
    ScaleLayer,
    build_crisis_classifier,
    build_model,
    estimate_model_size,
    load_model_config,
    print_model_budget_summary,
)
from ml.model.calibrate import (
    compute_ece,
    compute_nll,
    fit_temperature_calibration,
    load_calibration_temperature,
)
from ml.model.embeddings import (
    build_and_save_embeddings,
    build_embedding_matrix,
    load_embedding_matrix,
    load_glove_vectors,
    save_embedding_matrix,
)
from ml.model.teacher import (
    GroqTeacher,
    TransformerTeacher,
    apply_temperature,
    generate_soft_labels,
)

__all__ = [
    "ScaleLayer",
    "build_crisis_classifier",
    "build_model",
    "estimate_model_size",
    "load_model_config",
    "print_model_budget_summary",
    "load_glove_vectors",
    "build_embedding_matrix",
    "save_embedding_matrix",
    "load_embedding_matrix",
    "build_and_save_embeddings",
    "apply_temperature",
    "GroqTeacher",
    "TransformerTeacher",
    "generate_soft_labels",
    "fit_temperature_calibration",
    "compute_ece",
    "compute_nll",
    "load_calibration_temperature",
]
