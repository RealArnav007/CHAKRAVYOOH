"""
Project Pukar - Pretrained Embedding Matrix Initialization & Multilingual OOV Handling
=======================================================================================

Overview:
---------
Initializes a lightweight pretrained embedding matrix aligned with Project Pukar's
crisis vocabulary (ml/tokenizer/vocab.json).

Using a compact pretrained embedding matrix (e.g. GloVe-Twitter 25d or 50d) enables
a micro-sized on-device model to "punch above its weight" on short, high-urgency disaster text:
- Captures semantic relationships, conversational slang, urgency cues, and punctuation.
- Preserves the strict < 5 MB TFLite model size budget on resource-constrained edge devices.

Embedding Dimension Choice Justification (25d vs 50d):
------------------------------------------------------
1. Parameter Budget & Mobile CPU Cache:
   - For an on-device vocabulary of 3,000–5,000 tokens, a 25d embedding matrix consumes only
     ~75,000 to 125,000 float32 parameters (~300 KB to ~500 KB unquantized, < 125 KB fp16/int8).
   - A 50d matrix requires ~150,000 to 250,000 parameters (~600 KB to 1 MB).
   - Higher dimensions (100d, 300d) would consume > 50% of the entire 5 MB model budget on the
     embedding table alone, starving downstream 1D-CNN filters and causing CPU L1/L2 cache thrashing
     on low-end ARM Cortex-A53 cores during batch=1 edge inference (< 30 ms SLA).
2. Crisis Message Characteristics:
   - Distress packets are concise (< 64 tokens) with high-density emergency signals (e.g. "trapped",
     "bleeding", "cylinder", "fire", "flood"). A 25d or 50d manifold provides sufficient angular
     separation for crisis severity and category classification without overfitting.
3. Default Choice:
   - We default to dim=25 (with full support for dim=50), maintaining maximum compactness.

Multilingual OOV & Hindi/Hinglish Handling:
-------------------------------------------
1. Devanagari Hindi tokens (e.g., "पानी", "मकान", "मलबे", "तुरंत") and Romanized Hinglish
   slang (e.g., "fase", "chhat", "doobne", "bachao") do not have direct representations in
   standard English GloVe-Twitter corpora.
2. For any vocabulary token without a pretrained GloVe vector:
   - Initialized with zero-mean normal distribution with small variance (std=0.05).
   - Small variance prevents large initial gradients from destabilizing the shared Conv1D layers.
3. Special Tokens:
   - `<PAD>` (index 0): strictly forced to the zero vector [0.0, ..., 0.0].
   - `<UNK>` (index 1): initialized with small-variance random vector.
4. Downstream Trainability:
   - All embedding weights (both pretrained GloVe anchors and randomly initialized Hindi/Hinglish
     tokens) remain trainable (`trainable=True` in Keras Embedding layer), allowing multi-task
     backpropagation to align multilingual embeddings into a shared disaster semantic space.

Setup Note / GloVe Download Instructions:
------------------------------------------
To use official GloVe-Twitter pretrained vectors:
1. Download GloVe Twitter (27B tokens):
     curl -LO https://nlp.stanford.edu/data/glove.twitter.27B.zip
2. Unzip the 25d or 50d file:
     unzip glove.twitter.27B.zip glove.twitter.27B.25d.txt -d ml/model/glove/
3. Run this script pointing to the extracted vector file:
     python -m ml.model.embeddings --glove-path ml/model/glove/glove.twitter.27B.25d.txt --dim 25
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pukar.embeddings")

DEFAULT_VOCAB_PATH = Path("ml/tokenizer/vocab.json")
DEFAULT_EMBEDDING_PATH = Path("ml/model/embedding_matrix.npy")
DEFAULT_DIM = 25  # 25d chosen to respect < 5 MB TFLite edge budget


def load_glove_vectors(
    glove_path: str | Path,
    expected_dim: int = DEFAULT_DIM,
) -> dict[str, np.ndarray]:
    """
    Loads GloVe vector text file into an in-memory dictionary mapping word -> numpy array.

    Args:
        glove_path: Path to the GloVe .txt file (e.g., glove.twitter.27B.25d.txt).
        expected_dim: Expected dimensionality of each embedding vector (25 or 50).

    Returns:
        Dictionary mapping lowercased words to 1D float32 numpy arrays of shape (expected_dim,).
    """
    path = Path(glove_path)
    if not path.exists():
        raise FileNotFoundError(
            f"GloVe file not found at '{path}'. "
            "Please download GloVe-Twitter 25d/50d vectors (see setup note in module docstring)."
        )

    logger.info("Loading GloVe vectors from %s (expected dim=%d)...", path, expected_dim)
    embeddings_index: dict[str, np.ndarray] = {}
    lines_parsed = 0
    dim_mismatch_count = 0

    with open(path, encoding="utf-8", errors="ignore") as f:
        for line_num, line in enumerate(f, start=1):
            parts = line.strip().split()
            if not parts:
                continue

            word = parts[0]
            # Handle possible words containing whitespace or anomalous formatting
            try:
                vector = np.asarray(parts[1:], dtype=np.float32)
            except ValueError:
                # Malformed line, skip
                continue

            if len(vector) != expected_dim:
                dim_mismatch_count += 1
                continue

            embeddings_index[word.lower()] = vector
            lines_parsed += 1

    logger.info(
        "Successfully loaded %d GloVe word vectors from %s (skipped %d dimension mismatches).",
        lines_parsed,
        path.name,
        dim_mismatch_count,
    )
    return embeddings_index


def build_embedding_matrix(
    vocab_path: str | Path = DEFAULT_VOCAB_PATH,
    glove_path: str | Path | None = None,
    embedding_dim: int = DEFAULT_DIM,
    random_variance: float = 0.05,
    seed: int = 42,
) -> tuple[np.ndarray, dict[str, Any]]:
    """
    Builds a dense embedding matrix aligned with the tokenizer vocabulary.

    Args:
        vocab_path: Path to the JSON vocabulary file (ml/tokenizer/vocab.json).
        glove_path: Optional path to GloVe vector text file. If None or not found,
                    initializes all tokens with small-variance normal noise.
        embedding_dim: Dimensionality of embeddings (typically 25 or 50).
        random_variance: Standard deviation for random initialization of OOV/Hindi tokens.
        seed: Random seed for reproducible initialization.

    Returns:
        Tuple of:
            - embedding_matrix: np.ndarray of shape (vocab_size, embedding_dim), dtype float32.
            - stats: dictionary with vocabulary coverage metrics and breakdown.
    """
    vocab_file = Path(vocab_path)
    if not vocab_file.exists():
        raise FileNotFoundError(f"Vocabulary file not found at '{vocab_file}'")

    with open(vocab_file, encoding="utf-8") as f:
        vocab_data = json.load(f)

    # Support both raw dict {word: idx} and structured dict {"vocab": {word: idx}}
    token_to_idx: dict[str, int] = vocab_data.get("vocab", vocab_data)
    pad_token = vocab_data.get("pad_token", "<PAD>")
    unk_token = vocab_data.get("unk_token", "<UNK>")

    vocab_size = max(token_to_idx.values()) + 1 if token_to_idx else 0
    if vocab_size == 0:
        raise ValueError(f"Vocabulary in '{vocab_file}' is empty.")

    # Set random seed for deterministic initialization of OOV and Hindi/Hinglish terms
    rng = np.random.default_rng(seed)

    # Initialize full matrix with small-variance Gaussian distribution (mean=0, std=random_variance)
    # Small variance ensures initial activations in downstream Conv1D layers are well-conditioned.
    embedding_matrix = rng.normal(
        loc=0.0,
        scale=random_variance,
        size=(vocab_size, embedding_dim),
    ).astype(np.float32)

    # Special token 0 (<PAD>): strictly zeros
    pad_idx = token_to_idx.get(pad_token, 0)
    if pad_idx < vocab_size:
        embedding_matrix[pad_idx] = np.zeros(embedding_dim, dtype=np.float32)

    # Load GloVe vectors if path is provided and exists
    glove_index: dict[str, np.ndarray] = {}
    if glove_path:
        g_path = Path(glove_path)
        if g_path.exists():
            glove_index = load_glove_vectors(g_path, expected_dim=embedding_dim)
        else:
            logger.warning(
                "GloVe path '%s' does not exist. Initializing all tokens randomly (small variance).",
                glove_path,
            )

    matched_tokens: list[str] = []
    oov_tokens: list[str] = []
    special_tokens: list[str] = [pad_token]

    for token, idx in token_to_idx.items():
        if idx >= vocab_size:
            continue

        if token == pad_token:
            embedding_matrix[idx] = np.zeros(embedding_dim, dtype=np.float32)
            continue

        # Look up token in GloVe (try exact match, lowercased, and stripped punctuation)
        token_clean = token.strip().lower()
        vector = glove_index.get(token_clean)

        if vector is not None:
            embedding_matrix[idx] = vector
            matched_tokens.append(token)
        else:
            # Token is OOV (Devanagari Hindi, Romanized Hinglish, or special token)
            # Retains the small-variance random initialization; marked trainable in model.
            if token == unk_token:
                special_tokens.append(token)
            else:
                oov_tokens.append(token)

    total_words = len(token_to_idx)
    content_tokens_count = len(matched_tokens) + len(oov_tokens)
    coverage_pct = (len(matched_tokens) / content_tokens_count * 100.0) if content_tokens_count > 0 else 0.0

    stats: dict[str, Any] = {
        "vocab_size": vocab_size,
        "embedding_dim": embedding_dim,
        "total_tokens": total_words,
        "pretrained_matched_count": len(matched_tokens),
        "oov_or_hindi_count": len(oov_tokens),
        "special_tokens_count": len(special_tokens),
        "coverage_percentage": round(coverage_pct, 2),
        "matched_sample": matched_tokens[:10],
        "oov_sample": oov_tokens[:10],
    }

    return embedding_matrix, stats


def save_embedding_matrix(
    matrix: np.ndarray,
    output_path: str | Path = DEFAULT_EMBEDDING_PATH,
) -> Path:
    """
    Saves the embedding matrix as a binary .npy file.

    Args:
        matrix: 2D numpy array of shape (vocab_size, embedding_dim).
        output_path: Output file path.

    Returns:
        Path to the saved .npy file.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_file, matrix.astype(np.float32))
    logger.info("Saved embedding matrix [shape=%s] to %s", matrix.shape, out_file)
    return out_file


