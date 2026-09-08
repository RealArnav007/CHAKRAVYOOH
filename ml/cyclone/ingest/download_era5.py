"""ERA5 atmospheric reanalysis data downloader for storm environmental context via Copernicus CDS API."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import List, Optional

try:
    import cdsapi
except ImportError:
    cdsapi = None


CDS_SETUP_INSTRUCTIONS = """
[ERA5 / CDS API Notice]
Copernicus Climate Data Store (CDS) credentials not detected!
To enable real-time and historical ERA5 reanalysis ingestion:
1. Register for a free account at: https://cds.climate.copernicus.eu/
2. Retrieve your Personal Access Token from your CDS profile page.
3. Save your credentials to ~/.cdsapirc in the format:
   url: https://cds.climate.copernicus.eu/api
   key: <YOUR-PERSONAL-ACCESS-TOKEN>
   or export CDSAPI_URL and CDSAPI_KEY in your environment.

The pipeline will proceed using Tier-0 fallback or cached environmental estimates.
"""


def check_cds_credentials() -> bool:
    """Checks whether Copernicus CDS API credentials exist in environment or ~/.cdsapirc."""
    if os.environ.get("CDSAPI_KEY") and os.environ.get("CDSAPI_URL"):
        return True
    rc_file = Path.home() / ".cdsapirc"
    if rc_file.is_file():
        try:
            content = rc_file.read_text()
            if "key:" in content or "key :" in content:
                return True
        except Exception:
            pass
    return False


def download_era5_storm_context(
    storm_name: str,
    date_start: str,
    date_end: str,
    bbox: List[float],
    output_dir: Path,
    force: bool = False,
) -> Optional[Path]:
    """Requests and downloads ERA5 single-level and pressure-level atmospheric variables."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_nc = output_dir / f"era5_{storm_name.lower()}_{date_start.replace('-', '')}_{date_end.replace('-', '')}.nc"

    if out_nc.exists() and not force:
        print(f"[ERA5] Environmental NetCDF already exists at {out_nc}. Skipping download.")
        return out_nc

    if cdsapi is None:
        print("[ERA5] 'cdsapi' Python package is not installed.")
        print(CDS_SETUP_INSTRUCTIONS)
        return None

    if not check_cds_credentials():
        print(CDS_SETUP_INSTRUCTIONS)
        return None

    print(f"[ERA5] Initializing CDS API client for storm {storm_name}...")
    print(f"[ERA5] Date range: {date_start} to {date_end} | Bounding box (N/W/S/E): {bbox}")

    try:
        client = cdsapi.Client()

        # Download surface variables (SST, MSLP, 10m Winds)
        print("[ERA5] Requesting single-level surface fields (SST, MSL Pressure, 10m Winds)...")
        surface_nc = output_dir / f"era5_surface_{storm_name.lower()}.nc"
        client.retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "format": "netcdf",
                "variable": [
                    "sea_surface_temperature",
                    "mean_sea_level_pressure",
                    "10m_u_component_of_wind",
                    "10m_v_component_of_wind",
                ],
                "date": f"{date_start}/{date_end}",
                "time": [f"{h:02d}:00" for h in range(0, 24, 3)],
                "area": bbox,  # [North, West, South, East]
            },
            str(surface_nc),
        )

        # Download pressure level variables (Shear: 850/200 u/v, RH: 500, Vorticity: 850)
        print("[ERA5] Requesting pressure-level fields (850/200 hPa winds for shear, 500 hPa RH, 850 hPa vorticity)...")
        pressure_nc = output_dir / f"era5_pressure_{storm_name.lower()}.nc"
        client.retrieve(
            "reanalysis-era5-pressure-levels",
            {
                "product_type": "reanalysis",
                "format": "netcdf",
                "variable": [
                    "u_component_of_wind",
                    "v_component_of_wind",
                    "relative_humidity",
                    "vorticity",
                ],
                "pressure_level": ["200", "500", "850"],
                "date": f"{date_start}/{date_end}",
                "time": [f"{h:02d}:00" for h in range(0, 24, 3)],
                "area": bbox,
            },
            str(pressure_nc),
        )

        print(f"[ERA5] Successfully retrieved ERA5 datasets for {storm_name}:")
        print(f"       Surface NetCDF : {surface_nc}")
        print(f"       Pressure NetCDF: {pressure_nc}")
        return surface_nc

    except Exception as exc:
        print(f"[ERA5] CDS API request encountered an error: {exc}", file=sys.stderr)
        print(CDS_SETUP_INSTRUCTIONS)
        return None


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download ERA5 atmospheric reanalysis variables for cyclone environmental fusion.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--storm", type=str, default="Amphan", help="Name of the cyclone")
    parser.add_argument("--date-start", type=str, default="2020-05-16", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--date-end", type=str, default="2020-05-21", help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        default=[28.0, 78.0, 5.0, 96.0],
        metavar=("NORTH", "WEST", "SOUTH", "EAST"),
        help="Geographic bounding box: North West South East in decimal degrees.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("ml/cyclone/data/era5"),
        help="Directory to save downloaded NetCDF files.",
    )
    parser.add_argument("--force", action="store_true", help="Force re-download even if files exist.")

    args = parser.parse_args(argv)

    try:
        download_era5_storm_context(
            storm_name=args.storm,
            date_start=args.date_start,
            date_end=args.date_end,
            bbox=args.bbox,
            output_dir=args.output_dir,
            force=args.force,
        )
        return 0
    except Exception as err:
        print(f"[Error] ERA5 download failed: {err}", file=sys.stderr)
        return 0  # Exit 0 with graceful instruction output per requirements


if __name__ == "__main__":
    sys.exit(main())
