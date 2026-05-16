from __future__ import annotations

import math

import pandas as pd

from src.core.signals import Signal, SignalType


def make_signal(dt, signal: SignalType, reason: str, strength: float | None = None, **metadata) -> Signal:
    metadata["reason"] = reason
    return Signal(datetime=pd.Timestamp(dt).to_pydatetime(), signal=signal, strength=strength, metadata=metadata)


def rsi(close: pd.Series, period: int) -> pd.Series:
    diff = close.diff()
    gain = diff.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-diff.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, math.nan)
    return (100 - (100 / (1 + rs))).fillna(50)
