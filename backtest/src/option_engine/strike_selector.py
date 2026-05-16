from __future__ import annotations

import pandas as pd


class StrikeSelector:
    def __init__(self, market_config: dict, selector: str = "ATM"):
        self.market_config = market_config
        self.selector = selector.upper()

    def select(self, underlying_price: float, signal: str, options: pd.DataFrame) -> float:
        step = float(self.market_config.get("strike_step", 50))
        atm = round(underlying_price / step) * step
        if self.selector == "ATM":
            return atm
        if self.selector.startswith("OTM"):
            distance = self._distance()
            return atm + distance if signal == "LONG" else atm - distance
        if self.selector.startswith("ITM"):
            distance = self._distance()
            return atm - distance if signal == "LONG" else atm + distance
        if self.selector.startswith("FIXED_DISTANCE_"):
            distance = self._distance()
            return atm + distance if signal == "LONG" else atm - distance
        if self.selector.startswith("PREMIUM_"):
            target = float(self.selector.split("_", 1)[1])
            return self._closest_premium(options, target)
        raise ValueError(f"Unsupported strike selector: {self.selector}")

    def _distance(self) -> float:
        parts = self.selector.split("_")
        if len(parts) >= 2 and parts[-1].replace(".", "", 1).isdigit():
            return float(parts[-1])
        return float(self.market_config.get("strike_step", 50))

    @staticmethod
    def _closest_premium(options: pd.DataFrame, target: float) -> float:
        if options.empty:
            raise ValueError("Cannot select premium-based strike without option data")
        idx = (options["close"] - target).abs().idxmin()
        return float(options.loc[idx, "strike"])
