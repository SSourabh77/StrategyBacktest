from src.data_providers.base import BaseDataProvider
from src.data_providers.csv_provider import CsvDataProvider
from src.data_providers.custom_loader import load_custom_provider
from src.data_providers.database_provider import DatabaseDataProvider
from src.data_providers.excel_provider import ExcelDataProvider


DATA_PROVIDER_REGISTRY: dict[str, type[BaseDataProvider]] = {
    CsvDataProvider.name: CsvDataProvider,
    DatabaseDataProvider.name: DatabaseDataProvider,
    ExcelDataProvider.name: ExcelDataProvider,
}


def get_data_provider(config: dict) -> BaseDataProvider:
    provider_name = config["data"].get("provider", "csv")
    if provider_name == "custom":
        custom_cfg = config["data"].get("custom", {})
        provider_cls = load_custom_provider(custom_cfg["module_path"], custom_cfg["class_name"])
        return provider_cls()
    if provider_name not in DATA_PROVIDER_REGISTRY:
        known = ", ".join(sorted(DATA_PROVIDER_REGISTRY))
        raise KeyError(f"Unknown data provider '{provider_name}'. Known providers: {known}, custom")
    return DATA_PROVIDER_REGISTRY[provider_name]()