def load_embedding_matrix(
    matrix_path: str | Path = DEFAULT_EMBEDDING_PATH,
) -> np.ndarray:
    """
    Loads an embedding matrix from a .npy file.

    Args:
        matrix_path: Path to the .npy file.

    Returns:
        Numpy array containing the embedding matrix.
    """
    in_file = Path(matrix_path)
    if not in_file.exists():
        raise FileNotFoundError(f"Embedding matrix not found at '{in_file}'")
    matrix = np.load(in_file)
    return matrix


def build_and_save_embeddings(
    vocab_path: str | Path = DEFAULT_VOCAB_PATH,
    glove_path: str | Path | None = None,
    output_path: str | Path = DEFAULT_EMBEDDING_PATH,
    embedding_dim: int = DEFAULT_DIM,
    seed: int = 42,
) -> tuple[np.ndarray, dict[str, Any]]:
    """
    Builds, logs statistics for, and saves the vocabulary-aligned embedding matrix.
    """
    matrix, stats = build_embedding_matrix(
        vocab_path=vocab_path,
        glove_path=glove_path,
        embedding_dim=embedding_dim,
        seed=seed,
    )
    save_embedding_matrix(matrix, output_path=output_path)

    # Print coverage and summary report
    print("\n" + "=" * 65)
    print(" PROJECT PUKAR — EMBEDDING MATRIX GENERATION REPORT")
    print("=" * 65)
    print(f" Vocabulary Path:       {vocab_path}")
    print(f" Output Matrix Path:    {output_path}")
    print(f" Matrix Dimensions:     {stats['vocab_size']} tokens × {stats['embedding_dim']} dim")
    print(f" Total Tokens:          {stats['total_tokens']}")
    print(f" Pretrained Matched:    {stats['pretrained_matched_count']}")
    print(f" OOV / Hindi / Hinglish: {stats['oov_or_hindi_count']} (Random Init + Trainable)")
    print(f" Pretrained Coverage:   {stats['coverage_percentage']:.2f}%")
    print("-" * 65)
    if stats["matched_sample"]:
        print(f" Sample Pretrained:     {', '.join(stats['matched_sample'])}")
    if stats["oov_sample"]:
        print(f" Sample OOV / Hindi:    {', '.join(stats['oov_sample'])}")
    print("=" * 65 + "\n")

    return matrix, stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize small pretrained embedding matrix for Project Pukar vocabulary."
    )
    parser.add_argument(
        "--vocab-path",
        type=str,
        default=str(DEFAULT_VOCAB_PATH),
        help="Path to vocab.json (default: ml/tokenizer/vocab.json)",
    )
    parser.add_argument(
        "--glove-path",
        type=str,
        default=None,
        help="Path to GloVe vector text file (e.g. glove.twitter.27B.25d.txt)",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=str(DEFAULT_EMBEDDING_PATH),
        help="Path to output embedding_matrix.npy (default: ml/model/embedding_matrix.npy)",
    )
    parser.add_argument(
        "--dim",
        type=int,
        default=DEFAULT_DIM,
        help="Embedding dimensionality (25 or 50, default: 25)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for OOV initialization (default: 42)",
    )
    args = parser.parse_args()

    build_and_save_embeddings(
        vocab_path=args.vocab_path,
        glove_path=args.glove_path,
        output_path=args.output_path,
        embedding_dim=args.dim,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
