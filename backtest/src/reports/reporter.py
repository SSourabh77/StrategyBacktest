from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.core.trade import Trade


class Reporter:
    def __init__(self, config: dict, results_dir: Path):
        self.config = config
        self.results_dir = results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def trade_rows(self, trades: list[Trade]) -> list[dict]:
        rows = []
        for trade in trades:
            for leg in trade.legs:
                rows.append(
                    {
                        "run_id": trade.run_id,
                        "strategy_name": trade.strategy_name,
                        "parameter_hash": trade.parameter_hash,
                        "entry_time": trade.entry_time,
                        "exit_time": trade.exit_time,
                        "signal": trade.signal,
                        "action": leg.action,
                        "instrument": leg.instrument,
                        "symbol": leg.symbol,
                        "expiry": leg.expiry,
                        "option_type": leg.option_type,
                        "strike": leg.strike,
                        "quantity": leg.quantity,
                        "entry_price": leg.entry_price,
                        "exit_price": leg.exit_price,
                        "gross_pnl": trade.gross_pnl,
                        "charges": trade.charges,
                        "net_pnl": trade.net_pnl,
                        "exit_reason": trade.exit_reason,
                        "metadata": json.dumps(trade.metadata, default=str),
                    }
                )
        return rows

    def write_tradebook(self, trades: list[Trade], filename: str = "tradebook.csv") -> Path:
        rows = self.trade_rows(trades)
        df = pd.DataFrame(rows)
        df = self._select_and_rename(df, "tradebook_columns")
        csv_path = self.results_dir / filename
        df.to_csv(csv_path, index=False)
        if "json" in self.config.get("reports", {}).get("formats", []):
            df.to_json(csv_path.with_suffix(".json"), orient="records", indent=2, date_format="iso")
        return csv_path

    def write_optimization(self, rows: list[dict], filename: str = "optimization_results.csv") -> Path:
        df = pd.DataFrame(rows)
        if not df.empty:
            metric = self.config.get("optimization", {}).get("ranking_metric", "profit_factor")
            if metric in df.columns:
                df = df.sort_values(metric, ascending=False)
        df = self._select_and_rename(df, "optimization_columns")
        csv_path = self.results_dir / filename
        df.to_csv(csv_path, index=False)
        if "json" in self.config.get("reports", {}).get("formats", []):
            df.to_json(csv_path.with_suffix(".json"), orient="records", indent=2)
        return csv_path

    def write_best_parameters(self, rows: list[dict], filename: str = "best_parameters.csv") -> Path:
        df = pd.DataFrame(rows)
        if not df.empty:
            metric = self.config.get("optimization", {}).get("ranking_metric", "profit_factor")
            if metric in df.columns:
                df = df.sort_values(metric, ascending=False)
            df = df.head(1)
        csv_path = self.results_dir / filename
        df.to_csv(csv_path, index=False)
        if "json" in self.config.get("reports", {}).get("formats", []):
            df.to_json(csv_path.with_suffix(".json"), orient="records", indent=2)
        return csv_path

    def write_run_summary(self, summary: dict, filename: str = "run_summary.csv") -> Path:
        df = pd.DataFrame([summary])
        csv_path = self.results_dir / filename
        df.to_csv(csv_path, index=False)
        if "json" in self.config.get("reports", {}).get("formats", []):
            df.to_json(csv_path.with_suffix(".json"), orient="records", indent=2)
        return csv_path

    def _select_and_rename(self, df: pd.DataFrame, column_key: str) -> pd.DataFrame:
        if df.empty:
            return df
        columns = self.config.get("reports", {}).get(column_key, [])
        selected = [col for col in columns if col in df.columns]
        if selected:
            df = df[selected]
        renames = self.config.get("reports", {}).get("column_renames", {})
        return df.rename(columns=renames)

