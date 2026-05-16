from __future__ import annotations

import hashlib
import json
from itertools import product
from pathlib import Path
from typing import Any

import pandas as pd

from src.core.engine import BacktestEngine


def parameter_hash(parameters: dict[str, Any]) -> str:
    raw = json.dumps(parameters, sort_keys=True)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def parameter_file_name(parameters: dict[str, Any]) -> str:
    parts = [f"{key}_{str(value).replace('.', 'p')}" for key, value in sorted(parameters.items())]
    return "__".join(parts)


class Optimizer:
    def __init__(self, config: dict, run_id: str, results_dir: Path, logs_dir: Path):
        self.config = config
        self.run_id = run_id
        self.results_dir = results_dir
        self.logs_dir = logs_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def parameter_combinations(self, grid: dict[str, list[Any]]) -> list[dict[str, Any]]:
        keys = list(grid)
        return [dict(zip(keys, values)) for values in product(*(grid[key] for key in keys))]

    def run(self, futures: pd.DataFrame, options: pd.DataFrame, strategy) -> tuple[list[dict], list, dict]:
        rows: list[dict] = []
        all_trades = []
        combinations = self.parameter_combinations(strategy.get_parameter_grid(self.config))
        completed = self._completed_hashes()
        skipped = 0
        for parameters in combinations:
            p_hash = parameter_hash(parameters)
            if self.config.get("optimization", {}).get("resume", True) and p_hash in completed:
                skipped += 1
                continue
            log_file = self.logs_dir / "trades" / f"{parameter_file_name(parameters)}.log"
            engine = BacktestEngine(self.config, self.run_id, self.results_dir, self.logs_dir)
            trades, metrics = engine.run_once(futures, options, strategy, parameters, p_hash, log_file)
            all_trades.extend(trades)
            row = {
                "run_id": self.run_id,
                "strategy_name": strategy.name,
                "parameter_hash": p_hash,
                "parameters": json.dumps(parameters, sort_keys=True),
                **metrics,
            }
            rows.append(row)
            self._append_completed(row)
        stats = {
            "total_combinations_planned": len(combinations),
            "completed_this_run": len(rows),
            "skipped_existing": skipped,
            "total_combinations_tested": len(rows) + skipped,
        }
        return rows, all_trades, stats

    def _progress_file(self) -> Path:
        return self.results_dir / "optimization_progress.csv"

    def _completed_hashes(self) -> set[str]:
        path = self._progress_file()
        if not path.exists():
            return set()
        df = pd.read_csv(path)
        if "parameter_hash" not in df.columns:
            return set()
        return set(df["parameter_hash"].astype(str))

    def _append_completed(self, row: dict) -> None:
        path = self._progress_file()
        header = not path.exists()
        pd.DataFrame([row]).to_csv(path, mode="a", index=False, header=header)

