from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.signals import Signal


class BaseStrategy:
    name = "base"

    def get_parameter_grid(self, config: dict[str, Any] | None = None) -> dict[str, list[Any]]:
        return {}

    def generate_signals(self, market_data: pd.DataFrame, parameters: dict[str, Any]) -> list[Signal]:
        raise NotImplementedError
