from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.option_engine.expiry_selector import ExpirySelector


def sample_options():
    return pd.DataFrame(
        {
            "datetime": pd.to_datetime(["2026-01-01 09:16:00"] * 4),
            "expiry": ["2026-01-01", "2026-01-08", "2026-01-29", "2026-02-26"],
            "strike": [22000, 22000, 22000, 22000],
            "option_type": ["CE", "CE", "CE", "CE"],
            "close": [100, 120, 180, 240],
        }
    )


def test_nearest_expiry():
    selected = ExpirySelector("NEAREST").select("2026-01-01 09:16:00", sample_options())
    assert selected.expiry == "2026-01-01"
    assert selected.dte == 0


def test_next_expiry():
    selected = ExpirySelector("NEXT").select("2026-01-01 09:16:00", sample_options())
    assert selected.expiry == "2026-01-08"


def test_monthly_expiry():
    selected = ExpirySelector("MONTHLY").select("2026-01-01 09:16:00", sample_options())
    assert selected.expiry == "2026-01-29"


def test_dte_expiry():
    selected = ExpirySelector("DTE_7").select("2026-01-01 09:16:00", sample_options())
    assert selected.expiry == "2026-01-08"


def test_fixed_expiry():
    selected = ExpirySelector("FIXED_DATE", fixed_expiry="2026-02-26").select("2026-01-01 09:16:00", sample_options())
    assert selected.expiry == "2026-02-26"
