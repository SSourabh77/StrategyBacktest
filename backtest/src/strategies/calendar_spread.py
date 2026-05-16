from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal


class CalendarSpreadStrategy(BaseStrategy):
    name = "calendar_spread"

    def get_parameter_grid(self, config=None):
        return {"near_far_gap_days": [7]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        return [make_signal(market_data.iloc[0]["datetime"], SignalType.LONG, "calendar_spread_entry", 0.5, gap_days=parameters.get("near_far_gap_days", 7))] if not market_data.empty else []
