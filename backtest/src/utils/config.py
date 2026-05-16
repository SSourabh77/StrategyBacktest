from __future__ import annotations

import json
from datetime import date
from pathlib import Path


def load_config(path: str | Path) -> dict:
    path = Path(path)
    base_dir = path.parent.parent if path.parent.name == "config" else Path.cwd()
    with path.open("r", encoding="utf-8-sig") as handle:
        if path.suffix.lower() == ".json":
            config = json.load(handle)
        else:
            try:
                import yaml
            except ImportError as exc:
                raise ImportError("PyYAML is required for YAML config files. Use config/backtest_config.json or install requirements.txt.") from exc
            config = yaml.safe_load(handle)
    config = merge_strategy_config(config, base_dir)
    config["data"]["start_date"] = _as_date(config["data"]["start_date"])
    config["data"]["end_date"] = _as_date(config["data"]["end_date"])
    return config


def merge_strategy_config(config: dict, base_dir: Path) -> dict:
    strategy_name = config.get("strategy", {}).get("name")
    if not strategy_name:
        return config

    strategy_config_path = config.get("strategy", {}).get("config_path")
    if strategy_config_path:
        path = Path(strategy_config_path)
        if not path.is_absolute():
            path = base_dir / path
    else:
        path = base_dir / "StrategyConfig" / strategy_name / f"{strategy_name}_config.json"

    if not path.exists():
        return config

    strategy_config = _load_raw_config(path)
    strategy_section = strategy_config.get("strategy", strategy_config)
    config.setdefault("strategy", {})
    if "parameters" in strategy_section:
        config["strategy"]["parameters"] = strategy_section["parameters"]
    if "optimization" in strategy_section:
        config.setdefault("optimization", {})
        config["optimization"].update(strategy_section["optimization"])
    return config


def _load_raw_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        if path.suffix.lower() == ".json":
            return json.load(handle)
        try:
            import yaml
        except ImportError as exc:
            raise ImportError("PyYAML is required for YAML config files. Use JSON config or install requirements.txt.") from exc
        return yaml.safe_load(handle)


def _as_date(value) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))

