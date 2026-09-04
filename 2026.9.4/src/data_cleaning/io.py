"""Input and output helpers for tabular data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def read_table(path: Path) -> pd.DataFrame:
    """Read a supported tabular file into a DataFrame."""

    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, dtype=str, keep_default_na=False, skipinitialspace=True)
    if suffix == ".json":
        return pd.read_json(path, dtype=str)
    if suffix == ".jsonl":
        return pd.read_json(path, lines=True, dtype=str)
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(path, dtype=str, keep_default_na=False)

    supported = ".csv, .json, .jsonl, .xls, .xlsx"
    raise ValueError(f"Unsupported input format {suffix!r}. Supported formats: {supported}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a JSON file with stable formatting."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
