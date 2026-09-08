# 📊 Chakravyuh Cyclone Intelligence Engine — Data Card

## 1. Multi-Source Dataset Registry

The Chakravyuh Cyclone Engine integrates multi-modal satellite observations, global numerical reanalysis, and official best-track archives.

| Source | Provider | Modality / Variables | License | Access Method | Auth Required? | Consuming Component |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **IBTrACS (NI Subset)** | NOAA NCEI | 3-hourly Best Track: `lat`, `lon`, `wind_kt`, `pres_mb`, `speed`, `heading`, `nature` | Public Domain / NOAA Open Data | Direct HTTPS CSV Download (`ingest/download_ibtracs.py`) | ❌ No | Ground Truth Labels, Track GRU Branch, Tier-0 CLIPER Baseline |
| **IMD RSMC Best Track** | IMD New Delhi | Official RSMC Cyclone e-Atlas records, 3-min sustained wind, IMD classifications | Open Government Data (OGD India) | Web Scraping / Table Ingestion | ❌ No | IMD Scale Calibration & RSMC Ground Truth Validation |
| **Digital Typhoon** | NII, Japan | 40+ Years of Geostationary IR Satellites (Himawari/MTSAT/GMS) 512×512 patches + track metadata | CC BY 4.0 / Academic Open Access | Tar/Zip Archives via `download_digital_typhoon.py` | ⚠️ Free Registration | Tier-1 Satellite IR CNN Backbone Pretraining |
| **DrivenData Wind Speed** | DrivenData / MathWorks | Geostationary single-band IR storm patches labeled with verified wind speeds | Competition Open Data | Archive Download via `download_drivendata.py` | ⚠️ Free Competition Account | Satellite Intensity Regression Benchmark & Transfer Fine-Tuning |
| **HURSAT-B1** | NOAA NCEI | Gridded 3-hourly 8km IR centered storm patches | Public Domain (NOAA) | NCEI HTTP / S3 Mirror | ❌ No | Satellite CNN Multi-Basin Transfer Learning |
| **INSAT-3D / 3DR** | ISRO MOSDAC | Domestic Geostationary Imager IR1 (10.8µm), TIR2 (12.0µm), Water Vapor (6.8µm) | Open ISRO Academic License | MOSDAC API / Portal | ⚠️ Free MOSDAC Account | Live & Replay Satellite Ingestion for North Indian Ocean Storms |
| **ERA5 Atmospheric** | ECMWF / Copernicus CDS | SST, 850–200 hPa Wind Shear, 500 hPa RH, 850 hPa Vorticity, MSLP | CC BY 4.0 / Copernicus Open Access | `cdsapi` REST Client (`download_era5.py`) | 🔑 Free CDS API Key (`~/.cdsapirc`) | Tier-1 Atmospheric Environmental MLP Branch |
| **INCOIS Ocean Heat** | INCOIS (MoES India) | Ocean Heat Content (OHC), Sea Surface Salinity, Tropical Cyclone Heat Potential | OGD India | Web GIS / In Situ Buoys | ❌ No | High-Resolution Indian Ocean Thermal Context |

---

## 2. Recommended Demo Storms

The engine provides calibrated historical replay streams for benchmark storms in the North Indian Ocean basin:

### 🌟 Primary Storm 1: Super Cyclonic Storm Amphan (May 2020)
- **Basin**: Bay of Bengal
- **Peak Intensity**: Super Cyclonic Storm (130 kt / 240 km/h, 920 mb)
- **Trajectory Arc**: Formed in the South Bay of Bengal $\to$ explosive rapid intensification (RI) over anomalously warm SSTs $\to$ curved north-northeast $\to$ devastating landfall near West Bengal / Bangladesh border (20 May 2020).
- **Why It's the Primary Showcase**:
  1. Complete high-quality INSAT-3D, HURSAT, and ERA5 coverage.
  2. Exhibits the full dynamic spectrum: tropical depression $\to$ Category 5 equivalent $\to$ extratropical transition / post-landfall dissipation.
  3. Demonstrates the power of **learned heteroscedastic uncertainty cones** during the critical 24–48h pre-landfall curvature window.

### 🌟 Primary Storm 2: Extremely Severe Cyclonic Storm Biparjoy (June 2023)
- **Basin**: Arabian Sea
- **Peak Intensity**: Extremely Severe Cyclonic Storm (90 kt, 954 mb)
- **Trajectory Arc**: Extremely long-lived, complex erratic track over the Arabian Sea with dual stalling periods before making landfall in Gujarat, India (15 June 2023).
- **Why It's the Primary Showcase**:
  1. Tests trajectory forecasting under anomalous steering flow and environmental wind shear.
  2. Directly contrasts Arabian Sea dynamics against Bay of Bengal dynamics.

---

### 🛡️ Backup Demo Storms

- **Extremely Severe Cyclonic Storm Fani (April–May 2019)**:
  - *Location*: Bay of Bengal $\to$ Puri, Odisha.
  - *Rationale*: Classic recurving track, rare April/May genesis near equator; rigorous test of early-season climatology and intensity estimation.
- **Extremely Severe Cyclonic Storm Tauktae (May 2021)**:
  - *Location*: Arabian Sea $\to$ Southern Gujarat.
  - *Rationale*: Intense coastal-parallel northward track demonstrating persistent cross-shore risk modeling.
- **Severe Cyclonic Storm Remal (May 2024)**:
  - *Location*: Bay of Bengal $\to$ West Bengal/Bangladesh.
  - *Rationale*: Most recent benchmark for modern operational INSAT-3DR satellite and multi-sensor validation.

---

## 3. Data Hygiene & Security Guidelines

- **Zero Secret Exposure**: CDS API keys, ISRO credentials, or private tokens must **never** be committed into source control. All scripts inspect environment variables (`CDSAPI_KEY`, `CDSAPI_URL`) or local non-committed config (`~/.cdsapirc`).
- **Sample vs. Full Separation**:
  - Full NetCDF and raw image archives are ignored via `ml/cyclone/.gitignore`.
  - Minimal synthetic fixtures and sample index files (`*_sample.*`) with $\sim 50$ items are tracked for end-to-end unit test execution in CI/CD.
