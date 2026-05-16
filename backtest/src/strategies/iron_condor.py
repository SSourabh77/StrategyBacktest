from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal


class IronCondorStrategy(BaseStrategy):
    name = "iron_condor"

    def get_parameter_grid(self, config=None):
        return {"wing_width": [100]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        return [make_signal(market_data.iloc[0]["datetime"], SignalType.LONG, "iron_condor_entry", 0.5, wing_width=parameters.get("wing_width", 100))] if not market_data.empty else []
