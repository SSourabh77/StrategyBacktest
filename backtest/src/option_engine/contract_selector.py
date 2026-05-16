from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.option_engine.expiry_selector import ExpirySelector
from src.option_engine.strike_selector import StrikeSelector


@dataclass(frozen=True)
class OptionContract:
    row: Any | None
    symbol: str
    expiry: str | None
    strike: float
    option_type: str
    selector_metadata: dict


class OptionContractSelector:
    def __init__(self, market_config: dict, execution_config: dict):
        self.market_config = market_config
        self.execution_config = execution_config
        self.strike_selector = StrikeSelector(market_config, execution_config.get("strike_selector", "ATM"))
        self.expiry_selector = ExpirySelector(
            execution_config.get("expiry_selector", "NEAREST"),
            execution_config.get("fixed_expiry"),
        )

    def select(
        self,
        trade_time,
        options: pd.DataFrame,
        underlying_price: float,
        signal: str,
        option_type: str,
        leg_config: dict | None = None,
    ) -> OptionContract:
        leg_config = leg_config or {}
        available = self._available_at_time(options, trade_time, option_type)
        expiry_selection = self.expiry_selector.select(trade_time, available, leg_config)
        if expiry_selection is not None:
            available = available[available["expiry"].astype(str) == expiry_selection.expiry]

        strike_selector = StrikeSelector(self.market_config, leg_config.get("strike_selector", self.execution_config.get("strike_selector", "ATM")))
        strike = float(leg_config["strike"]) if "strike" in leg_config else strike_selector.select(underlying_price, signal, available)
        row = self._option_row(available, strike)
        if row is not None and not self._passes_liquidity(row):
            row = None
        return OptionContract(
            row=row,
            symbol=self.market_config.get("symbol", ""),
            expiry=expiry_selection.expiry if expiry_selection else None,
            strike=strike,
            option_type=option_type,
            selector_metadata={
                "expiry_selector": expiry_selection.selector if expiry_selection else None,
                "dte": expiry_selection.dte if expiry_selection else None,
                "strike_selector": leg_config.get("strike_selector", self.execution_config.get("strike_selector", "ATM")),
            },
        )

    def find_existing_row(
        self,
        trade_time,
        options: pd.DataFrame,
        strike: float | None,
        option_type: str | None,
        expiry: str | None = None,
        allow_previous: bool = False,
    ):
        if options.empty or strike is None or option_type is None:
            return None
        time_filter = options["datetime"] <= pd.Timestamp(trade_time) if allow_previous else options["datetime"] == pd.Timestamp(trade_time)
        rows = options[time_filter & (options["strike"] == float(strike)) & (options["option_type"] == option_type)]
        if expiry:
            rows = rows[rows["expiry"].astype(str) == str(expiry)]
        if rows.empty:
            return None
        return rows.sort_values(["datetime", "expiry"]).iloc[-1]

    @staticmethod
    def _available_at_time(options: pd.DataFrame, trade_time, option_type: str) -> pd.DataFrame:
        if options.empty:
            return options
        return options[(options["datetime"] == pd.Timestamp(trade_time)) & (options["option_type"] == option_type)].copy()

    @staticmethod
    def _option_row(options: pd.DataFrame, strike: float):
        rows = options[options["strike"] == float(strike)]
        if rows.empty:
            return None
        return rows.sort_values("expiry").iloc[0]

    def _passes_liquidity(self, row) -> bool:
        min_volume = self.execution_config.get("min_option_volume")
        if min_volume is not None and "volume" in row.index and float(row["volume"]) < float(min_volume):
            return False

        max_spread = self.execution_config.get("max_bid_ask_spread")
        if max_spread is not None and {"bid", "ask"}.issubset(set(row.index)):
            bid = float(row["bid"])
            ask = float(row["ask"])
            if ask - bid > float(max_spread):
                return False
        return True
