from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pandas as pd

from src.data_providers.base import BaseDataProvider, DataRequest
from src.data_providers.validators import apply_column_mapping, validate_futures, validate_options


class CsvDataProvider(BaseDataProvider):
    name = "csv"

    def _date_paths(self, request: DataRequest, glob_pattern: str) -> list[Path]:
        data_cfg = request.config["data"]
        root = Path(data_cfg.get("root", "DATA"))
        folder_format = data_cfg.get("csv", {}).get("date_folder_format", "%Y-%m-%d")
        paths: list[Path] = []
        current = request.start_date
        while current <= request.end_date:
            folder = root / current.strftime(folder_format)
            paths.extend(sorted(folder.glob(glob_pattern)))
            current += timedelta(days=1)
        return paths

    def _read_many(self, paths: list[Path]) -> pd.DataFrame:
        if not paths:
            return pd.DataFrame()
        return pd.concat([pd.read_csv(path) for path in paths], ignore_index=True)

    def load_futures(self, request: DataRequest) -> pd.DataFrame:
        glob_pattern = request.config["data"].get("csv", {}).get("futures_glob", "*future*.csv")
        df = self._read_many(self._date_paths(request, glob_pattern))
        df = apply_column_mapping(df, request.config["data"].get("column_mapping"))
        return validate_futures(df)

    def load_options(self, request: DataRequest) -> pd.DataFrame:
        glob_pattern = request.config["data"].get("csv", {}).get("options_glob", "*option*.csv")
        df = self._read_many(self._date_paths(request, glob_pattern))
        if df.empty:
            return df
        df = apply_column_mapping(df, request.config["data"].get("column_mapping"))
        return validate_options(df)

