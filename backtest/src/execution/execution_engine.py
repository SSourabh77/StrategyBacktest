from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.core.signals import Signal, SignalType
from src.core.trade import Trade, TradeLeg
from src.option_engine.contract_selector import OptionContractSelector
from src.portfolio.portfolio import Portfolio
from src.risk_management.risk_engine import RiskEngine


class ExecutionEngine:
    def __init__(self, config: dict[str, Any], run_id: str, strategy_name: str, parameter_hash: str, log_file: Path):
        self.config = config
        self.run_id = run_id
        self.strategy_name = strategy_name
        self.parameter_hash = parameter_hash
        self.log_file = log_file
        self.risk = RiskEngine(config.get("risk", {}), config.get("market", {}))
        self.contract_selector = OptionContractSelector(config.get("market", {}), config.get("execution", {}))

    def run(self, futures: pd.DataFrame, options: pd.DataFrame, signals: list[Signal], parameters: dict[str, Any]) -> list[Trade]:
        signal_by_time = {pd.Timestamp(s.datetime): s for s in signals}
        delay = int(self.config.get("execution", {}).get("signal_execution_delay_bars", 1))
        trades: list[Trade] = []
        portfolio = Portfolio(initial_capital=float(self.config.get("portfolio", {}).get("initial_capital", 0.0)))
        open_trade: Trade | None = None
        pending_signal: Signal | None = None
        pending_delay = 0

        self._log(f"PARAMETERS {parameters}")
        for row in futures.itertuples(index=False):
            now = getattr(row, "datetime")
            price = float(getattr(row, self.config.get("execution", {}).get("price_column", "close")))

            if open_trade:
                current_trade_price = self._current_trade_price(open_trade, now, options, price)
                exit_reason = self.risk.check_exit(open_trade, now, current_trade_price)
                opposite = signal_by_time.get(pd.Timestamp(now))
                if opposite and self._is_opposite(open_trade.signal, opposite.signal.value):
                    exit_reason = "opposite_signal"
                if exit_reason:
                    self._close_trade(open_trade, now, options, price, exit_reason)
                    trades.append(open_trade)
                    portfolio.record_closed_trade(open_trade)
                    open_trade = None

            if pd.Timestamp(now) in signal_by_time:
                current_signal = signal_by_time[pd.Timestamp(now)]
                if current_signal.signal in {SignalType.LONG, SignalType.SHORT}:
                    pending_signal = current_signal
                    pending_delay = delay
                    self._log(f"SIGNAL {now} {current_signal.signal.value} strength={current_signal.strength} metadata={current_signal.metadata}")

            if pending_signal:
                if pending_delay > 0:
                    pending_delay -= 1
                elif open_trade is None and self.risk.can_enter(now, trades):
                    open_trade = self._open_trade(pending_signal, now, row, options, price, parameters)
                    pending_signal = None

        if open_trade:
            last = futures.iloc[-1]
            self._close_trade(open_trade, last["datetime"], options, float(last["close"]), "end_of_data")
            trades.append(open_trade)
            portfolio.record_closed_trade(open_trade)
        return trades

    def _open_trade(self, signal: Signal, now: datetime, future_row: Any, options: pd.DataFrame, underlying_price: float, parameters: dict[str, Any]) -> Trade:
        execution_cfg = self.config.get("execution", {})
        market_cfg = self.config.get("market", {})
        quantity = int(execution_cfg.get("quantity_lots", 1)) * int(market_cfg.get("lot_size", 1))
        legs = self._build_legs(signal, now, future_row, options, underlying_price, quantity)
        trade = Trade(
            run_id=self.run_id,
            strategy_name=self.strategy_name,
            parameter_hash=self.parameter_hash,
            entry_time=now,
            signal=signal.signal.value,
            legs=legs,
            metadata={"signal_metadata": signal.metadata, "parameters": parameters},
        )
        for leg in legs:
            self._log(f"OPEN {now} instrument={leg.instrument} action={leg.action} option_type={leg.option_type} strike={leg.strike} price={leg.entry_price} qty={leg.quantity}")
        return trade

    def _build_legs(self, signal: Signal, now: datetime, future_row: Any, options: pd.DataFrame, underlying_price: float, quantity: int) -> list[TradeLeg]:
        execution_cfg = self.config.get("execution", {})
        market_cfg = self.config.get("market", {})
        symbol = market_cfg.get("symbol", getattr(future_row, "symbol", ""))
        instrument = execution_cfg.get("instrument", "OPTIONS").upper()
        mode = execution_cfg.get("mode", "BUY").upper()
        if instrument == "FUTURES":
            action = "BUY" if signal.signal == SignalType.LONG else "SELL"
            return [TradeLeg(instrument="FUTURES", symbol=symbol, action=action, quantity=quantity, entry_price=underlying_price)]

        if instrument == "SYNTHETIC_FUTURES":
            atm = self._selected_strike(now, options, underlying_price, signal.signal.value, "CE")
            if signal.signal == SignalType.LONG:
                return [self._option_leg(now, options, symbol, "BUY", "CE", atm, quantity, underlying_price), self._option_leg(now, options, symbol, "SELL", "PE", atm, quantity, underlying_price)]
            return [self._option_leg(now, options, symbol, "SELL", "CE", atm, quantity, underlying_price), self._option_leg(now, options, symbol, "BUY", "PE", atm, quantity, underlying_price)]

        if instrument in {"MULTI_LEG_OPTIONS", "HEDGED", "SPREAD"}:
            return self._multi_leg_plan(signal, now, options, symbol, underlying_price, quantity, instrument)

        option_type = "CE" if signal.signal == SignalType.LONG else "PE"
        strike = self._selected_strike(now, options, underlying_price, signal.signal.value, option_type)
        action = "SELL" if mode == "SELL" else "BUY"
        return [self._option_leg(now, options, symbol, action, option_type, strike, quantity, underlying_price)]

    def _multi_leg_plan(self, signal: Signal, now: datetime, options: pd.DataFrame, symbol: str, underlying_price: float, quantity: int, instrument: str) -> list[TradeLeg]:
        step = float(self.config.get("market", {}).get("strike_step", 50))
        atm = self._selected_strike(now, options, underlying_price, signal.signal.value, "CE")
        strategy_name = self.strategy_name
        structure = str(signal.metadata.get("structure", "")).lower()
        if strategy_name == "iron_condor":
            width = float(signal.metadata.get("wing_width", step * 2))
            return [
                self._option_leg(now, options, symbol, "SELL", "PE", atm - step, quantity, underlying_price),
                self._option_leg(now, options, symbol, "BUY", "PE", atm - step - width, quantity, underlying_price),
                self._option_leg(now, options, symbol, "SELL", "CE", atm + step, quantity, underlying_price),
                self._option_leg(now, options, symbol, "BUY", "CE", atm + step + width, quantity, underlying_price),
            ]
        if strategy_name == "calendar_spread":
            return [
                self._option_leg(now, options, symbol, "SELL", "CE", atm, quantity, underlying_price, {"expiry_selector": "NEAREST"}),
                self._option_leg(now, options, symbol, "BUY", "CE", atm, quantity, underlying_price, {"expiry_selector": "NEXT"}),
            ]
        if "strangle" in structure:
            return [
                self._option_leg(now, options, symbol, "BUY", "CE", atm + step, quantity, underlying_price),
                self._option_leg(now, options, symbol, "BUY", "PE", atm - step, quantity, underlying_price),
            ]
        if instrument == "HEDGED":
            option_type = "CE" if signal.signal == SignalType.LONG else "PE"
            hedge_type = "PE" if signal.signal == SignalType.LONG else "CE"
            return [
                self._option_leg(now, options, symbol, "BUY", option_type, atm, quantity, underlying_price),
                self._option_leg(now, options, symbol, "BUY", hedge_type, atm - step if hedge_type == "PE" else atm + step, quantity, underlying_price),
            ]
        if instrument == "SPREAD":
            option_type = "CE" if signal.signal == SignalType.LONG else "PE"
            return [
                self._option_leg(now, options, symbol, "BUY", option_type, atm, quantity, underlying_price),
                self._option_leg(now, options, symbol, "SELL", option_type, atm + step if option_type == "CE" else atm - step, quantity, underlying_price),
            ]
        return [
            self._option_leg(now, options, symbol, "BUY", "CE", atm, quantity, underlying_price),
            self._option_leg(now, options, symbol, "BUY", "PE", atm, quantity, underlying_price),
        ]

    def _option_leg(
        self,
        now: datetime,
        options: pd.DataFrame,
        symbol: str,
        action: str,
        option_type: str,
        strike: float,
        quantity: int,
        underlying_price: float,
        leg_config: dict | None = None,
    ) -> TradeLeg:
        leg_config = {"strike": strike, **(leg_config or {})}
        contract = self.contract_selector.select(now, options, underlying_price, "LONG" if option_type == "CE" else "SHORT", option_type, leg_config)
        option_row = contract.row
        if option_row is None and not self.config.get("execution", {}).get("allow_missing_option_price", False):
            raise ValueError(
                "Missing option entry price. "
                f"time={now}, symbol={symbol}, expiry={contract.expiry}, "
                f"strike={contract.strike}, option_type={option_type}. "
                "Load matching options data or change execution.allow_missing_option_price only for smoke testing."
            )
        entry_price = self._price_or_raise(option_row, underlying_price, "entry")
        return TradeLeg(
            instrument="OPTIONS",
            symbol=symbol,
            action=action,
            quantity=quantity,
            entry_price=entry_price,
            option_type=option_type,
            strike=contract.strike,
            expiry=contract.expiry or (str(option_row["expiry"]) if option_row is not None else None),
        )

    def _close_trade(self, trade: Trade, now: datetime, options: pd.DataFrame, underlying_price: float, reason: str) -> None:
        charges = 0.0
        for leg in trade.legs:
            if leg.instrument == "FUTURES":
                leg.exit_price = underlying_price
            else:
                option_row = self.contract_selector.find_existing_row(options=options, trade_time=now, strike=leg.strike, option_type=leg.option_type, expiry=leg.expiry, allow_previous=True)
                leg.exit_price = self._price_or_raise(option_row, underlying_price, "exit")
            charges += float(self.config.get("execution", {}).get("charges_per_order", 0.0)) * 2
            self._log(f"CLOSE {now} action={leg.action} option_type={leg.option_type} strike={leg.strike} price={leg.exit_price} reason={reason}")
        trade.exit_time = now
        trade.exit_reason = reason
        trade.charges = charges
        self._log(f"PNL gross={trade.gross_pnl:.2f} charges={trade.charges:.2f} net={trade.net_pnl:.2f}")

    def _selected_strike(self, now: datetime, options: pd.DataFrame, underlying_price: float, signal: str, option_type: str) -> float:
        contract = self.contract_selector.select(now, options, underlying_price, signal, option_type)
        return contract.strike

    def _price_or_raise(self, option_row, underlying_price: float, phase: str) -> float:
        if option_row is not None:
            price = float(option_row[self.config.get("execution", {}).get("price_column", "close")])
            slip = float(self.config.get("execution", {}).get("slippage_points", 0.0))
            if phase == "mark":
                return price
            return price + slip if phase == "entry" else price - slip
        if self.config.get("execution", {}).get("allow_missing_option_price", False):
            return underlying_price
        raise ValueError(f"Missing option price for {phase}. Provide options data or enable allow_missing_option_price.")

    def _current_trade_price(self, trade: Trade, now: datetime, options: pd.DataFrame, underlying_price: float) -> float:
        current_position_value = 0.0
        for leg in trade.legs:
            direction = 1 if leg.action.upper() == "BUY" else -1
            if leg.instrument == "FUTURES":
                mark_price = underlying_price
            else:
                option_row = self.contract_selector.find_existing_row(options=options, trade_time=now, strike=leg.strike, option_type=leg.option_type, expiry=leg.expiry, allow_previous=True)
                mark_price = self._price_or_raise(option_row, underlying_price, "mark")
            current_position_value += mark_price * leg.quantity * direction
        return current_position_value

    @staticmethod
    def _is_opposite(open_signal: str, new_signal: str) -> bool:
        return (open_signal == "LONG" and new_signal == "SHORT") or (open_signal == "SHORT" and new_signal == "LONG")

    def _log(self, message: str) -> None:
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")

