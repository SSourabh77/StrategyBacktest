# Strategy Config

Strategy-specific settings live here.

Folder pattern:

```text
StrategyConfig/{strategy_name}/{strategy_name}_config.json
```

Example:

```text
StrategyConfig/ema_adx_crossover/ema_adx_crossover_config.json
```

This keeps strategy parameters and optimization grids separate from the global backtest config.

Global config only needs:

```json
"strategy": {
  "name": "ema_adx_crossover"
}
```

The system automatically loads:

```text
StrategyConfig/ema_adx_crossover/ema_adx_crossover_config.json
```
