"""DrivenData 'Predict Wind Speeds of Tropical Storms' dataset unpacker, indexer, and sample generator."""

from __future__ import annotations

import argparse
import sys
import tarfile
import zipfile
from pathlib import Path

try:
    import numpy as np
except ImportError:
    np = None

try:
    import pandas as pd
except ImportError:
    pd = None


INSTRUCTIONS = """
[DrivenData 'Predict Wind Speeds of Tropical Storms' Ingestion]
DrivenData requires a free user account and competition agreement.
To obtain the full competition dataset:
1. Visit: https://www.drivendata.org/competitions/72/predict-wind-speeds/
2. Download `train_features.tar.gz` (or `train_features.zip`) and `train_labels.csv`.
3. Run this script passing the downloaded archive:
   python -m ml.cyclone.ingest.download_drivendata --archive /path/to/train_features.tar.gz --labels /path/to/train_labels.csv

If no archive is provided, this script creates a synthetic 50-image test sample suite
in `ml/cyclone/data/drivendata_sample/` so test pipelines run out-of-the-box.
"""


def create_synthetic_drivendata_sample(output_dir: Path, num_samples: int = 50) -> Path:
    """Generates synthetic 224x224 infrared brightness temperature patches and metadata index for tests."""
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    records = []
    print(
        f"[DrivenData] Generating {num_samples} sample synthetic satellite IR patches for CI/testing..."
    )

    for i in range(num_samples):
        img_id = f"storm_sample_{i:03d}"
        img_filename = f"{img_id}.npy"
        img_path = images_dir / img_filename

        # Generate realistic vortex brightness temperature field (190K - 300K)
        # Eye: warmer center surrounded by cold convective eyewall
        if not img_path.exists():
            if np is not None:
                y, x = np.ogrid[-112:112, -112:112]
                r = np.sqrt(x * x + y * y)
                # Cold eyewall around r=30
                eyewall = np.exp(-((r - 30) ** 2) / (2 * 15**2))
                spiral = np.sin(r / 10 + np.arctan2(y, x) * 2) * np.exp(-r / 70)
                temp_field = (
                    290.0 - 90.0 * eyewall + 15.0 * spiral + np.random.normal(0, 2.0, (224, 224))
                )
                temp_field = np.clip(temp_field, 180.0, 310.0).astype(np.float32)
                np.save(img_path, temp_field)
            else:
                # Fallback empty byte placeholder if numpy not available
                img_path.write_bytes(b"\x00" * 1024)

        wind_kt = float(30.0 + (i % 8) * 12.5 + (i * 0.5))
        pres_mb = float(1005.0 - (wind_kt - 30) * 0.7)

        records.append(
            {
                "image_id": img_id,
                "storm_id": f"SYN_{i // 10:02d}",
                "image_path": str(img_path),
                "relative_path": f"images/{img_filename}",
                "wind_speed_kt": round(wind_kt, 1),
                "min_pressure_mb": round(pres_mb, 1),
                "time_step": i % 10,
            }
        )

    index_csv = output_dir / "drivendata_sample.csv"
    if pd is not None:
        pd.DataFrame(records).to_csv(index_csv, index=False)
    else:
        # Fallback manual CSV writing
        with open(index_csv, "w", encoding="utf-8") as f:
            f.write(
                "image_id,storm_id,image_path,relative_path,wind_speed_kt,min_pressure_mb,time_step\n"
            )
            for r in records:
                f.write(
                    f"{r['image_id']},{r['storm_id']},{r['image_path']},{r['relative_path']},{r['wind_speed_kt']},{r['min_pressure_mb']},{r['time_step']}\n"
                )

    print(f"[DrivenData] Sample index saved to {index_csv} ({len(records)} records).")
    return index_csv


def unpack_and_index_drivendata(
    archive_path: Path,
    labels_csv_path: Path | None,
    output_dir: Path,
    sample_size: int = 50,
) -> Path:
    """Unpacks user-provided DrivenData archive and produces an indexed metadata CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    extract_dir = output_dir / "raw_features"
    extract_dir.mkdir(exist_ok=True)

    print(f"[DrivenData] Unpacking {archive_path} to {extract_dir}...")
    if archive_path.suffix in [".gz", ".tgz"] or archive_path.name.endswith(".tar.gz"):
        with tarfile.open(archive_path, "r:*") as tar:
            tar.extractall(path=extract_dir)
    elif archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path, "r") as z:
            z.extractall(path=extract_dir)
    elif archive_path.is_dir():
        extract_dir = archive_path
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")

    # Discover images (.jpg, .png, .npy)
    image_files = (
        list(extract_dir.rglob("*.jpg"))
        + list(extract_dir.rglob("*.png"))
        + list(extract_dir.rglob("*.npy"))
    )
    print(f"[DrivenData] Discovered {len(image_files):,} satellite image frames.")

    labels_map = {}
    if labels_csv_path and labels_csv_path.is_file() and pd is not None:
        lbl_df = pd.read_csv(labels_csv_path)
        for _, row in lbl_df.iterrows():
            img_id = str(row.get("image_id", row.iloc[0])).strip()
            labels_map[img_id] = float(row.get("wind_speed", 0.0))

    records = []
    for img_p in image_files:
        stem = img_p.stem
        wind = labels_map.get(stem, 45.0)
        records.append(
            {
                "image_id": stem,
                "storm_id": stem.split("_")[0] if "_" in stem else "STORM",
                "image_path": str(img_p),
                "wind_speed_kt": wind,
            }
        )

    index_csv = output_dir / "drivendata_index.csv"
    if pd is not None:
        df = pd.DataFrame(records)
        df.to_csv(index_csv, index=False)
        print(f"[DrivenData] Master index written to {index_csv} ({len(df):,} items).")

        # Create small test sample
        sample_csv = output_dir / "drivendata_sample.csv"
        df.head(sample_size).to_csv(sample_csv, index=False)
        print(f"[DrivenData] Sample subset written to {sample_csv} ({sample_size} items).")
    return index_csv


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="DrivenData Wind-Dependent Tropical Cyclone Dataset processor and indexer.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=None,
        help="Path to downloaded train_features archive (.tar.gz / .zip)",
    )
    parser.add_argument("--labels", type=Path, default=None, help="Path to train_labels.csv")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("ml/cyclone/data/drivendata"),
        help="Output directory",
    )
    parser.add_argument(
        "--generate-sample-only",
        action="store_true",
        help="Generate synthetic test sample dataset.",
    )

    args = parser.parse_args(argv)

    if args.generate_sample_only or (args.archive is None and not args.output_dir.exists()):
        print(INSTRUCTIONS)
        create_synthetic_drivendata_sample(output_dir=args.output_dir)
        return 0

    if args.archive and args.archive.exists():
        unpack_and_index_drivendata(
            archive_path=args.archive,
            labels_csv_path=args.labels,
            output_dir=args.output_dir,
        )
        return 0

    print(INSTRUCTIONS)
    create_synthetic_drivendata_sample(output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
