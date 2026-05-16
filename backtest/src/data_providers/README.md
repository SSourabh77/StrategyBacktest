# Data Providers

Code for loading data from different sources.

Current providers:

```text
csv_provider.py       loads DATA/{Date}/*.csv files
excel_provider.py     loads Excel sheets
database_provider.py  loads SQL query results
custom_loader.py      loads user-written provider classes
```

All providers must return the standard columns described in `docs/DATA_CONTRACT.md`.
