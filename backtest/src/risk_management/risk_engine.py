from __future__ import annotations

from datetime import datetime

from src.core.trade import Trade


class RiskEngine:
    def __init__(self, risk_config: dict, market_config: dict):
        self.risk_config = risk_config
        self.market_config = market_config

    def can_enter(self, now: datetime, closed_trades: list[Trade]) -> bool:
        max_trades = self.risk_config.get("max_trades_per_day")
        if max_trades is None:
            return True
        todays_trades = [t for t in closed_trades if t.entry_time.date() == now.date()]
        return len(todays_trades) < int(max_trades)

    def check_exit(self, trade: Trade, now: datetime, current_position_value: float) -> str | None:
        square_off = self.risk_config.get("square_off_time")
        if square_off and now.strftime("%H:%M") >= str(square_off):
            return "square_off_time"

        entry_position_value = 0.0
        entry_exposure = 0.0
        for leg in trade.legs:
            direction = 1 if leg.action.upper() == "BUY" else -1
            entry_position_value += leg.entry_price * leg.quantity * direction
            entry_exposure += abs(leg.entry_price * leg.quantity)
        if entry_exposure == 0:
            return None

        unrealized_pnl = current_position_value - entry_position_value
        stop_loss_pct = self.risk_config.get("stop_loss_pct")
        target_pct = self.risk_config.get("target_pct")
        if stop_loss_pct is not None:
            stop_amount = entry_exposure * float(stop_loss_pct) / 100
            if unrealized_pnl <= -stop_amount:
                return "stop_loss"
        if target_pct is not None:
            target_amount = entry_exposure * float(target_pct) / 100
            if unrealized_pnl >= target_amount:
                return "target"
        return None

