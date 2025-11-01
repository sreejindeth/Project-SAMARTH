# Data Integration Notes

## Target Portals
- **Ministry of Agriculture & Farmers Welfare** – crop production datasets (district/state granularity).
- **India Meteorological Department (IMD)** – rainfall and temperature series published via data.gov.in CKAN API.

## High-Value Datasets
| Label | data.gov.in Resource | Schema Highlights | Update Cadence | Notes |
| --- | --- | --- | --- | --- |
| `agri_production` | `9ef84268-d588-465a-a308-a864a43d0070` | `State_Name`, `District_Name`, `Crop`, `Crop_Year`, `Season`, `Production` (tonnes) | Annual | Comprehensive crop stats from `Agricultural Statistics at a Glance`. |
| `rainfall_state` | `cca5f77c-68b3-43df-bd01-beb3b69204ed` | `SUBDIVISION`, `YEAR`, `ANNUAL`, `JAN-FEB`, … | Annual | IMD rainfall series aggregated by meteorological subdivision. |
| `rainfall_district` | `f8b77da1-7387-45bf-a2b9-270c122d7b68` | `STATE`, `DISTRICT`, `YEAR`, `ANNUAL_RAINFALL` | Annual | Needed for district-level comparisons in sample questions. |
| `temperature_state` | `cbb357b0-3b46-47fa-9ef0-04b6dfe8353d` | `YEAR`, `STATE`, `AVG_TEMP` | Annual | Optional for climate correlation; fallback to rainfall if unavailable. |

Resource identifiers come from the CKAN `datastore` API; they can be looked up with:

```bash
curl "https://data.gov.in/api/3/action/package_search?q=<keywords>&api-key=$API_KEY"
```

## Harmonisation Strategy
- Normalize geographic names via a canonical dimension table (`state`, `district`) with aliases sourced from census codes.
- Convert crop names to lowercase snake-case, map multi-word aliases (e.g., `arhar/tur` → `pigeon_pea`).
- Standardise production units to metric tonnes and rainfall to millimetres.
- Add surrogate keys: `state_id`, `district_id`, `crop_id`.

## Access Pattern
1. Pull raw records through `datastore_search` with pagination (`offset`, `limit=1000`).
2. Persist raw JSON snapshots under `data/raw/<dataset>/<timestamp>.json`.
3. Transform into columnar tables (DuckDB/Parquet) for fast analytical queries.
4. Maintain derived aggregates:
   - `crop_production_yearly` (state/district, crop, year).
   - `rainfall_yearly` (state, year).
   - `crop_rainfall_summary` (joined view for correlations).

Run `python -m app.ingest --force-refresh` from `backend/` to automate the snapshot workflow (writes to `data/processed/`).

## Known Challenges
- District spellings vary across datasets; require fuzzy matching (Jaro-Winkler) with manual overrides.
- Some crops report `Production = 0` with `Area > 0`; treat as missing (`None`).
- Rainfall series may have gaps for recent years; fill via linear interpolation for trend charts, but keep raw values for citations.

## Credentials
- Users must generate a personal API key from data.gov.in developer portal.
- Provide the key via environment variable `DATAGOV_API_KEY` for ingestion jobs.
