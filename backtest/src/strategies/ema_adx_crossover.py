from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.strategy_base import BaseStrategy


def _range_from_config(spec: dict[str, Any]) -> list[Any]:
    if "values" in spec:
        return list(spec["values"])
    start = spec["start"]
    stop = spec["stop"]
    step = spec.get("step", 1)
    values = []
    current = start
    while current <= stop:
        values.append(current)
        current += step
    return values


def _adx(df: pd.DataFrame, period: int) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    atr = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean() / atr
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    return dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


class EmaAdxCrossoverStrategy(BaseStrategy):
    name = "ema_adx_crossover"

    def get_parameter_grid(self, config: dict[str, Any] | None = None) -> dict[str, list[Any]]:
        grid_cfg = (config or {}).get("optimization", {}).get("parameter_grid", {})
        if grid_cfg:
            return {key: _range_from_config(value) for key, value in grid_cfg.items()}
        return {
            "ema_fast": list(range(5, 16)),
            "ema_slow": list(range(18, 51)),
            "adx_period": list(range(10, 21)),
            "adx_threshold": [18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0],
            # FIX 1: removed dead absolute min_ema_distance param entirely
            # FIX 2: kept pct version only; shift() applied in generate_signals
            "min_ema_distance_pct": [0.0],
            "require_adx_rising": [False, True],
        }

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        df = market_data.sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last").copy()
        ema_fast = int(parameters["ema_fast"])
        ema_slow = int(parameters["ema_slow"])
        adx_period = int(parameters["adx_period"])
        adx_threshold = float(parameters["adx_threshold"])
        require_adx_rising = bool(parameters.get("require_adx_rising", False))
        # FIX 1: removed dead min_ema_distance (absolute) — only pct version remains
        min_ema_distance_pct = float(parameters.get("min_ema_distance_pct", 0.0))

        if ema_fast >= ema_slow:
            return []

        df["ema_fast"] = df["close"].ewm(span=ema_fast, adjust=False).mean()
        df["ema_slow"] = df["close"].ewm(span=ema_slow, adjust=False).mean()
        df["adx"] = _adx(df, adx_period)

        # FIX 3: dropna AFTER warmup slice so post-slice NaNs are also caught
        warmup = max(ema_slow, adx_period) + 5
        if len(df) <= warmup:
            return []
        df = df.iloc[warmup:].copy()
        df = df.dropna(subset=["ema_fast", "ema_slow", "adx", "close"]).copy()

        if df.empty:
            return []

        crossed_up = (df["ema_fast"] > df["ema_slow"]) & (df["ema_fast"].shift(1) <= df["ema_slow"].shift(1))
        crossed_down = (df["ema_fast"] < df["ema_slow"]) & (df["ema_fast"].shift(1) >= df["ema_slow"].shift(1))

        strong_trend = df["adx"] >= adx_threshold

        if require_adx_rising:
            strong_trend = strong_trend & (df["adx"] > df["adx"].shift(1))

        
        if min_ema_distance_pct > 0:
            ema_distance_pct = (
                (df["ema_fast"] - df["ema_slow"]).abs()
                / df["ema_slow"].replace(0, np.nan)
            ) * 100
            strong_trend = strong_trend & (ema_distance_pct.shift(1) >= min_ema_distance_pct)

        signals: list[Signal] = []
        for row in df.loc[(crossed_up | crossed_down) & strong_trend].itertuples(index=False):
            signal = SignalType.LONG if getattr(row, "ema_fast") > getattr(row, "ema_slow") else SignalType.SHORT
            strength = max(0.0, min(float(getattr(row, "adx")) / 100.0, 1.0))  # clamped [0, 1]
            signals.append(
                Signal(
                    datetime=getattr(row, "datetime").to_pydatetime(),
                    signal=signal,
                    strength=strength,
                    metadata={
                        "reason": "ema_cross_with_adx_filter",
                        "ema_fast": float(getattr(row, "ema_fast")),
                        "ema_slow": float(getattr(row, "ema_slow")),
                        "adx": float(getattr(row, "adx")),
                    },
                )
            )
        return signals