from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.core.trade import Trade


@dataclass
class EquityPoint:
    datetime: datetime
    equity: float
    realized_pnl: float


@dataclass
class Portfolio:
    initial_capital: float = 0.0
    closed_trades: list[Trade] = field(default_factory=list)
    equity_curve: list[EquityPoint] = field(default_factory=list)

    @property
    def realized_pnl(self) -> float:
        return sum(trade.net_pnl for trade in self.closed_trades)

    @property
    def equity(self) -> float:
        return self.initial_capital + self.realized_pnl

    def record_closed_trade(self, trade: Trade) -> None:
        self.closed_trades.append(trade)
        if trade.exit_time is not None:
            self.equity_curve.append(
                EquityPoint(
                    datetime=trade.exit_time,
                    equity=self.equity,
                    realized_pnl=self.realized_pnl,
                )
            )

    def exposure(self) -> float:
        total = 0.0
        for trade in self.closed_trades:
            for leg in trade.legs:
                total += abs(leg.entry_price * leg.quantity)
        return total
