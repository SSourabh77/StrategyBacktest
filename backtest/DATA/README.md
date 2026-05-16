# DATA

Put real market data here.

Default expected layout:

```text
DATA/{Date}/futures.csv
DATA/{Date}/options.csv
```

Example:

```text
DATA/2026-05-15/futures.csv
DATA/2026-05-15/options.csv
```

This folder is used by the default CSV data provider.

To convert raw files into this day-wise format, use:

```bash
python scripts/extract_daywise_data.py --futures-file raw_futures.csv --options-file raw_options.csv
```

For futures files with expiry series `I`, `II`, and `III`, use:

```bash
python scripts/extract_daywise_data.py --futures-file raw_futures.csv --futures-expiry I --timeframe 1min
```
