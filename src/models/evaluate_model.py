"""Evaluate model on offline evaluation dataset."""
import pandas as pd
import numpy as np
import json
import pickle
from pathlib import Path
from typing import Dict, List, Tuple
import sys

from src.utils.config import (
    FEATURE_STORE_FILE, MODELS_DIR, CURRENT_MODEL_VERSION_FILE
)
from src.utils.logging_utils import setup_logging

logger = setup_logging()

# Evaluation metrics directory
ARTIFACTS_DIR = Path(__file__).parent.parent.parent / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)
METRICS_FILE = ARTIFACTS_DIR / "metrics.json"
BASELINE_METRICS_FILE = ARTIFACTS_DIR / "baseline_metrics.json"


def load_model(version: str = None):
    """Load model from registry."""
    if version is None:
        # Load current model version
        if CURRENT_MODEL_VERSION_FILE.exists():
            version = CURRENT_MODEL_VERSION_FILE.read_text().strip()
        else:
            # Find latest version
            model_files = sorted(MODELS_DIR.glob("model_v*.pkl"))
            if not model_files:
                raise FileNotFoundError("No model files found")
            version = model_files[-1].stem.replace("model_", "")
    
    model_path = MODELS_DIR / f"model_{version}.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    logger.info(f"Loading model: {model_path}")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    
    return model, version


def load_eval_dataset():
    """Load evaluation dataset."""
    eval_dir = Path(__file__).parent.parent.parent / "data" / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    
    eval_queries_file = eval_dir / "eval_queries.parquet"
    eval_clicks_file = eval_dir / "eval_clicks.parquet"
    
    if not eval_queries_file.exists() or not eval_clicks_file.exists():
        logger.warning("Evaluation dataset not found. Creating from feature store...")
        create_eval_dataset()
    
    eval_queries = pd.read_parquet(eval_queries_file)
    eval_clicks = pd.read_parquet(eval_clicks_file)
    
    return eval_queries, eval_clicks


def create_eval_dataset():
    """Create evaluation dataset from feature store."""
    logger.info("Creating evaluation dataset from feature store...")
    
    feature_store = pd.read_parquet(FEATURE_STORE_FILE)
    
    # Sample queries for evaluation (stratified by query frequency)
    query_counts = feature_store["query"].value_counts()
    
    # Take top queries and some random ones
    top_queries = query_counts.head(20).index.tolist()
    random_queries = query_counts.sample(min(10, len(query_counts))).index.tolist()
    eval_queries_list = list(set(top_queries + random_queries))
    
    eval_data = feature_store[feature_store["query"].isin(eval_queries_list)].copy()
    
    # For each query, get candidate products
    eval_queries = []
    for query in eval_queries_list:
        query_products = eval_data[eval_data["query"] == query]["product_id"].unique()
        if len(query_products) > 0:
            eval_queries.append({
                "query": query,
                "candidate_product_ids": query_products.tolist()[:50]  # Limit to 50 products
            })
    
    eval_queries_df = pd.DataFrame(eval_queries)
    
    # Create ground truth clicks (use query_ctr > 0.1 as positive signal)
    eval_clicks = []
    for _, row in eval_queries_df.iterrows():
        query = row["query"]
        for product_id in row["candidate_product_ids"]:
            product_data = eval_data[
                (eval_data["query"] == query) & 
                (eval_data["product_id"] == product_id)
            ]
            if len(product_data) > 0:
                # Use query_ctr as proxy for relevance
                relevance = product_data.iloc[0].get("query_ctr", 0)
                clicked = 1 if relevance > 0.1 else 0
                eval_clicks.append({
                    "query": query,
                    "product_id": product_id,
                    "clicked": clicked,
                    "relevance": relevance
                })
    
    eval_clicks_df = pd.DataFrame(eval_clicks)
    
    # Save
    eval_dir = Path(__file__).parent.parent.parent / "data" / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    eval_queries_df.to_parquet(eval_dir / "eval_queries.parquet", index=False)
    eval_clicks_df.to_parquet(eval_dir / "eval_clicks.parquet", index=False)
    
    logger.info(f"Created evaluation dataset: {len(eval_queries_df)} queries, {len(eval_clicks_df)} query-product pairs")


def compute_ndcg_at_k(y_true: List[int], y_score: List[float], k: int = 10) -> float:
    """Compute NDCG@k."""
    if len(y_true) == 0 or sum(y_true) == 0:
        return 0.0
    
    # Sort by score
    sorted_pairs = sorted(zip(y_score, y_true), reverse=True)
    y_sorted = [label for _, label in sorted_pairs[:k]]
    
    # Compute DCG
    dcg = sum((2 ** label - 1) / np.log2(i + 2) for i, label in enumerate(y_sorted))
    
    # Compute IDCG (ideal DCG)
    ideal_sorted = sorted(y_true, reverse=True)[:k]
    idcg = sum((2 ** label - 1) / np.log2(i + 2) for i, label in enumerate(ideal_sorted))
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


