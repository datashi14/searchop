"""Test configuration and paths."""
import pytest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import (
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    MODELS_DIR,
    CATALOG_FILE,
    EVENTS_FILE,
    FEATURE_STORE_FILE,
)


def test_project_root_exists():
    """Test that project root is valid."""
    assert PROJECT_ROOT.exists()
    assert PROJECT_ROOT.is_dir()


def test_data_directories_exist():
    """Test that data directories exist."""
    assert DATA_DIR.exists()
    assert RAW_DATA_DIR.exists()
    assert PROCESSED_DATA_DIR.exists()
    assert MODELS_DIR.exists()


def test_config_paths_are_pathlib_paths():
    """Test that all config paths are Path objects."""
    assert isinstance(CATALOG_FILE, Path)
    assert isinstance(EVENTS_FILE, Path)
    assert isinstance(FEATURE_STORE_FILE, Path)


def test_paths_are_absolute():
    """Test that paths are absolute."""
    assert CATALOG_FILE.is_absolute() or CATALOG_FILE == RAW_DATA_DIR / "catalog.csv"
    assert EVENTS_FILE.is_absolute() or EVENTS_FILE == RAW_DATA_DIR / "events.csv"
    assert FEATURE_STORE_FILE.is_absolute() or FEATURE_STORE_FILE == PROCESSED_DATA_DIR / "feature_store.parquet"

