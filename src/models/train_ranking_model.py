"""Train ranking model on feature store."""
import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, log_loss, classification_report
import lightgbm as lgb
import sys

from src.utils.config import (
    FEATURE_STORE_FILE, MODELS_DIR, CURRENT_MODEL_VERSION_FILE
)
from src.utils.logging_utils import setup_logging

logger = setup_logging()

# Metrics directory
ARTIFACTS_DIR = Path(__file__).parent.parent.parent / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)


def get_next_model_version() -> str:
    """Get next model version number."""
    model_files = sorted(MODELS_DIR.glob("model_v*.pkl"))
    if not model_files:
        return "v1"
    
    # Extract version numbers
    versions = []
    for f in model_files:
        version_str = f.stem.replace("model_", "")
        try:
            version_num = int(version_str.replace("v", ""))
            versions.append(version_num)
        except ValueError:
            continue
    
    if not versions:
        return "v1"
    
    next_version = max(versions) + 1
    return f"v{next_version}"


def prepare_features_and_labels(feature_store: pd.DataFrame) -> tuple:
    """Prepare features and labels for training."""
    logger.info("Preparing features and labels...")
    
    # Feature columns (numeric features for model)
    feature_cols = [
        "ctr", "atc_rate", "purchase_rate",
        "recent_views_7d", "recent_purchases_7d", "popularity",
        "query_ctr", "query_purchase_rate", "tfidf_similarity",
        "price", "rating"
    ]
    
    # Filter to available columns
    available_feature_cols = [col for col in feature_cols if col in feature_store.columns]
    logger.info(f"Using {len(available_feature_cols)} features: {available_feature_cols}")
    
    # Create label: clicked or purchased (binary classification)
    # We'll use query_ctr > 0.1 as a proxy for positive label
    # In real scenario, you'd use actual click/purchase data
    feature_store["label"] = (
        (feature_store["query_ctr"] > 0.1) | 
        (feature_store["query_purchase_rate"] > 0.05)
    ).astype(int)
    
    # Prepare data
    X = feature_store[available_feature_cols].fillna(0)
    y = feature_store["label"]
    
    # Remove rows with all zeros (no signal)
    valid_rows = (X.sum(axis=1) > 0) | (y > 0)
    X = X[valid_rows]
    y = y[valid_rows]
    
    logger.info(f"Prepared {len(X)} samples")
    logger.info(f"Positive label rate: {y.mean():.4f}")
    
    return X, y, available_feature_cols


def train_model(X_train: pd.DataFrame, y_train: pd.Series, 
                X_val: pd.DataFrame, y_val: pd.Series) -> lgb.Booster:
    """Train LightGBM model."""
    logger.info("Training LightGBM model...")
    
    # LightGBM parameters
    params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "boosting_type": "gbdt",
        "num_leaves": 31,
        "learning_rate": 0.05,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "verbose": -1,
        "seed": 42,
    }
    
    # Create datasets
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    # Train model
    model = lgb.train(
        params,
        train_data,
        valid_sets=[val_data],
        num_boost_round=100,
        callbacks=[lgb.early_stopping(stopping_rounds=10), lgb.log_evaluation(period=10)],
    )
    
    logger.info("Model training complete")
    return model


def evaluate_model(model: lgb.Booster, X: pd.DataFrame, y: pd.Series, 
                   split_name: str) -> dict:
    """Evaluate model and return metrics."""
    logger.info(f"Evaluating on {split_name} set...")
    
    # Get predictions
    y_pred_proba = model.predict(X)
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    # Compute metrics
    auc = roc_auc_score(y, y_pred_proba) if y.nunique() > 1 else 0.0
    logloss = log_loss(y, y_pred_proba)
    
    metrics = {
        f"{split_name}_auc": float(auc),
        f"{split_name}_logloss": float(logloss),
        f"{split_name}_samples": int(len(X)),
    }
    
    logger.info(f"{split_name} AUC: {auc:.4f}")
    logger.info(f"{split_name} Log Loss: {logloss:.4f}")
    
    return metrics


def save_model(model: lgb.Booster, version: str, feature_cols: list, metrics: dict):
    """Save model and metadata."""
    logger.info(f"Saving model version {version}...")
    
    # Save model
    model_path = MODELS_DIR / f"model_{version}.pkl"
    with open(model_path, "wb") as f:
        pickle.dump({
            "model": model,
            "feature_cols": feature_cols,
            "version": version,
        }, f)
    
    logger.info(f"Saved model to {model_path}")
    
    # Save version info
    CURRENT_MODEL_VERSION_FILE.write_text(version)
    logger.info(f"Set current model version to {version}")
    
    # Save training metrics
    metrics_file = ARTIFACTS_DIR / f"training_metrics_{version}.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved metrics to {metrics_file}")


def main():
    """Train ranking model."""
    logger.info("Starting model training...")
    
    # Load feature store
    if not FEATURE_STORE_FILE.exists():
        logger.error(f"Feature store not found: {FEATURE_STORE_FILE}")
        logger.info("Please build feature store first: python src/data_ingestion/build_feature_store.py")
        return
    
    logger.info(f"Loading feature store from {FEATURE_STORE_FILE}")
    feature_store = pd.read_parquet(FEATURE_STORE_FILE)
    logger.info(f"Loaded {len(feature_store)} query-product pairs")
    
    # Prepare features and labels
    X, y, feature_cols = prepare_features_and_labels(feature_store)
    
    # Split data
    logger.info("Splitting data into train/validation sets...")
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"Train set: {len(X_train)} samples")
    logger.info(f"Validation set: {len(X_val)} samples")
    
    # Train model
    model = train_model(X_train, y_train, X_val, y_val)
    
    # Evaluate
    train_metrics = evaluate_model(model, X_train, y_train, "train")
    val_metrics = evaluate_model(model, X_val, y_val, "val")
    
    # Combine metrics
    all_metrics = {**train_metrics, **val_metrics}
    
    # Get next version
    version = get_next_model_version()
    
    # Save model
    save_model(model, version, feature_cols, all_metrics)
    
    logger.info("\n" + "="*50)
    logger.info("Training Summary:")
    logger.info(f"Model Version: {version}")
    logger.info(f"Features: {len(feature_cols)}")
    logger.info(f"Train AUC: {train_metrics['train_auc']:.4f}")
    logger.info(f"Val AUC: {val_metrics['val_auc']:.4f}")
    logger.info("="*50)
    logger.info("Training complete!")


if __name__ == "__main__":
    main()

