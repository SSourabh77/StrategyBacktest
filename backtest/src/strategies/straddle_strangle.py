from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal


class StraddleStrangleStrategy(BaseStrategy):
    name = "straddle_strangle"

    def get_parameter_grid(self, config=None):
        return {"structure": ["straddle", "strangle"]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        return [make_signal(market_data.iloc[0]["datetime"], SignalType.LONG, "option_volatility_structure_entry", 0.5, structure=parameters.get("structure", "straddle"))] if not market_data.empty else []
