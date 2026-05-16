import pandas as pd

from src.data_providers.base import BaseDataProvider, DataRequest
from src.data_providers.validators import validate_futures, validate_options


class SampleCustomProvider(BaseDataProvider):
    name = "sample_custom"

    def load_futures(self, request: DataRequest) -> pd.DataFrame:
        # Replace this with any source: SQL query, API call, Parquet read, etc.
        df = pd.read_csv("example_files/futures_sample.csv")
        return validate_futures(df)

    def load_options(self, request: DataRequest) -> pd.DataFrame:
        # Database example:
        # query = "SELECT candle_time AS datetime, symbol, expiry, strike, option_type, open, high, low, close, volume FROM option_table"
        # df = pd.read_sql(query, connection)
        df = pd.read_csv("example_files/options_sample.csv")
        return validate_options(df)

