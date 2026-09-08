"""Typed loader and lazy reader for multi-source geostationary satellite IR imagery."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, Union
import numpy as np
import pandas as pd
from PIL import Image

from ml.cyclone.config import load_config


SATELLITE_INDEX_COLUMNS = [
    "image_path",
    "time",
    "lat",
    "lon",
    "wind_kt",
    "pres_mb",
    "storm_id",
    "source",
]


def load_image_index(
    source: Optional[str] = None,
    data_dir: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """Loads standardized satellite image index from Digital Typhoon and/or DrivenData.

    Args:
        source: Optional filter: 'digital_typhoon', 'drivendata', or None (loads all available).
        data_dir: Base directory containing satellite datasets. Defaults to ml/cyclone/data.

    Returns:
        pd.DataFrame with columns: [image_path, time, lat, lon, wind_kt, pres_mb, storm_id, source]
    """
    cfg = load_config()
    base_data = Path(data_dir) if data_dir else Path(cfg.data.paths.data_root)

    dfs = []
    sources_to_check = [source] if source else ["digital_typhoon", "drivendata"]

    for src in sources_to_check:
        src_dir = base_data / src
        if not src_dir.exists():
            continue

        # Look for master index, then sample index
        candidates = [
            src_dir / f"{src}_index.csv",
            src_dir / f"{src}_sample.csv",
        ]

        found_csv = None
        for cand in candidates:
            if cand.is_file():
                found_csv = cand
                break

        if found_csv is None:
            continue

        raw_df = pd.read_csv(found_csv)
        normalized_df = pd.DataFrame()

        # Image path resolution
        if "image_path" in raw_df.columns:
            normalized_df["image_path"] = raw_df["image_path"].astype(str)
        elif "relative_path" in raw_df.columns:
            normalized_df["image_path"] = raw_df["relative_path"].apply(lambda p: str(src_dir / p))
        else:
            normalized_df["image_path"] = raw_df.iloc[:, 0].astype(str)

        # Time
        time_col = "timestamp" if "timestamp" in raw_df.columns else ("time" if "time" in raw_df.columns else None)
        if time_col:
            normalized_df["time"] = pd.to_datetime(raw_df[time_col], utc=True, errors="coerce")
        else:
            normalized_df["time"] = pd.Series(pd.Timestamp.now(tz="UTC"), index=raw_df.index)

        # Lat / Lon
        lat_series = raw_df["lat"] if "lat" in raw_df.columns else pd.Series(15.0, index=raw_df.index)
        lon_series = raw_df["lon"] if "lon" in raw_df.columns else pd.Series(85.0, index=raw_df.index)
        normalized_df["lat"] = pd.to_numeric(lat_series, errors="coerce").fillna(15.0)
        normalized_df["lon"] = pd.to_numeric(lon_series, errors="coerce").fillna(85.0)

        # Wind speed & Pressure
        wind_col = "wind_speed_kt" if "wind_speed_kt" in raw_df.columns else ("wind_kt" if "wind_kt" in raw_df.columns else ("wind_speed" if "wind_speed" in raw_df.columns else None))
        pres_col = "min_pressure_mb" if "min_pressure_mb" in raw_df.columns else ("pres_mb" if "pres_mb" in raw_df.columns else ("pressure" if "pressure" in raw_df.columns else None))

        wind_series = raw_df[wind_col] if wind_col else pd.Series(45.0, index=raw_df.index)
        pres_series = raw_df[pres_col] if pres_col else pd.Series(990.0, index=raw_df.index)

        normalized_df["wind_kt"] = pd.to_numeric(wind_series, errors="coerce").fillna(45.0)
        normalized_df["pres_mb"] = pd.to_numeric(pres_series, errors="coerce").fillna(990.0)

        # Storm ID
        storm_series = raw_df["storm_id"] if "storm_id" in raw_df.columns else pd.Series("STORM", index=raw_df.index)
        normalized_df["storm_id"] = storm_series.astype(str)
        normalized_df["source"] = src

        dfs.append(normalized_df)

    if not dfs:
        # Return clean empty DataFrame with standard schema if no index exists
        return pd.DataFrame(columns=SATELLITE_INDEX_COLUMNS)

    master_df = pd.concat(dfs, ignore_index=True)
    return master_df[SATELLITE_INDEX_COLUMNS]


def read_image(
    path: Union[str, Path],
    target_size: Tuple[int, int] = (224, 224),
    norm_min: float = 180.0,
    norm_max: float = 310.0,
) -> np.ndarray:
    """Lazily reads and normalizes a satellite image file into a float32 array in [0.0, 1.0].

    Supports .npy (brightness temperature in Kelvin), .png, .jpg, and raw tensors.

    Args:
        path: Filepath to satellite image.
        target_size: Target (height, width) spatial dimension.
        norm_min: Lower bound for Kelvin normalization (default: 180.0 K).
        norm_max: Upper bound for Kelvin normalization (default: 310.0 K).

    Returns:
        np.ndarray of shape (target_size[0], target_size[1]) with dtype float32 in range [0.0, 1.0].
    """
    img_path = Path(path)
    if not img_path.exists():
        raise FileNotFoundError(f"Satellite image not found at {img_path}")

    if img_path.suffix == ".npy":
        arr = np.load(img_path).astype(np.float32)
        # Handle 3D (C, H, W) or (H, W, C)
        if arr.ndim == 3:
            arr = arr[0] if arr.shape[0] in [1, 3] else arr[..., 0]
        # Normalize Kelvin brightness temperature to [0, 1]
        norm_arr = (arr - norm_min) / (norm_max - norm_min)
        norm_arr = np.clip(norm_arr, 0.0, 1.0).astype(np.float32)

    elif img_path.suffix in [".png", ".jpg", ".jpeg"]:
        with Image.open(img_path) as img:
            img_gray = img.convert("L")
            if img_gray.size != (target_size[1], target_size[0]):
                img_gray = img_gray.resize((target_size[1], target_size[0]), Image.Resampling.BILINEAR)
            norm_arr = np.array(img_gray, dtype=np.float32) / 255.0

    else:
        raise ValueError(f"Unsupported image file extension: {img_path.suffix}")

    # Resize if shape does not match target_size
    if norm_arr.shape != target_size:
        pil_img = Image.fromarray((norm_arr * 255.0).astype(np.uint8))
        pil_resized = pil_img.resize((target_size[1], target_size[0]), Image.Resampling.BILINEAR)
        norm_arr = np.array(pil_resized, dtype=np.float32) / 255.0

    return norm_arr.astype(np.float32)


__all__ = ["load_image_index", "read_image", "SATELLITE_INDEX_COLUMNS"]
