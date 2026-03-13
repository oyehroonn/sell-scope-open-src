"""Storage layer: CSV or Pandas in-memory store (no Postgres/Redis)."""

from app.core.config import settings
from app.store.csv_store import CSVStore, get_store as get_csv_store
from app.store.pandas_store import PandasStore

_pandas_store_instance: PandasStore = None


def get_store():
    """Return the active store (Pandas or CSV) based on config."""
    if getattr(settings, "USE_PANDAS_STORE", False):
        global _pandas_store_instance
        if _pandas_store_instance is None:
            _pandas_store_instance = PandasStore()
            _pandas_store_instance.load_all()
        return _pandas_store_instance
    return get_csv_store()


def init_store():
    """Load the active store at startup."""
    return get_store()


__all__ = ["CSVStore", "PandasStore", "get_store", "init_store"]
