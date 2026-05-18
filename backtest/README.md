# Backtest

Portable, strategy-independent Python backtesting framework for Nifty futures signals and futures/options execution.

Version 1 includes a complete EMA + ADX strategy, ATM option execution, generic optimization, per-combination logs, configurable reports, and plugin-style data providers.

See `docs/BACKTEST_FLOW.md` for the full interview-ready explanation of the data, signal, option execution, risk, optimization, and reporting flow.

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py dry-run --config config/backtest_config.json
python main.py optimize --config config/backtest_config.json
```

On Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py dry-run --config config/backtest_config.json
python main.py optimize --config config/backtest_config.json
```

Windows helper files are also included in `scripts/`:

```text
scripts/run_dry_run.bat
scripts/run_single.bat
scripts/run_optimize.bat
```

## Data Location

By default data is read from:

```text
DATA/{date}/*.csv
```

Example:

```text
DATA/2026-05-15/futures.csv
DATA/2026-05-15/options.csv
```

See `docs/DATA_CONTRACT.md` for mandatory columns.

Important for option backtests:

```text
futures.csv gives the signal
options.csv must contain matching datetime + expiry + strike + CE/PE rows for execution
```

If matching option candles are missing, the real backtest intentionally stops instead of inventing prices.

## Convert Raw Data Into Day-Wise DATA Folder

Use:

```bash
python scripts/extract_daywise_data.py --futures-file raw_futures.csv --options-file raw_options.csv
```

If the raw futures file contains multiple expiry series like `I`, `II`, `III`, use near-month `I` for normal futures signal generation:

```bash
python scripts/extract_daywise_data.py ^
  --futures-file raw_futures.csv ^
  --futures-expiry I ^
  --timeframe 1min
```

If raw column names are different, pass mapping files:

```bash
python scripts/extract_daywise_data.py ^
  --futures-file raw_futures.csv ^
  --options-file raw_options.csv ^
  --futures-mapping example_files/futures_column_mapping.json ^
  --options-mapping example_files/options_column_mapping.json
```

The script writes:

```text
DATA/{Date}/futures.csv
DATA/{Date}/options.csv
```

## Commands

```bash
python main.py dry-run --config config/backtest_config.json
python main.py run --config config/backtest_config.json
python main.py optimize --config config/backtest_config.json
```

## Output

Every run creates a unique folder:

```text
results/{strategy_name}/{run_id}/
logs/{strategy_name}/{run_id}/
```

Main files:

```text
results/{strategy_name}/{run_id}/tradebook.csv
results/{strategy_name}/{run_id}/optimization_results.csv
logs/{strategy_name}/{run_id}/trades/{parameter_combination}.log
```

## Add a New Strategy

Create only the strategy file in `src/strategies`, inherit `BaseStrategy`, and implement:

```python
generate_signals(market_data, parameters)
get_parameter_grid()
```

Then register it separately in:

```text
src/registries/strategy_registry.py
```

## EMA + ADX Safety Filters

`ema_adx_crossover` rejects invalid parameters where:

```text
ema_fast >= ema_slow
```

Optional filters are available in strategy parameters:

```json
"require_adx_rising": false,
"min_ema_distance": 0.0,
"min_ema_distance_pct": 0.0
```

Option liquidity filters are available in execution config:

```json
"min_option_volume": 1,
"max_bid_ask_spread": null
```

## Strategy-Specific Config

Global backtest settings stay in:

```text
config/backtest_config.json
```

Strategy parameters and optimization grids live separately:

```text
StrategyConfig/{strategy_name}/{strategy_name}_config.json
```

For EMA + ADX:

```text
StrategyConfig/ema_adx_crossover/ema_adx_crossover_config.json
```

The global config does not need a strategy config path. It only needs:

```json
"strategy": {
  "name": "ema_adx_crossover"
}
```

The system automatically searches:

```text
StrategyConfig/{strategy_name}/{strategy_name}_config.json
```

## Included Strategy Plugins

```text
ema_adx_crossover
sma_crossover
supertrend
vwap_breakout
opening_range_breakout
rsi_mean_reversion
macd_crossover
bollinger_band_breakout
price_action_breakout
option_greeks_based
delta_neutral
gamma_scalping
straddle_strangle
iron_condor
calendar_spread
statistical_arbitrage
machine_learning_signal_model
```

## Supported Execution Styles

```text
FUTURES
OPTIONS with BUY mode
OPTIONS with SELL mode
MULTI_LEG_OPTIONS
SYNTHETIC_FUTURES
HEDGED
SPREAD
```

## Option Expiry Selection

Option expiry selection is handled in `src/option_engine/`, not inside strategy files.

Supported expiry selectors:

```text
NEAREST
NEXT
WEEKLY
MONTHLY
SAME_DAY
DTE_0
DTE_1
DTE_7
DTE_14
FIXED_DATE
```

Example:

```json
"execution": {
  "instrument": "OPTIONS",
  "strike_selector": "ATM",
  "expiry_selector": "DTE_7"
}
```

For fixed expiry:

```json
"execution": {
  "expiry_selector": "FIXED_DATE",
  "fixed_expiry": "2026-01-29"
}
```

Smoke test all registered strategy plugins and execution styles:

```bash
python tests/smoke_all_requirements.py
```

## Folder Structure

Clean root structure:

```text
backtest/
  config/            settings files
  DATA/              real futures/options market data
  src/               framework source code
  custom_providers/  user-written data loaders
  example_files/     tiny sample CSV files
  tests/             smoke tests
  scripts/           helper run commands
  docs/              documentation
  logs/              generated log files
  results/           generated reports
```

See `docs/PROJECT_STRUCTURE.md` for the full explanation.

## Architecture Rule

The project separates responsibilities:

```text
DATA
  -> STRATEGY
  -> SIGNAL
  -> OPTION ENGINE
  -> EXECUTION ENGINE
  -> RISK MANAGEMENT
  -> PORTFOLIO
  -> REPORTS
```

Strategy files only generate signals. They do not select strikes, place trades, calculate PnL, or write reports.

## Add a Custom Data Provider

Create a class inheriting `BaseDataProvider` and return standard DataFrames.

For external custom loaders, set:

```yaml
data:
  provider: custom
  custom:
    module_path: custom_providers/sample_custom_provider.py
    class_name: SampleCustomProvider
```

## Portability

The project uses relative paths by default, so the full `backtest` folder can be zipped and moved to another system.

