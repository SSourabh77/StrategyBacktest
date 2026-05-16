import pandas as pd

from src.data_providers.base import BaseDataProvider, DataRequest
from src.data_providers.validators import apply_column_mapping, validate_futures, validate_options


class ExcelDataProvider(BaseDataProvider):
    name = "excel"

    def load_futures(self, request: DataRequest) -> pd.DataFrame:
        cfg = request.config["data"]
        excel_cfg = cfg.get("excel", {})
        df = pd.read_excel(excel_cfg["file"], sheet_name=excel_cfg.get("futures_sheet", "futures"))
        df = apply_column_mapping(df, cfg.get("column_mapping"))
        return validate_futures(df)

    def load_options(self, request: DataRequest) -> pd.DataFrame:
        cfg = request.config["data"]
        excel_cfg = cfg.get("excel", {})
        df = pd.read_excel(excel_cfg["file"], sheet_name=excel_cfg.get("options_sheet", "options"))
        df = apply_column_mapping(df, cfg.get("column_mapping"))
        return validate_options(df)

