import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import httpx
import pandas as pd


class DatasetConfig(Dict):
    """Typed helper for IDEs."""


class DataManager:
    def __init__(self, config: Dict):
        self._app_cfg = config.get("app", {})
        self._datasets = config.get("datasets", {})
        self._cache: Dict[str, pd.DataFrame] = {}
        base_dir = self._app_cfg.get("dataset_cache_dir", "../data")
        self._data_dir = (Path(__file__).resolve().parent.parent / base_dir).resolve()
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def get_metadata(self, name: str) -> DatasetConfig:
        cfg: Optional[DatasetConfig] = self._datasets.get(name)
        if not cfg:
            raise KeyError(f"Unknown dataset '{name}'")
        return cfg

    def load_dataset(self, name: str, *, force_refresh: bool = False) -> pd.DataFrame:
        if not force_refresh and name in self._cache:
            return self._cache[name]

        cfg: Optional[DatasetConfig] = self._datasets.get(name)
        if not cfg:
            raise KeyError(f"Unknown dataset '{name}'. Check config.yaml.")

        df = None
        api_key = os.getenv("DATAGOV_API_KEY")
        if api_key:
            try:
                df = self._fetch_remote(cfg, api_key)
            except Exception as exc:  # noqa: BLE001 - surface context
                print(f"[DataManager] Remote fetch failed for '{name}': {exc}. Falling back to local sample.")

        if df is None:
            df = self._load_local_sample(cfg)

        self._cache[name] = df
        return df

    def reload_all(self) -> Dict[str, pd.DataFrame]:
        self._cache.clear()
        for dataset_name in self._datasets:
            self.load_dataset(dataset_name, force_refresh=True)
        return self._cache

    def _fetch_remote(self, cfg: DatasetConfig, api_key: str) -> pd.DataFrame:
        resource_id = cfg.get("resource_id")
        if not resource_id:
            raise ValueError("Missing resource_id for remote fetch.")

        client = httpx.Client(timeout=30.0, follow_redirects=True)
        records = []
        limit = 2000
        offset = 0
        more = True
        while more:
            params = {
                "resource_id": resource_id,
                "api-key": api_key,
                "limit": limit,
                "offset": offset,
            }
            resp = client.get("https://data.gov.in/api/3/action/datastore_search", params=params)
            resp.raise_for_status()
            payload = resp.json()
            result = payload.get("result", {})
            batch = result.get("records", [])
            records.extend(batch)
            offset += limit
            more = len(batch) == limit

        if not records:
            raise RuntimeError("No records returned from API.")

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        raw_path = self._data_dir / "raw" / cfg.get("resource_id", "unknown")
        raw_path.mkdir(parents=True, exist_ok=True)
        snapshot_file = raw_path / f"{timestamp}.json"
        snapshot_file.write_text(json.dumps(records, indent=2), encoding="utf-8")

        df = pd.DataFrame.from_records(records)
        df = self._normalise_columns(df)
        return df

    def _load_local_sample(self, cfg: DatasetConfig) -> pd.DataFrame:
        sample_path = cfg.get("local_sample")
        if not sample_path:
            raise FileNotFoundError(f"No local_sample configured for dataset: {cfg}")
        resolved = (Path(__file__).resolve().parent.parent / sample_path).resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Sample file not found: {resolved}")
        df = pd.read_csv(resolved)
        df = self._normalise_columns(df)
        return df

    @staticmethod
    def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
        df.columns = [col.strip().lower() for col in df.columns]
        return df
