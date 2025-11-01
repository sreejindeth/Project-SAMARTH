"""Command-line entrypoint for downloading and snapshotting datasets."""

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd

from .config import load_config
from .data_manager import DataManager


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_snapshot(df: pd.DataFrame, dest: Path, fmt: str) -> Path:
    fmt = fmt.lower()
    if fmt == "parquet":
        try:
            df.to_parquet(dest.with_suffix(".parquet"), index=False)
            return dest.with_suffix(".parquet")
        except Exception as exc:  # noqa: BLE001
            print(f"[ingest] Parquet write failed ({exc}); falling back to CSV.")
            return _write_snapshot(df, dest, "csv")
    elif fmt == "csv":
        df.to_csv(dest.with_suffix(".csv"), index=False)
        return dest.with_suffix(".csv")
    else:
        raise ValueError(f"Unsupported format '{fmt}'.")


def ingest(datasets: Iterable[str], fmt: str, output: Path, force_refresh: bool) -> None:
    config = load_config()
    manager = DataManager(config)

    output = _ensure_dir(output)
    for name in datasets:
        print(f"[ingest] Loading dataset '{name}'...")
        df = manager.load_dataset(name, force_refresh=force_refresh)
        if df.empty:
            print(f"[ingest] Warning: dataset '{name}' returned no rows.")
            continue
        dest = output / f"{name}"
        result_path = _write_snapshot(df, dest, fmt)
        print(f"[ingest] Snapshot written to {result_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and snapshot Project Samarth datasets.")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=None,
        help="Datasets to ingest (default: all configured in config.yaml).",
    )
    parser.add_argument(
        "--format",
        choices=["parquet", "csv"],
        default="parquet",
        help="Snapshot format (default: parquet, falls back to csv if pyarrow unavailable).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("../data/processed"),
        help="Output directory for processed snapshots.",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force re-download even if cached.",
    )
    args = parser.parse_args()

    config = load_config()
    dataset_names = args.datasets or list(config.get("datasets", {}).keys())

    if not dataset_names:
        raise SystemExit("No datasets configured. Check backend/config.yaml.")

    ingest(dataset_names, args.format, args.output, args.force_refresh)


if __name__ == "__main__":
    main()

