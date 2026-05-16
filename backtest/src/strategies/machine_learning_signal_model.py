from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal


class MachineLearningSignalStrategy(BaseStrategy):
    name = "machine_learning_signal_model"

    def get_parameter_grid(self, config=None):
        return {"model_threshold": [0.5]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        if "ml_signal" not in market_data.columns:
            return []
        df = market_data.copy()
        long = df.ml_signal.astype(str).str.upper() == "LONG"
        short = df.ml_signal.astype(str).str.upper() == "SHORT"
        return [make_signal(row.datetime, SignalType.LONG if long.loc[idx] else SignalType.SHORT, "external_ml_signal", 0.5) for idx, row in df.loc[long | short].iterrows()]
