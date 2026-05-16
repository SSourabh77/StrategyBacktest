# Project Structure

This project is organized so the engine is independent from strategy, data source, execution style, risk rules, and reports.

```text
backtest/
  main.py
  requirements.txt
  README.md

  config/
    backtest_config.json
    backtest_config.yaml

  DATA/
    2026-05-15/
      futures.csv
      options.csv

  src/
    core/
    data_providers/
    registries/
    strategies/
    strategy_helpers/
    execution/
    option_engine/
    portfolio/
    risk_management/
    optimization/
    reports/
    utils/

  custom_providers/
    sample_custom_provider.py

  example_files/
    futures_sample.csv
    options_sample.csv

  tests/
    smoke_all_requirements.py
    test_core.py

  scripts/
    run_dry_run.bat
    run_single.bat
    run_optimize.bat

  docs/
    DATA_CONTRACT.md
    PROJECT_STRUCTURE.md

  logs/
  results/
```

## What Each Folder Means

`config/`
Stores runtime settings. Change strategy name, data provider, execution mode, risk rules, optimization grid, and report columns here.

`DATA/`
Default CSV data location. The current format is:

```text
DATA/{Date}/futures.csv
DATA/{Date}/options.csv
```

`src/core/`
Core backtest objects and engine. This should stay strategy-independent.

`src/data_providers/`
Data providers and validation. CSV, Excel, database, and custom loader support lives here.

`src/strategies/`
Only strategy plugin files. No registry or framework plumbing should live here.

`src/registries/`
Registration files for pluggable components. Strategy registration lives in `strategy_registry.py`.

`src/strategy_helpers/`
Shared helper functions used by strategy files, such as common indicators and signal builders.

`src/execution/`
Trade execution simulation only: entries, exits, fills, slippage, brokerage/charges.

`src/option_engine/`
Option selection only: ATM/ITM/OTM, premium-based strikes, and future expiry/delta selection.

`src/portfolio/`
Portfolio state: capital, realized PnL, equity curve, exposure, and future margin tracking.

`src/risk_management/`
Reusable stop loss, target, square-off, and trade-limit logic.

`src/optimization/`
Strategy-independent optimizer. It reads each strategy's parameter grid.

`src/reports/`
Tradebook, optimization summary, metrics, and output column selection.

`custom_providers/`
Example place for users who want to write their own database/API/custom data loader.

`example_files/`
Tiny examples of valid futures and options files.

`tests/`
Smoke checks for strategy plugins and execution styles.

`scripts/`
Simple Windows/Linux helper commands.

`logs/`
Generated trade logs. Every parameter combination gets its own `.log` file.

`results/`
Generated CSV/JSON reports.

