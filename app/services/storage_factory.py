"""
Factory for selecting the storage backend (local JSON vs Supabase).

Usage:
    data_service = get_data_service()
"""

import os

from .data_service import DataService


def get_data_service():
    """
    Choose the storage backend based on USE_LOCAL_STORAGE env var.

    - USE_LOCAL_STORAGE=true (default): local JSON files in data/
    - USE_LOCAL_STORAGE=false: placeholder for SupabaseDataService (to be implemented)
    """
    use_local = os.environ.get("USE_LOCAL_STORAGE", "true").lower() == "true"

    if use_local:
        return DataService()

    try:
        from .supabase_service import SupabaseDataService  # type: ignore
    except ImportError as exc:  # pragma: no cover - import-time guard
        raise RuntimeError("Supabase backend requested but supabase_service is missing") from exc

    return SupabaseDataService()
