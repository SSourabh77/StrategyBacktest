from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal


class DeltaNeutralStrategy(BaseStrategy):
    name = "delta_neutral"

    def get_parameter_grid(self, config=None):
        return {"delta_band": [0.1]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        return [make_signal(market_data.iloc[0]["datetime"], SignalType.LONG, "delta_neutral_structure_entry", 0.5, structure="hedged_delta_neutral")] if not market_data.empty else []
