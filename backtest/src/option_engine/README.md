# Option Engine

This module is responsible only for option selection.

Responsibilities:

```text
ATM / ITM / OTM strike selection
premium-based strike selection
future delta-based strike selection
expiry selection
full option contract selection
option-chain filtering
```

It should not generate strategy signals, calculate stop loss, write reports, or calculate portfolio metrics.

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
