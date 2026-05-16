from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.engine import BacktestEngine
from src.core.signals import Signal
from src.data_providers.base import DataRequest
from src.data_providers.registry import get_data_provider
from src.registries.strategy_registry import STRATEGY_REGISTRY
from src.utils.config import load_config


def first_params(strategy, config):
    grid = strategy.get_parameter_grid(config)
    return {key: values[0] for key, values in grid.items()}


def main() -> None:
    config = load_config("config/backtest_config.json")
    config["execution"]["allow_missing_option_price"] = True
    config["data"]["start_date"] = config["data"]["end_date"]
    provider = get_data_provider(config)
    request = DataRequest(
        symbol=config["market"]["symbol"],
        start_date=config["data"]["start_date"],
        end_date=config["data"]["end_date"],
        config=config,
    )
    futures = provider.load_futures(request)
    options = provider.load_options(request)

    strategy_results = []
    for name, strategy_cls in sorted(STRATEGY_REGISTRY.items()):
        strategy = strategy_cls()
        params = first_params(strategy, config)
        signals = strategy.generate_signals(futures, params)
        assert isinstance(signals, list), f"{name} must return list"
        assert all(isinstance(signal, Signal) for signal in signals), f"{name} must return Signal objects"
        strategy_results.append((name, len(signals)))

    execution_cases = [
        ("futures_trading", {"instrument": "FUTURES", "mode": "BUY"}),
        ("options_buying", {"instrument": "OPTIONS", "mode": "BUY"}),
        ("options_selling", {"instrument": "OPTIONS", "mode": "SELL"}),
        ("options_next_expiry", {"instrument": "OPTIONS", "mode": "BUY", "expiry_selector": "NEXT"}),
        ("options_dte_7_expiry", {"instrument": "OPTIONS", "mode": "BUY", "expiry_selector": "DTE_7"}),
        ("multi_leg_option_strategies", {"instrument": "MULTI_LEG_OPTIONS", "mode": "BUY"}),
        ("synthetic_futures", {"instrument": "SYNTHETIC_FUTURES", "mode": "BUY"}),
        ("hedged_positions", {"instrument": "HEDGED", "mode": "BUY"}),
        ("spread_strategies", {"instrument": "SPREAD", "mode": "BUY"}),
    ]
    ema = STRATEGY_REGISTRY["ema_adx_crossover"]()
    params = first_params(ema, config)
    execution_results = []
    for case_name, execution_config in execution_cases:
        case_config = deepcopy(config)
        case_config["execution"].update(execution_config)
        engine = BacktestEngine(case_config, "smoke", Path("results") / "smoke", Path("logs") / "smoke")
        trades, metrics = engine.run_once(futures, options, ema, params, case_name, Path("logs") / "smoke" / f"{case_name}.log")
        execution_results.append((case_name, len(trades), metrics["total_trades"]))

    print("STRATEGY_SMOKE")
    for name, count in strategy_results:
        print(f"{name}: signals={count}")
    print("EXECUTION_SMOKE")
    for name, trade_count, total_trades in execution_results:
        print(f"{name}: trades={trade_count}, metrics_total={total_trades}")


if __name__ == "__main__":
    main()

