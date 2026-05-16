from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal


class OptionGreeksBasedStrategy(BaseStrategy):
    name = "option_greeks_based"

    def get_parameter_grid(self, config=None):
        return {"delta_threshold": [0.3]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        if "delta" not in market_data.columns:
            return []
        threshold = float(parameters.get("delta_threshold", 0.3))
        df = market_data.copy()
        long = df.delta >= threshold
        short = df.delta <= -threshold
        return [make_signal(row.datetime, SignalType.LONG if long.loc[idx] else SignalType.SHORT, "option_greeks_delta_filter", 0.5, delta=float(row.delta)) for idx, row in df.loc[long | short].iterrows()]
