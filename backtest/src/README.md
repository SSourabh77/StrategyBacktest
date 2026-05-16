# Source Code

Framework source code lives here.

Important folders:

```text
core/              backtest engine and trade objects
data_providers/    CSV, Excel, database, custom data loading
strategies/        pluggable strategy classes
registries/        registration process for strategy/data plugins
strategy_helpers/  shared helper functions for strategies
execution/         futures/options/multi-leg execution logic
option_engine/     strike and expiry selection logic
portfolio/         capital, equity, exposure, portfolio state
risk_management/   stop loss, target, square-off, trade limits
optimization/      strategy-agnostic optimizer
reports/           tradebook, metrics, output files
utils/             helper functions
```
