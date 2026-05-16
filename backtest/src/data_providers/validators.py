from __future__ import annotations

import pandas as pd


FUTURES_REQUIRED = ["datetime", "symbol", "open", "high", "low", "close", "volume"]
OPTIONS_REQUIRED = [
    "datetime",
    "symbol",
    "expiry",
    "strike",
    "option_type",
    "open",
    "high",
    "low",
    "close",
    "volume",
]


class DataValidationError(ValueError):
    pass


def apply_column_mapping(df: pd.DataFrame, mapping: dict[str, str] | None) -> pd.DataFrame:
    if not mapping:
        return df
    rename_map = {source: standard for standard, source in mapping.items() if source in df.columns}
    return df.rename(columns=rename_map)


def validate_ohlc(df: pd.DataFrame, required: list[str], label: str) -> pd.DataFrame:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise DataValidationError(f"{label} data missing required columns: {missing}")

    clean = df.copy()
    clean["datetime"] = pd.to_datetime(clean["datetime"], errors="coerce")
    if clean["datetime"].isna().any():
        raise DataValidationError(f"{label} data contains invalid datetime values")

    for col in ["open", "high", "low", "close", "volume"]:
        clean[col] = pd.to_numeric(clean[col], errors="coerce")
        if clean[col].isna().any():
            raise DataValidationError(f"{label} data column {col} contains non-numeric values")

    if (clean["high"] < clean["low"]).any():
        raise DataValidationError(f"{label} data contains rows where high is less than low")

    return clean.sort_values("datetime").reset_index(drop=True)


def validate_futures(df: pd.DataFrame) -> pd.DataFrame:
    clean = validate_ohlc(df, FUTURES_REQUIRED, "Futures")
    duplicate_cols = ["datetime", "symbol"]
    if clean.duplicated(duplicate_cols).any():
        raise DataValidationError("Futures data contains duplicate datetime/symbol candles")
    return clean


def validate_options(df: pd.DataFrame) -> pd.DataFrame:
    clean = validate_ohlc(df, OPTIONS_REQUIRED, "Options")
    clean["expiry"] = pd.to_datetime(clean["expiry"], errors="coerce").dt.date.astype(str)
    clean["strike"] = pd.to_numeric(clean["strike"], errors="coerce")
    if clean["strike"].isna().any():
        raise DataValidationError("Options data contains invalid strike values")
    clean["option_type"] = clean["option_type"].astype(str).str.upper().replace({"CALL": "CE", "PUT": "PE"})
    if not clean["option_type"].isin(["CE", "PE"]).all():
        raise DataValidationError("Options data option_type must be CE/PE/CALL/PUT")
    duplicate_cols = ["datetime", "symbol", "expiry", "strike", "option_type"]
    if clean.duplicated(duplicate_cols).any():
        raise DataValidationError("Options data contains duplicate instrument candles")
    return clean

