# Backtest Flow

This project is designed so strategy logic, data loading, option selection, execution, risk, optimization, and reporting stay separate.

## Main Idea

The strategy does not directly trade. It only reads futures candles and creates signals.

```text
futures.csv
  -> strategy signal
  -> option selector
  -> execution engine
  -> risk management
  -> tradebook and logs
```

For the current assignment:

```text
Signal source: NIFTY futures
Trade instrument: NIFTY options
LONG signal: BUY CE
SHORT signal: BUY PE
Strike: nearest 50 from futures price
Expiry: nearest available expiry
Price: option close price from options.csv
```

## Config Flow

The project uses two config levels.

```text
config/backtest_config.json
```

This stores global settings:

```text
data location
strategy name
execution instrument
option selector
risk settings
report columns
```

```text
StrategyConfig/ema_adx_crossover/ema_adx_crossover_config.json
```

This stores strategy-specific settings:

```text
ema_fast
ema_slow
adx_period
adx_threshold
optimization parameter grid
```

When the program starts, it reads `config/backtest_config.json`, then automatically loads the matching strategy config based on strategy name.

## Data Flow

Default data location:

```text
DATA/{date}/futures.csv
DATA/{date}/options.csv
```

Example:

```text
DATA/2026-01-01/futures.csv
DATA/2026-01-01/options.csv
```

Mandatory futures columns:

```text
datetime, symbol, open, high, low, close, volume
```

Mandatory options columns:

```text
datetime, symbol, expiry, strike, option_type, open, high, low, close, volume
```

If option premium is missing, the backtest stops with an error. It does not create fake prices.

## Raw Data Extraction

If raw file has `DERIVATIVE_TYPE`:

```text
F = futures
O = options
```

For only options data:

```powershell
python .\scripts\extract_daywise_data.py --options-file "C:\Users\User\Downloads\Option_data.csv" --timeframe raw
```

For one mixed file containing both futures and options:

```powershell
python .\scripts\extract_daywise_data.py --mixed-file "C:\Users\User\Downloads\data.csv" --timeframe raw
```

`--timeframe raw` is recommended for large option files that are already candle data.

## Strategy Flow

Current strategy:

```text
ema_adx_crossover
```

Rules:

```text
LONG  = EMA_FAST crosses above EMA_SLOW and ADX >= threshold
SHORT = EMA_FAST crosses below EMA_SLOW and ADX >= threshold
```

The strategy returns standardized signals:

```text
datetime | signal | strength | metadata
```

The strategy does not select strikes, place trades, calculate PnL, or write reports.

## Option Selection Flow

For every signal, execution engine selects option contract:

```text
LONG  -> CE
SHORT -> PE
```

Strike selection:

```text
ATM = round(futures_price / 50) * 50
```

Example:

```text
futures price = 26315.10
ATM strike = 26300
LONG signal = BUY 26300 CE
```

Expiry selection:

```text
expiry_selector = NEAREST
```

So the system picks the nearest non-expired expiry available in `options.csv`.

## Price Search Flow

For entry price, system searches in `options.csv`:

```text
datetime = trade entry time
strike = selected strike
option_type = CE or PE
expiry = selected expiry
```

Then it uses:

```text
price_column = close
```

So entry price and exit price come from option candle close.

## Execution Flow

Signal execution delay is set to 1 bar.

Example:

```text
09:43 signal generated
09:44 option trade entered
```

This avoids same-candle lookahead bias.

The engine allows only one open trade at a time. It will not enter another trade while one is already open.

## Exit Flow

Trades can close due to:

```text
opposite_signal
stop_loss
target
trailing_stop
square_off_time
end_of_data
```

In the latest one-day test, all trades closed because of:

```text
opposite_signal
```

That means a LONG CE trade closed when a SHORT signal came, and a SHORT PE trade closed when a LONG signal came.

## Reporting Flow

Each run creates:

```text
results/{strategy_name}/{run_id}/tradebook.csv
results/{strategy_name}/{run_id}/optimization_results.csv
results/{strategy_name}/{run_id}/best_parameters.csv
results/{strategy_name}/{run_id}/run_summary.csv
```

Logs are written to:

```text
logs/{strategy_name}/{run_id}/trades/
```

The log shows:

```text
parameters
signal time
entry instrument
option type
strike
entry price
exit price
exit reason
PnL
```

## Best Parameter Flow

For a single run:

```text
combinations tested = 1
```

So `best_parameters.csv` is best only among that one setup.

For real optimization:

```powershell
python main.py optimize --config config\backtest_config.json
```

Then the system tests all parameter combinations and ranks them by:

```text
profit_factor
```

The best row is saved in:

```text
best_parameters.csv
```

## Current One-Day Test Result

The latest verified one-day run produced real option trades:

```text
instrument = OPTIONS
LONG = BUY CE
SHORT = BUY PE
strike = 26300
expiry = 2026-01-06
```

Result:

```text
total trades = 5
winning trades = 2
losing trades = 3
win rate = 40%
net pnl = 332.5
profit factor = 1.75
```

This proves the core assignment flow is working:

```text
futures signal -> option trade -> strike selection -> expiry selection -> premium lookup -> tradebook/log
```
