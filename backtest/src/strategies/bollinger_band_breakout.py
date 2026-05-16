from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal


class BollingerBandBreakoutStrategy(BaseStrategy):
    name = "bollinger_band_breakout"

    def get_parameter_grid(self, config=None):
        return {"period": [20], "std_dev": [2.0]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        df = market_data.copy()
        period = int(parameters.get("period", 20))
        mult = float(parameters.get("std_dev", 2.0))
        ma = df.close.rolling(period, min_periods=1).mean()
        std = df.close.rolling(period, min_periods=1).std().fillna(0)
        upper = ma + mult * std
        lower = ma - mult * std
        up = (df.close > upper) & (df.close.shift(1) <= upper.shift(1))
        down = (df.close < lower) & (df.close.shift(1) >= lower.shift(1))
        return [make_signal(row.datetime, SignalType.LONG if up.loc[idx] else SignalType.SHORT, "bollinger_band_breakout", 0.55) for idx, row in df.loc[up | down].iterrows()]
