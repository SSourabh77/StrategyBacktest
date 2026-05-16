from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal


class SupertrendStrategy(BaseStrategy):
    name = "supertrend"

    def get_parameter_grid(self, config: dict[str, Any] | None = None) -> dict[str, list[Any]]:
        return {"atr_period": [10], "multiplier": [2.0, 3.0]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        df = market_data.copy()
        period = int(parameters.get("atr_period", 10))
        multiplier = float(parameters.get("multiplier", 3.0))
        tr = pd.concat([(df.high - df.low), (df.high - df.close.shift()).abs(), (df.low - df.close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(period, min_periods=1).mean()
        mid = (df.high + df.low) / 2
        upper = mid + multiplier * atr
        lower = mid - multiplier * atr
        trend_up = df.close > upper.shift(1)
        trend_down = df.close < lower.shift(1)
        signals = []
        for idx, row in df.loc[trend_up | trend_down].iterrows():
            sig = SignalType.LONG if trend_up.loc[idx] else SignalType.SHORT
            signals.append(make_signal(row["datetime"], sig, "supertrend_flip", 0.6, atr_period=period, multiplier=multiplier))
        return signals
