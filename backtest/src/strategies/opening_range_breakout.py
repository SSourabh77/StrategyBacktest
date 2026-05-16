from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal


class OpeningRangeBreakoutStrategy(BaseStrategy):
    name = "opening_range_breakout"

    def get_parameter_grid(self, config=None):
        return {"range_minutes": [15, 30]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        df = market_data.copy()
        minutes = int(parameters.get("range_minutes", 15))
        signals = []
        for _, day in df.groupby(df["datetime"].dt.date):
            opening = day.head(minutes)
            if opening.empty:
                continue
            high = opening.high.max()
            low = opening.low.min()
            later = day.iloc[minutes:]
            up = later.close > high
            down = later.close < low
            for idx, row in later.loc[up | down].head(1).iterrows():
                signals.append(make_signal(row.datetime, SignalType.LONG if up.loc[idx] else SignalType.SHORT, "opening_range_breakout", 0.6, range_high=float(high), range_low=float(low)))
        return signals
