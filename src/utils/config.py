"""Configuration settings for the SearchOp project."""
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Data paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Model paths
MODELS_DIR = PROJECT_ROOT / "models"

# File names
CATALOG_FILE = RAW_DATA_DIR / "catalog.csv"
EVENTS_FILE = RAW_DATA_DIR / "events.csv"
FEATURE_STORE_FILE = PROCESSED_DATA_DIR / "feature_store.parquet"

# Model registry
MODEL_VERSION_PREFIX = "model_v"
CURRENT_MODEL_VERSION_FILE = MODELS_DIR / "current_model_version.txt"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)


