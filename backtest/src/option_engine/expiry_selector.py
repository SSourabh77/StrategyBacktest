from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass(frozen=True)
class ExpirySelection:
    expiry: str
    selector: str
    dte: int


class ExpirySelector:
    def __init__(self, selector: str = "NEAREST", fixed_expiry: str | None = None):
        self.selector = str(selector or "NEAREST").upper()
        self.fixed_expiry = fixed_expiry

    def select(self, trade_time, options: pd.DataFrame, leg_config: dict | None = None) -> ExpirySelection | None:
        if options.empty or "expiry" not in options.columns:
            return None

        selector = str((leg_config or {}).get("expiry_selector", self.selector)).upper()
        fixed_expiry = (leg_config or {}).get("fixed_expiry", self.fixed_expiry)
        trade_date = pd.Timestamp(trade_time).date()
        expiries = self._future_expiries(options, trade_date)
        if not expiries:
            return None

        if selector in {"NEAREST", "WEEKLY"}:
            selected = expiries[0]
        elif selector == "NEXT":
            selected = expiries[1] if len(expiries) > 1 else expiries[0]
        elif selector == "MONTHLY":
            selected = self._monthly_expiry(expiries)
        elif selector in {"SAME_DAY", "DTE_0"}:
            selected = self._closest_dte(expiries, trade_date, 0)
        elif selector.startswith("DTE_"):
            selected = self._closest_dte(expiries, trade_date, int(selector.split("_", 1)[1]))
        elif selector == "FIXED_DATE":
            if not fixed_expiry:
                raise ValueError("FIXED_DATE expiry selector requires fixed_expiry")
            selected_date = pd.Timestamp(fixed_expiry).date()
            selected = selected_date if selected_date in expiries else None
            if selected is None:
                raise ValueError(f"Fixed expiry {fixed_expiry} not found in option data")
        else:
            raise ValueError(f"Unsupported expiry selector: {selector}")

        return ExpirySelection(expiry=selected.isoformat(), selector=selector, dte=(selected - trade_date).days)

    @staticmethod
    def _future_expiries(options: pd.DataFrame, trade_date: date) -> list[date]:
        expiry_values = pd.to_datetime(options["expiry"], errors="coerce").dt.date.dropna().unique()
        return sorted(expiry for expiry in expiry_values if expiry >= trade_date)

    @staticmethod
    def _monthly_expiry(expiries: list[date]) -> date:
        by_month: dict[tuple[int, int], date] = {}
        for expiry in expiries:
            key = (expiry.year, expiry.month)
            by_month[key] = max(expiry, by_month.get(key, expiry))
        first_month = (expiries[0].year, expiries[0].month)
        return by_month[first_month]

    @staticmethod
    def _closest_dte(expiries: list[date], trade_date: date, target_dte: int) -> date:
        return min(expiries, key=lambda expiry: (abs((expiry - trade_date).days - target_dte), expiry))
