import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy


class SmaCrossoverStrategy(BaseStrategy):
    name = "sma_crossover"

    def get_parameter_grid(self, config=None):
        return {"sma_fast": [5, 10], "sma_slow": [20, 30]}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict) -> list[Signal]:
        df = market_data.copy()
        df["sma_fast"] = df["close"].rolling(int(parameters["sma_fast"])).mean()
        df["sma_slow"] = df["close"].rolling(int(parameters["sma_slow"])).mean()
        crossed_up = (df["sma_fast"] > df["sma_slow"]) & (df["sma_fast"].shift(1) <= df["sma_slow"].shift(1))
        crossed_down = (df["sma_fast"] < df["sma_slow"]) & (df["sma_fast"].shift(1) >= df["sma_slow"].shift(1))
        signals = []
        for row in df.loc[crossed_up | crossed_down].itertuples(index=False):
            signal = SignalType.LONG if row.sma_fast > row.sma_slow else SignalType.SHORT
            signals.append(Signal(datetime=row.datetime.to_pydatetime(), signal=signal, metadata={"reason": "sma_cross"}))
        return signals

