# Strategies

Only strategy plugins live here.

Do not put registry, framework base classes, or engine code in this folder.

Each strategy must inherit `BaseStrategy` and implement:

```text
generate_signals()
get_parameter_grid()
```

Every strategy returns standard signals:

```text
datetime | signal | strength | metadata
```

The engine does not care which strategy generated the signal.

After creating a strategy file, register it separately in:

```text
src/registries/strategy_registry.py
```