def compute_mrr(y_true: List[int], y_score: List[float]) -> float:
    """Compute Mean Reciprocal Rank."""
    if len(y_true) == 0 or sum(y_true) == 0:
        return 0.0
    
    # Sort by score
    sorted_pairs = sorted(zip(y_score, y_true), reverse=True)
    
    # Find rank of first relevant item
    for rank, (_, label) in enumerate(sorted_pairs, 1):
        if label > 0:
            return 1.0 / rank
    
    return 0.0


def compute_ctr(y_true: List[int], y_score: List[float], k: int = 10) -> float:
    """Compute CTR@k (click-through rate for top k items)."""
    if len(y_true) == 0:
        return 0.0
    
    # Sort by score
    sorted_pairs = sorted(zip(y_score, y_true), reverse=True)
    top_k_labels = [label for _, label in sorted_pairs[:k]]
    
    return sum(top_k_labels) / len(top_k_labels) if top_k_labels else 0.0


def evaluate_model(model, feature_store: pd.DataFrame, eval_queries: pd.DataFrame, 
                   eval_clicks: pd.DataFrame) -> Dict:
    """Evaluate model and return metrics."""
    logger.info("Evaluating model...")
    
    # Feature columns for model (exclude identifiers and text)
    feature_cols = [
        "ctr", "atc_rate", "purchase_rate", "recent_views_7d", "recent_purchases_7d",
        "popularity", "query_ctr", "query_purchase_rate", "tfidf_similarity",
        "price", "rating"
    ]
    
    # Filter to available columns
    available_feature_cols = [col for col in feature_cols if col in feature_store.columns]
    
    all_ndcg10 = []
    all_mrr = []
    all_ctr = []
    
    for _, query_row in eval_queries.iterrows():
        query = query_row["query"]
        candidate_ids = query_row["candidate_product_ids"]
        
        # Get features for candidate products
        query_features = feature_store[
            (feature_store["query"] == query) &
            (feature_store["product_id"].isin(candidate_ids))
        ].copy()
        
        if len(query_features) == 0:
            continue
        
        # Prepare features
        X = query_features[available_feature_cols].fillna(0)
        
        # Get predictions
        if hasattr(model, "predict_proba"):
            scores = model.predict_proba(X)[:, 1]  # Probability of positive class
        else:
            scores = model.predict(X)
        
        # Get ground truth
        query_clicks = eval_clicks[
            (eval_clicks["query"] == query) &
            (eval_clicks["product_id"].isin(candidate_ids))
        ]
        
        # Create label vector
        y_true = []
        y_score = []
        product_to_label = dict(zip(query_clicks["product_id"], query_clicks["clicked"]))
        
        for product_id, score in zip(query_features["product_id"], scores):
            y_score.append(score)
            y_true.append(product_to_label.get(product_id, 0))
        
        # Compute metrics
        ndcg10 = compute_ndcg_at_k(y_true, y_score, k=10)
        mrr = compute_mrr(y_true, y_score)
        ctr = compute_ctr(y_true, y_score, k=10)
        
        all_ndcg10.append(ndcg10)
        all_mrr.append(mrr)
        all_ctr.append(ctr)
    
    # Aggregate metrics
    metrics = {
        "ndcg@10": float(np.mean(all_ndcg10)),
        "mrr": float(np.mean(all_mrr)),
        "ctr@10": float(np.mean(all_ctr)),
        "num_queries": len(eval_queries),
        "num_evaluated": len(all_ndcg10),
    }
    
    logger.info(f"Evaluation metrics: {metrics}")
    return metrics


def main():
    """Run model evaluation."""
    logger.info("Starting model evaluation...")
    
    # Load model
    try:
        model, version = load_model()
        logger.info(f"Evaluating model version: {version}")
    except FileNotFoundError as e:
        logger.error(f"Model not found: {e}")
        logger.info("Please train a model first using: python src/models/train_ranking_model.py")
        return
    
    # Load feature store
    if not FEATURE_STORE_FILE.exists():
        logger.error(f"Feature store not found: {FEATURE_STORE_FILE}")
        logger.info("Please build feature store first using: python src/data_ingestion/build_feature_store.py")
        return
    
    feature_store = pd.read_parquet(FEATURE_STORE_FILE)
    
    # Load evaluation dataset
    eval_queries, eval_clicks = load_eval_dataset()
    
    # Evaluate
    metrics = evaluate_model(model, feature_store, eval_queries, eval_clicks)
    
    # Save metrics
    with open(METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved metrics to {METRICS_FILE}")
    
    # Create baseline if it doesn't exist
    if not BASELINE_METRICS_FILE.exists():
        logger.info("Creating baseline metrics...")
        with open(BASELINE_METRICS_FILE, "w") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Saved baseline metrics to {BASELINE_METRICS_FILE}")
    
    logger.info("Evaluation complete!")


if __name__ == "__main__":
    main()

