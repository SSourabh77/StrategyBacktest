from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal, rsi


class RsiMeanReversionStrategy(BaseStrategy):
    name = "rsi_mean_reversion"

    def get_parameter_grid(self, config=None):
        return {"rsi_period": [14], "oversold": [30], "overbought": [70]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        df = market_data.copy()
        values = rsi(df.close, int(parameters.get("rsi_period", 14)))
        long = (values < float(parameters.get("oversold", 30))) & (values.shift(1) >= float(parameters.get("oversold", 30)))
        short = (values > float(parameters.get("overbought", 70))) & (values.shift(1) <= float(parameters.get("overbought", 70)))
        return [make_signal(row.datetime, SignalType.LONG if long.loc[idx] else SignalType.SHORT, "rsi_mean_reversion", 0.5, rsi=float(values.loc[idx])) for idx, row in df.loc[long | short].iterrows()]
