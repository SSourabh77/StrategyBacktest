from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.strategies.ema_adx_crossover import EmaAdxCrossoverStrategy


def test_strategy_sorts_data_and_skips_warmup():
    df = pd.read_csv(Path(__file__).resolve().parents[1] / "DATA" / "2026-05-15" / "futures.csv")
    df["datetime"] = pd.to_datetime(df["datetime"])
    shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
    strategy = EmaAdxCrossoverStrategy()
    parameters = {"ema_fast": 5, "ema_slow": 18, "adx_period": 10, "adx_threshold": 18}

    sorted_signals = strategy.generate_signals(df, parameters)
    shuffled_signals = strategy.generate_signals(shuffled, parameters)

    assert [signal.datetime for signal in shuffled_signals] == [signal.datetime for signal in sorted_signals]
    assert all(signal.datetime > df["datetime"].min() for signal in sorted_signals)


def test_strategy_rejects_invalid_ema_order():
    df = pd.read_csv(Path(__file__).resolve().parents[1] / "DATA" / "2026-05-15" / "futures.csv")
    df["datetime"] = pd.to_datetime(df["datetime"])
    strategy = EmaAdxCrossoverStrategy()
    parameters = {"ema_fast": 20, "ema_slow": 10, "adx_period": 10, "adx_threshold": 18}

    assert strategy.generate_signals(df, parameters) == []


def test_strategy_handles_duplicate_datetimes():
    df = pd.read_csv(Path(__file__).resolve().parents[1] / "DATA" / "2026-05-15" / "futures.csv")
    df["datetime"] = pd.to_datetime(df["datetime"])
    duplicated = pd.concat([df, df.head(5)], ignore_index=True)
    strategy = EmaAdxCrossoverStrategy()
    parameters = {"ema_fast": 5, "ema_slow": 18, "adx_period": 10, "adx_threshold": 18}

    normal_signals = strategy.generate_signals(df, parameters)
    duplicate_signals = strategy.generate_signals(duplicated, parameters)

    assert [signal.datetime for signal in duplicate_signals] == [signal.datetime for signal in normal_signals]
