from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy
from src.strategy_helpers.technical import make_signal


class GammaScalpingStrategy(BaseStrategy):
    name = "gamma_scalping"

    def get_parameter_grid(self, config=None):
        return {"rebalance_move_pct": [0.3]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        df = market_data.copy()
        move = df.close.pct_change().abs() * 100
        trigger = move >= float(parameters.get("rebalance_move_pct", 0.3))
        return [make_signal(row.datetime, SignalType.LONG, "gamma_scalping_rebalance", 0.5, move_pct=float(move.loc[idx])) for idx, row in df.loc[trigger].iterrows()]
