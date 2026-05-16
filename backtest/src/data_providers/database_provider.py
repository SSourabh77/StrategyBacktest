from __future__ import annotations

import pandas as pd

from src.data_providers.base import BaseDataProvider, DataRequest
from src.data_providers.validators import apply_column_mapping, validate_futures, validate_options


class DatabaseDataProvider(BaseDataProvider):
    name = "database"

    def _read_query(self, request: DataRequest, query_key: str) -> pd.DataFrame:
        try:
            from sqlalchemy import create_engine, text
        except ImportError as exc:
            raise ImportError("SQLAlchemy is required for database provider. Install requirements.txt first.") from exc

        db_config = request.config["data"].get("database", {})
        engine = create_engine(db_config["connection_url"])
        params = {
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
        }
        with engine.connect() as connection:
            return pd.read_sql(text(db_config[query_key]), connection, params=params)

    def load_futures(self, request: DataRequest) -> pd.DataFrame:
        df = self._read_query(request, "futures_query")
        df = apply_column_mapping(df, request.config["data"].get("column_mapping"))
        return validate_futures(df)

    def load_options(self, request: DataRequest) -> pd.DataFrame:
        df = self._read_query(request, "options_query")
        df = apply_column_mapping(df, request.config["data"].get("column_mapping"))
        return validate_options(df)
