from __future__ import annotations

from src.core.trade import Trade


def calculate_metrics(trades: list[Trade]) -> dict:
    pnl_values = [trade.net_pnl for trade in trades]
    winning = [p for p in pnl_values if p > 0]
    losing = [p for p in pnl_values if p < 0]
    gross_profit = sum(winning)
    gross_loss = abs(sum(losing))
    total = len(pnl_values)
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for pnl in pnl_values:
        equity += pnl
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity - peak)
    return {
        "total_trades": total,
        "winning_trades": len(winning),
        "losing_trades": len(losing),
        "win_rate": (len(winning) / total * 100) if total else 0.0,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "net_pnl": sum(pnl_values),
        "profit_factor": (gross_profit / gross_loss) if gross_loss else (float("inf") if gross_profit else 0.0),
        "max_drawdown": abs(max_drawdown),
        "expectancy": (sum(pnl_values) / total) if total else 0.0,
    }

