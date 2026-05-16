# Data Contract

All data providers may load data from any source, but must return these standard columns.

## Futures Data

Required:

```text
datetime, symbol, open, high, low, close, volume
```

## Options Data

Required:

```text
datetime, symbol, expiry, strike, option_type, open, high, low, close, volume
```

Allowed option types:

```text
CE, PE, CALL, PUT
```

Optional:

```text
open_interest, iv, delta, gamma, theta, vega, rho
```

## Rules

- `datetime` must be parseable as a timestamp.
- OHLC columns must be numeric.
- `high` must be greater than or equal to `low`.
- `strike` must be numeric for options.
- Duplicate candles are not allowed for the same instrument key.
- The engine avoids look-ahead bias by executing signals after the configured delay.

