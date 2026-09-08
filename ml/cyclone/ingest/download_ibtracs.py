"""Reproducible, idempotent downloader and parser for IBTrACS North Indian Ocean best-track dataset."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import requests
except ImportError:
    requests = None

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


DEFAULT_IBTRACS_NI_URL = (
    "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs"
    "/v04r00/access/csv/ibtracs.NI.list.v04r00.csv"
)

SLIM_COLUMNS = [
    "SID",
    "NAME",
    "ISO_TIME",
    "LAT",
    "LON",
    "WMO_WIND",
    "USA_WIND",
    "WMO_PRES",
    "USA_PRES",
    "STORM_SPEED",
    "STORM_DIR",
    "NATURE",
    "BASIN",
]


def download_file(
    url: str, dest_path: Path, force: bool = False, chunk_size: int = 1024 * 64
) -> Path:
    """Streams a remote file to local disk with progress reporting and resume/skip support."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if dest_path.exists() and not force and dest_path.stat().st_size > 0:
        print(
            f"[IBTrACS] File already exists at {dest_path} ({dest_path.stat().st_size / (1024*1024):.2f} MB). Skipping download (use --force to re-download)."
        )
        return dest_path

    if requests is None:
        raise RuntimeError(
            "The 'requests' package is required for downloading. Run `pip install requests`."
        )

    print(f"[IBTrACS] Downloading from {url} to {dest_path}...")
    headers = {"User-Agent": "Chakravyuh-Cyclone-Intelligence/0.1"}

    try:
        response = requests.get(url, stream=True, timeout=60, headers=headers)
        response.raise_for_status()
    except Exception as exc:
        print(f"[IBTrACS] Download failed: {exc}", file=sys.stderr)
        raise

    total_size = int(response.headers.get("content-length", 0))

    temp_path = dest_path.with_suffix(".tmp")
    with open(temp_path, "wb") as f:
        if tqdm is not None and total_size > 0:
            with tqdm(total=total_size, unit="B", unit_scale=True, desc="ibtracs.NI.csv") as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        else:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)

    temp_path.replace(dest_path)
    print(f"[IBTrACS] Successfully downloaded {dest_path.stat().st_size / (1024*1024):.2f} MB.")
    return dest_path


def process_ibtracs_csv(raw_csv_path: Path, output_dir: Path) -> dict:
    """Parses raw IBTrACS CSV, extracts key meteorological features, and writes slim parquet + sample."""
    if pd is None:
        raise RuntimeError(
            "The 'pandas' package is required for processing. Run `pip install pandas pyarrow`."
        )

    print(f"[IBTrACS] Parsing {raw_csv_path}...")
    # IBTrACS row 0 is column names, row 1 contains units (e.g. 'kts', 'mb', etc.)
    df = pd.read_csv(raw_csv_path, skiprows=[1], low_memory=False)

    # Filter only available columns
    available_cols = [c for c in SLIM_COLUMNS if c in df.columns]
    slim_df = df[available_cols].copy()

    # Clean numeric types
    for num_col in [
        "LAT",
        "LON",
        "WMO_WIND",
        "USA_WIND",
        "WMO_PRES",
        "USA_PRES",
        "STORM_SPEED",
        "STORM_DIR",
    ]:
        if num_col in slim_df.columns:
            slim_df[num_col] = pd.to_numeric(
                slim_df[num_col].astype(str).str.strip(), errors="coerce"
            )

    # Clean strings
    for str_col in ["SID", "NAME", "ISO_TIME", "NATURE", "BASIN"]:
        if str_col in slim_df.columns:
            slim_df[str_col] = slim_df[str_col].astype(str).str.strip()

    # Save full slim parquet
    parquet_path = output_dir / "ibtracs_north_indian_ocean.parquet"
    try:
        slim_df.to_parquet(parquet_path, index=False)
        print(f"[IBTrACS] Saved slim parquet to {parquet_path}")
    except Exception as e:
        csv_fallback = output_dir / "ibtracs_north_indian_ocean.csv"
        slim_df.to_csv(csv_fallback, index=False)
        print(f"[IBTrACS] Parquet write failed ({e}); saved slim CSV to {csv_fallback}")

    # Save a small sample file that is safe to commit for unit testing
    sample_path = output_dir / "ibtracs_sample.csv"
    # Select sample from prominent recent storms or first 200 rows
    sample_df = slim_df.head(200)
    sample_df.to_csv(sample_path, index=False)
    print(f"[IBTrACS] Saved sample CSV ({len(sample_df)} records) to {sample_path}")

    # Summary metrics
    unique_storms = slim_df["SID"].nunique() if "SID" in slim_df.columns else 0
    total_records = len(slim_df)
    min_date = slim_df["ISO_TIME"].min() if "ISO_TIME" in slim_df.columns else "N/A"
    max_date = slim_df["ISO_TIME"].max() if "ISO_TIME" in slim_df.columns else "N/A"

    summary = {
        "raw_csv": str(raw_csv_path),
        "total_records": total_records,
        "unique_storms": unique_storms,
        "date_range": f"{min_date} -> {max_date}",
        "columns": available_cols,
    }

    print("\n" + "=" * 60)
    print(" IBTrACS North Indian Ocean Ingestion Summary")
    print("=" * 60)
    print(f" Total Records : {total_records:,}")
    print(f" Unique Storms : {unique_storms:,}")
    print(f" Date Range    : {min_date} to {max_date}")
    print(f" Output Parquet: {parquet_path}")
    print(f" Sample File   : {sample_path}")
    print("=" * 60 + "\n")

    return summary


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download and process IBTrACS North Indian Ocean cyclone best-track dataset.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--url",
        type=str,
        default=DEFAULT_IBTRACS_NI_URL,
        help="URL to download the IBTrACS North Indian Ocean CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("ml/cyclone/data/ibtracs"),
        help="Destination directory for downloaded and processed dataset files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if files already exist.",
    )

    args = parser.parse_args(argv)

    try:
        dest_csv = args.output_dir / "ibtracs.NI.list.v04r00.csv"
        download_file(url=args.url, dest_path=dest_csv, force=args.force)
        process_ibtracs_csv(raw_csv_path=dest_csv, output_dir=args.output_dir)
        return 0
    except Exception as err:
        print(f"[Error] IBTrACS ingestion failed: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
