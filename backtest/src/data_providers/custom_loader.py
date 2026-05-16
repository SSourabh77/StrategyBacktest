from __future__ import annotations

import importlib.util
from pathlib import Path

from src.data_providers.base import BaseDataProvider


def load_custom_provider(module_path: str, class_name: str) -> type[BaseDataProvider]:
    path = Path(module_path)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load custom provider module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    provider_cls = getattr(module, class_name)
    if not issubclass(provider_cls, BaseDataProvider):
        raise TypeError(f"{class_name} must inherit BaseDataProvider")
    return provider_cls

