from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal


class VwapBreakoutStrategy(BaseStrategy):
    name = "vwap_breakout"

    def get_parameter_grid(self, config=None):
        return {"buffer_pct": [0.0, 0.1]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        df = market_data.copy()
        typical = (df.high + df.low + df.close) / 3
        volume = df.volume.replace(0, 1)
        df["vwap"] = (typical * volume).cumsum() / volume.cumsum()
        buffer = float(parameters.get("buffer_pct", 0.0)) / 100
        up = (df.close > df.vwap * (1 + buffer)) & (df.close.shift(1) <= df.vwap.shift(1))
        down = (df.close < df.vwap * (1 - buffer)) & (df.close.shift(1) >= df.vwap.shift(1))
        return [make_signal(row.datetime, SignalType.LONG if up.loc[idx] else SignalType.SHORT, "vwap_breakout", 0.55, vwap=float(row.vwap)) for idx, row in df.loc[up | down].iterrows()]
