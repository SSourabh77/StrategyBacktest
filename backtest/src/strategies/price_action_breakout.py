from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal


class PriceActionBreakoutStrategy(BaseStrategy):
    name = "price_action_breakout"

    def get_parameter_grid(self, config=None):
        return {"lookback": [5, 20]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        df = market_data.copy()
        lb = int(parameters.get("lookback", 20))
        prev_high = df.high.rolling(lb, min_periods=1).max().shift(1)
        prev_low = df.low.rolling(lb, min_periods=1).min().shift(1)
        up = df.close > prev_high
        down = df.close < prev_low
        return [make_signal(row.datetime, SignalType.LONG if up.loc[idx] else SignalType.SHORT, "price_action_breakout", 0.6, lookback=lb) for idx, row in df.loc[up | down].iterrows()]
