from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class DataRequest:
    symbol: str
    start_date: date
    end_date: date
    config: dict[str, Any]


class BaseDataProvider:
    name = "base"

    def load_futures(self, request: DataRequest) -> pd.DataFrame:
        raise NotImplementedError

    def load_options(self, request: DataRequest) -> pd.DataFrame:
        raise NotImplementedError

