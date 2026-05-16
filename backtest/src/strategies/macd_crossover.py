from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal


class MacdCrossoverStrategy(BaseStrategy):
    name = "macd_crossover"

    def get_parameter_grid(self, config=None):
        return {"fast": [12], "slow": [26], "signal_period": [9]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        df = market_data.copy()
        fast = df.close.ewm(span=int(parameters.get("fast", 12)), adjust=False).mean()
        slow = df.close.ewm(span=int(parameters.get("slow", 26)), adjust=False).mean()
        macd = fast - slow
        sig_line = macd.ewm(span=int(parameters.get("signal_period", 9)), adjust=False).mean()
        up = (macd > sig_line) & (macd.shift(1) <= sig_line.shift(1))
        down = (macd < sig_line) & (macd.shift(1) >= sig_line.shift(1))
        return [make_signal(row.datetime, SignalType.LONG if up.loc[idx] else SignalType.SHORT, "macd_crossover", 0.55, macd=float(macd.loc[idx])) for idx, row in df.loc[up | down].iterrows()]
