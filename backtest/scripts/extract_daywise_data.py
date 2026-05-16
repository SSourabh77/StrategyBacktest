from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


FUTURES_REQUIRED = ["datetime", "symbol", "open", "high", "low", "close", "volume"]
OPTIONS_REQUIRED = ["datetime", "symbol", "expiry", "strike", "option_type", "open", "high", "low", "close", "volume"]


def load_mapping(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def read_table(path: str, sheet: str | None = None) -> pd.DataFrame:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(file_path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(file_path, sheet_name=sheet or 0)
    if suffix == ".parquet":
        return pd.read_parquet(file_path)
    raise ValueError(f"Unsupported file type: {file_path.suffix}. Use CSV, Excel, or Parquet.")


def apply_mapping(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    clean = df.copy()
    if mapping:
        rename_map = {source: standard for standard, source in mapping.items() if source in clean.columns}
        clean = clean.rename(columns=rename_map)
    return auto_standardize_columns(clean)


def auto_standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "datetime": ["datetime", "timestamp", "date_time", "candle_time", "time_stamp"],
        "symbol": ["symbol", "ticker", "instrument", "name"],
        "open": ["open", "open_price", "o"],
        "high": ["high", "high_price", "h"],
        "low": ["low", "low_price", "l"],
        "close": ["close", "close_price", "c", "ltp"],
        "volume": ["volume", "vol", "qty"],
        "expiry": ["expiry", "expiry_date", "expiration"],
        "strike": ["strike", "strike_price"],
        "option_type": ["option_type", "opt_type", "type", "cp", "call_put"],
        "derivative_type": ["derivative_type", "deriv_type", "instrument_type", "segment"],
        "open_interest": ["open_interest", "oi"],
    }
    normalized = {str(column).strip().lower(): column for column in df.columns}
    rename_map = {}
    for standard, names in aliases.items():
        if standard in df.columns:
            continue
        for name in names:
            if name in normalized:
                rename_map[normalized[name]] = standard
                break
    return df.rename(columns=rename_map)


def build_datetime(df: pd.DataFrame, date_col: str | None, time_col: str | None) -> pd.DataFrame:
    clean = df.copy()
    if "datetime" in clean.columns:
        clean["datetime"] = pd.to_datetime(clean["datetime"], errors="coerce")
        return clean
    if date_col is None:
        date_col = find_column(clean, ["date", "trade_date", "candle_date"])
    if time_col is None:
        time_col = find_column(clean, ["time", "trade_time", "candle_time"])
    if date_col and time_col and date_col in clean.columns and time_col in clean.columns:
        clean["datetime"] = pd.to_datetime(clean[date_col].astype(str) + " " + clean[time_col].astype(str), errors="coerce")
        return clean
    raise ValueError("No datetime column found. Provide datetime column mapping or --date-col and --time-col.")


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    normalized = {str(column).strip().lower(): column for column in df.columns}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    return None


def filter_derivative_type(df: pd.DataFrame, derivative_type: str, label: str) -> pd.DataFrame:
    if "derivative_type" not in df.columns:
        return df
    clean = df[df["derivative_type"].astype(str).str.strip().str.upper() == derivative_type].copy()
    if clean.empty:
        raise ValueError(f"No {label} rows found where derivative_type={derivative_type}")
    return clean


def has_derivative_type(df: pd.DataFrame, derivative_type: str) -> bool:
    if "derivative_type" not in df.columns:
        return False
    values = df["derivative_type"].astype(str).str.strip().str.upper()
    return bool((values == derivative_type).any())


def clean_futures(
    df: pd.DataFrame,
    symbol: str | None,
    date_col: str | None,
    time_col: str | None,
    timeframe: str | None,
    futures_expiry: str | None,
) -> pd.DataFrame:
    df = filter_derivative_type(df, "F", "futures")
    clean = build_datetime(df, date_col, time_col)
    clean["datetime"] = clean["datetime"].dt.floor("min")
    if "symbol" not in clean.columns:
        clean["symbol"] = symbol or "NIFTY"
    clean["symbol"] = clean["symbol"].fillna(symbol or "NIFTY")
    if futures_expiry and "expiry" in clean.columns:
        clean = clean[clean["expiry"].astype(str).str.upper() == futures_expiry.upper()].copy()
        if clean.empty:
            raise ValueError(f"No futures rows found for expiry={futures_expiry}")
    clean = normalize_ohlc(clean, FUTURES_REQUIRED, "futures")
    return resample_ohlc(clean, ["symbol"], timeframe) if timeframe else clean


def clean_options(df: pd.DataFrame, symbol: str | None, date_col: str | None, time_col: str | None, timeframe: str | None) -> pd.DataFrame:
    df = filter_derivative_type(df, "O", "options")
    clean = build_datetime(df, date_col, time_col)
    clean["datetime"] = clean["datetime"].dt.floor("min")
    if "symbol" not in clean.columns:
        clean["symbol"] = symbol or "NIFTY"
    clean["symbol"] = clean["symbol"].fillna(symbol or "NIFTY")
    if "option_type" in clean.columns:
        clean["option_type"] = clean["option_type"].astype(str).str.upper().replace({"CALL": "CE", "PUT": "PE"})
    if "expiry" in clean.columns:
        clean["expiry"] = pd.to_datetime(clean["expiry"], errors="coerce").dt.date.astype(str)
    clean = normalize_ohlc(clean, OPTIONS_REQUIRED, "options")
    return resample_ohlc(clean, ["symbol", "expiry", "strike", "option_type"], timeframe) if timeframe else clean


def normalize_ohlc(df: pd.DataFrame, required: list[str], label: str) -> pd.DataFrame:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"{label} data missing required columns: {missing}")
    clean = df[required + [column for column in df.columns if column not in required]].copy()
    clean["datetime"] = pd.to_datetime(clean["datetime"], errors="coerce")
    if clean["datetime"].isna().any():
        raise ValueError(f"{label} data contains invalid datetime values")
    for column in ["open", "high", "low", "close", "volume"]:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
        if clean[column].isna().any():
            raise ValueError(f"{label} column {column} contains invalid numeric values")
    if (clean["high"] < clean["low"]).any():
        raise ValueError(f"{label} data contains high < low rows")
    if "strike" in required:
        clean["strike"] = pd.to_numeric(clean["strike"], errors="coerce")
        if clean["strike"].isna().any():
            raise ValueError("options strike contains invalid numeric values")
    return clean.sort_values("datetime").reset_index(drop=True)


def resample_ohlc(df: pd.DataFrame, group_columns: list[str], timeframe: str | None) -> pd.DataFrame:
    if not timeframe:
        return df
    rule = {"1min": "1min", "1m": "1min", "3min": "3min", "5min": "5min", "15min": "15min"}.get(timeframe.lower(), timeframe)
    optional_columns = [column for column in df.columns if column not in set(group_columns + ["datetime", "open", "high", "low", "close", "volume"])]
    rows = []
    for keys, group in df.groupby(group_columns, dropna=False):
        group = group.sort_values("datetime").set_index("datetime")
        agg = group.resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        agg = agg.dropna(subset=["open", "high", "low", "close"]).reset_index()
        if not isinstance(keys, tuple):
            keys = (keys,)
        for column, value in zip(group_columns, keys):
            agg[column] = value
        for column in optional_columns:
            if column in group.columns:
                extra = group[column].resample(rule).last().reindex(pd.DatetimeIndex(agg["datetime"])).reset_index(drop=True)
                agg[column] = extra.values
        rows.append(agg)
    if not rows:
        return df.iloc[0:0].copy()
    ordered = group_columns + ["datetime", "open", "high", "low", "close", "volume"] + optional_columns
    result = pd.concat(rows, ignore_index=True)
    return result[[column for column in ordered if column in result.columns]].sort_values("datetime").reset_index(drop=True)


def normalize_timeframe(value: str | None) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    if value.lower() in {"", "none", "raw", "no", "false", "off"}:
        return None
    return value


def write_daywise(df: pd.DataFrame, output_root: str | None, output_name: str) -> None:
    if output_root is None:
        output_root = str(Path(__file__).resolve().parents[1] / "DATA")
    root = Path(output_root)
    for day, day_df in df.groupby(df["datetime"].dt.date):
        folder = root / str(day)
        folder.mkdir(parents=True, exist_ok=True)
        output_path = folder / output_name
        day_df.to_csv(output_path, index=False)
        print(f"Wrote {len(day_df)} rows -> {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract raw data into DATA/{Date}/futures.csv and options.csv")
    parser.add_argument("--futures-file", help="Raw futures CSV/Excel/Parquet file")
    parser.add_argument("--options-file", help="Raw options CSV/Excel/Parquet file")
    parser.add_argument("--mixed-file", help="Raw file containing both futures and options. Uses derivative_type F/O to split.")
    parser.add_argument("--futures-sheet", help="Excel sheet name for futures")
    parser.add_argument("--options-sheet", help="Excel sheet name for options")
    parser.add_argument("--futures-mapping", help="JSON mapping: standard_column -> raw_column")
    parser.add_argument("--options-mapping", help="JSON mapping: standard_column -> raw_column")
    parser.add_argument("--date-col", help="Raw date column if datetime is split")
    parser.add_argument("--time-col", help="Raw time column if datetime is split")
    parser.add_argument("--symbol", default="NIFTY")
    parser.add_argument("--output-root", help="Output folder. Default: project_root/DATA")
    parser.add_argument("--timeframe", default="1min", help="Resample output candles. Use empty string to disable. Default: 1min")
    parser.add_argument("--futures-expiry", default="I", help="Futures expiry series to use when raw file contains I/II/III. Default: I")
    args = parser.parse_args()
    args.timeframe = normalize_timeframe(args.timeframe)

    if not args.futures_file and not args.options_file and not args.mixed_file:
        raise ValueError("Provide --futures-file, --options-file, --mixed-file, or a combination.")

    if args.mixed_file:
        mixed = read_table(args.mixed_file)
        mixed = apply_mapping(mixed, load_mapping(args.futures_mapping or args.options_mapping))
        if "derivative_type" not in mixed.columns:
            raise ValueError("--mixed-file requires derivative_type column with F for futures and O for options.")
        if has_derivative_type(mixed, "F"):
            futures = clean_futures(mixed, args.symbol, args.date_col, args.time_col, args.timeframe, args.futures_expiry)
            write_daywise(futures, args.output_root, "futures.csv")
        else:
            print("No derivative_type=F rows found. Skipping futures.csv.")
        if has_derivative_type(mixed, "O"):
            options = clean_options(mixed, args.symbol, args.date_col, args.time_col, args.timeframe)
            write_daywise(options, args.output_root, "options.csv")
        else:
            print("No derivative_type=O rows found. Skipping options.csv.")

    if args.futures_file:
        futures = read_table(args.futures_file, args.futures_sheet)
        futures = apply_mapping(futures, load_mapping(args.futures_mapping))
        futures = clean_futures(futures, args.symbol, args.date_col, args.time_col, args.timeframe, args.futures_expiry)
        write_daywise(futures, args.output_root, "futures.csv")

    if args.options_file:
        options = read_table(args.options_file, args.options_sheet)
        options = apply_mapping(options, load_mapping(args.options_mapping))
        options = clean_options(options, args.symbol, args.date_col, args.time_col, args.timeframe)
        write_daywise(options, args.output_root, "options.csv")


if __name__ == "__main__":
    main()
