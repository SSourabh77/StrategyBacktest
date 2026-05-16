from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TradeLeg:
    instrument: str
    symbol: str
    action: str
    quantity: int
    entry_price: float
    option_type: str | None = None
    strike: float | None = None
    expiry: str | None = None
    exit_price: float | None = None


@dataclass
class Trade:
    run_id: str
    strategy_name: str
    parameter_hash: str
    entry_time: datetime
    signal: str
    legs: list[TradeLeg]
    metadata: dict[str, Any] = field(default_factory=dict)
    exit_time: datetime | None = None
    exit_reason: str | None = None
    charges: float = 0.0

    @property
    def is_open(self) -> bool:
        return self.exit_time is None

    @property
    def gross_pnl(self) -> float:
        pnl = 0.0
        for leg in self.legs:
            if leg.exit_price is None:
                continue
            direction = 1 if leg.action.upper() == "BUY" else -1
            pnl += (leg.exit_price - leg.entry_price) * leg.quantity * direction
        return pnl

    @property
    def net_pnl(self) -> float:
        return self.gross_pnl - self.charges

