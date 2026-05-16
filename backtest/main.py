from __future__ import annotations

import argparse
from pathlib import Path

from src.core.engine import BacktestEngine
from src.data_providers.base import DataRequest
from src.data_providers.registry import get_data_provider
from src.optimization.optimizer import Optimizer, parameter_hash, parameter_file_name
from src.reports.reporter import Reporter
from src.registries.strategy_registry import get_strategy
from src.utils.config import load_config
from src.utils.run_id import make_run_id


def load_market_data(config: dict):
    provider = get_data_provider(config)
    request = DataRequest(
        symbol=config["market"]["symbol"],
        start_date=config["data"]["start_date"],
        end_date=config["data"]["end_date"],
        config=config,
    )
    futures = provider.load_futures(request)
    options = provider.load_options(request)
    return futures, options


def dry_run(config: dict) -> None:
    strategy = get_strategy(config["strategy"]["name"])
    futures, options = load_market_data(config)
    grid = strategy.get_parameter_grid(config)
    print("Dry run successful")
    print(f"Strategy: {strategy.name}")
    print(f"Futures rows: {len(futures)}")
    print(f"Options rows: {len(options)}")
    print(f"Parameter keys: {list(grid)}")
    print(f"Data provider: {config['data'].get('provider')}")


def run_single(config: dict) -> None:
    run_id = make_run_id()
    strategy = get_strategy(config["strategy"]["name"])
    results_dir = Path("results") / strategy.name / run_id
    logs_dir = Path("logs") / strategy.name / run_id
    futures, options = load_market_data(config)
    parameters = config["strategy"].get("parameters", {})
    p_hash = parameter_hash(parameters)
    log_file = logs_dir / "trades" / f"{parameter_file_name(parameters)}.log"
    engine = BacktestEngine(config, run_id, results_dir, logs_dir)
    trades, metrics = engine.run_once(futures, options, strategy, parameters, p_hash, log_file)
    reporter = Reporter(config, results_dir)
    reporter.write_tradebook(trades)
    rows = [{**metrics, "run_id": run_id, "strategy_name": strategy.name, "parameter_hash": p_hash, "parameters": str(parameters)}]
    reporter.write_optimization(rows)
    reporter.write_best_parameters(rows)
    reporter.write_run_summary(
        {
            "run_id": run_id,
            "strategy_name": strategy.name,
            "mode": "single",
            "ranking_metric": config.get("optimization", {}).get("ranking_metric", "profit_factor"),
            "total_combinations_planned": 1,
            "completed_this_run": 1,
            "skipped_existing": 0,
            "total_combinations_tested": 1,
            "best_parameter_hash": p_hash,
            "best_parameters": str(parameters),
            **metrics,
        }
    )
    print(f"Run complete: {run_id}")
    print("Combinations tested: 1")
    print(f"Results: {results_dir}")
    print(f"Logs: {logs_dir}")


def optimize(config: dict) -> None:
    run_id = make_run_id()
    strategy = get_strategy(config["strategy"]["name"])
    results_dir = Path("results") / strategy.name / run_id
    logs_dir = Path("logs") / strategy.name / run_id
    futures, options = load_market_data(config)
    optimizer = Optimizer(config, run_id, results_dir, logs_dir)
    rows, trades, stats = optimizer.run(futures, options, strategy)
    reporter = Reporter(config, results_dir)
    reporter.write_tradebook(trades)
    reporter.write_optimization(rows)
    reporter.write_best_parameters(rows)
    best = _best_row(config, rows)
    reporter.write_run_summary(
        {
            "run_id": run_id,
            "strategy_name": strategy.name,
            "mode": "optimize",
            "ranking_metric": config.get("optimization", {}).get("ranking_metric", "profit_factor"),
            **stats,
            "best_parameter_hash": best.get("parameter_hash") if best else "",
            "best_parameters": best.get("parameters") if best else "",
            "best_net_pnl": best.get("net_pnl") if best else "",
            "best_profit_factor": best.get("profit_factor") if best else "",
            "best_win_rate": best.get("win_rate") if best else "",
        }
    )
    print(f"Optimization complete: {run_id}")
    print(f"Total combinations planned: {stats['total_combinations_planned']}")
    print(f"Combinations completed this run: {stats['completed_this_run']}")
    print(f"Combinations skipped from resume: {stats['skipped_existing']}")
    print(f"Total combinations tested: {stats['total_combinations_tested']}")
    if best:
        print(f"Best parameter hash: {best.get('parameter_hash')}")
        print(f"Best parameters: {best.get('parameters')}")
    print(f"Results: {results_dir}")
    print(f"Logs: {logs_dir}")


def _best_row(config: dict, rows: list[dict]) -> dict:
    if not rows:
        return {}
    metric = config.get("optimization", {}).get("ranking_metric", "profit_factor")
    return sorted(rows, key=lambda row: row.get(metric, float("-inf")), reverse=True)[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Strategy-independent futures/options backtesting framework")
    parser.add_argument("command", choices=["dry-run", "run", "optimize"])
    parser.add_argument("--config", default="config/backtest_config.json")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config(args.config)
    if args.command == "dry-run":
        dry_run(config)
    elif args.command == "run":
        run_single(config)
    elif args.command == "optimize":
        optimize(config)


if __name__ == "__main__":
    main()

