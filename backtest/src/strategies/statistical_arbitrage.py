from __future__ import annotations

import math
from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal


class StatisticalArbitrageStrategy(BaseStrategy):
    name = "statistical_arbitrage"

    def get_parameter_grid(self, config=None):
        return {"zscore_threshold": [2.0]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        df = market_data.copy()
        spread = df.close - df.close.rolling(20, min_periods=1).mean()
        z = spread / spread.rolling(20, min_periods=1).std().replace(0, math.nan)
        long = z < -float(parameters.get("zscore_threshold", 2.0))
        short = z > float(parameters.get("zscore_threshold", 2.0))
        return [make_signal(row.datetime, SignalType.LONG if long.loc[idx] else SignalType.SHORT, "statistical_arbitrage_zscore", 0.5, zscore=float(z.loc[idx])) for idx, row in df.loc[long | short].iterrows()]
