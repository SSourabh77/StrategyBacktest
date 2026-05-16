from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.execution.execution_engine import ExecutionEngine
from src.reports.metrics import calculate_metrics


class BacktestEngine:
    def __init__(self, config: dict[str, Any], run_id: str, results_dir: Path, logs_dir: Path):
        self.config = config
        self.run_id = run_id
        self.results_dir = results_dir
        self.logs_dir = logs_dir

    def run_once(self, futures: pd.DataFrame, options: pd.DataFrame, strategy, parameters: dict, parameter_hash: str, log_file: Path):
        signals = strategy.generate_signals(futures, parameters)
        execution = ExecutionEngine(self.config, self.run_id, strategy.name, parameter_hash, log_file)
        trades = execution.run(futures, options, signals, parameters)
        metrics = calculate_metrics(trades)
        return trades, metrics

