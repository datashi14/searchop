"""Dagster pipeline for MLOps: data ingestion, feature engineering, and model retraining."""
from dagster import (
    op, job, schedule, DefaultScheduleStatus, Config,
    AssetMaterialization, MetadataValue
)
from dagster import repository
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_ingestion.generate_synthetic_data import main as generate_data
from src.data_ingestion.build_feature_store import main as build_features
from src.models.train_ranking_model import main as train_model
from src.models.evaluate_model import main as evaluate_model
from src.utils.config import (
    CATALOG_FILE, EVENTS_FILE, FEATURE_STORE_FILE, MODELS_DIR
)
from src.utils.logging_utils import setup_logging

logger = setup_logging()


class PipelineConfig(Config):
    """Pipeline configuration."""
    retrain_threshold: float = 0.05  # Retrain if improvement > 5%


@op
def ingest_data(context) -> dict:
    """Ingest new data."""
    context.log.info("Starting data ingestion...")
    
    try:
        generate_data()
        
        # Check if files were created
        catalog_exists = CATALOG_FILE.exists()
        events_exists = EVENTS_FILE.exists()
        
        if catalog_exists and events_exists:
            catalog_df = pd.read_csv(CATALOG_FILE)
            events_df = pd.read_csv(EVENTS_FILE)
            
            context.log.info(f"Ingested {len(catalog_df)} products and {len(events_df)} events")
            
            yield AssetMaterialization(
                asset_key="catalog_data",
                metadata={
                    "num_products": MetadataValue.int(len(catalog_df)),
                    "file_path": MetadataValue.path(str(CATALOG_FILE)),
                }
            )
            
            yield AssetMaterialization(
                asset_key="events_data",
                metadata={
                    "num_events": MetadataValue.int(len(events_df)),
                    "file_path": MetadataValue.path(str(EVENTS_FILE)),
                }
            )
            
            return {
                "status": "success",
                "num_products": len(catalog_df),
                "num_events": len(events_df),
            }
        else:
            raise Exception("Data files not created")
    
    except Exception as e:
        context.log.error(f"Data ingestion failed: {e}")
        raise


@op
def build_feature_store(context, data: dict) -> dict:
    """Build feature store from ingested data."""
    context.log.info("Building feature store...")
    
    try:
        build_features()
        
        if FEATURE_STORE_FILE.exists():
            feature_store = pd.read_parquet(FEATURE_STORE_FILE)
            
            context.log.info(f"Built feature store with {len(feature_store)} query-product pairs")
            
            yield AssetMaterialization(
                asset_key="feature_store",
                metadata={
                    "num_pairs": MetadataValue.int(len(feature_store)),
                    "file_path": MetadataValue.path(str(FEATURE_STORE_FILE)),
                }
            )
            
            return {
                "status": "success",
                "num_pairs": len(feature_store),
            }
        else:
            raise Exception("Feature store not created")
    
    except Exception as e:
        context.log.error(f"Feature store build failed: {e}")
        raise


@op
def train_ranking_model(context, features: dict, config: PipelineConfig) -> dict:
    """Train ranking model."""
    context.log.info("Training ranking model...")
    
    try:
        # Get current model metrics if exists
        current_metrics = None
        artifacts_dir = PROJECT_ROOT / "artifacts"
        model_files = sorted(MODELS_DIR.glob("model_v*.pkl"))
        
        if model_files:
            # Load latest model version
            latest_model = model_files[-1]
            version = latest_model.stem.replace("model_", "")
            metrics_file = artifacts_dir / f"training_metrics_{version}.json"
            
            if metrics_file.exists():
                import json
                with open(metrics_file, "r") as f:
                    current_metrics = json.load(f)
                context.log.info(f"Current model metrics: {current_metrics}")
        
        # Train new model
        train_model()
        
        # Get new model metrics
        model_files = sorted(MODELS_DIR.glob("model_v*.pkl"))
        if model_files:
            latest_model = model_files[-1]
            version = latest_model.stem.replace("model_", "")
            metrics_file = artifacts_dir / f"training_metrics_{version}.json"
            
            if metrics_file.exists():
                import json
                with open(metrics_file, "r") as f:
                    new_metrics = json.load(f)
                
                context.log.info(f"New model metrics: {new_metrics}")
                
                # Check if improvement is significant
                should_promote = True
                if current_metrics:
                    current_auc = current_metrics.get("val_auc", 0)
                    new_auc = new_metrics.get("val_auc", 0)
                    
                    improvement = (new_auc - current_auc) / current_auc if current_auc > 0 else 0
                    
                    if improvement < config.retrain_threshold:
                        context.log.warning(
                            f"Model improvement ({improvement:.2%}) below threshold "
                            f"({config.retrain_threshold:.2%}). Not promoting."
                        )
                        should_promote = False
                    else:
                        context.log.info(
                            f"Model improved by {improvement:.2%}. Promoting new version."
                        )
                
                yield AssetMaterialization(
                    asset_key="ranking_model",
                    metadata={
                        "version": MetadataValue.text(version),
                        "val_auc": MetadataValue.float(new_metrics.get("val_auc", 0)),
                        "promoted": MetadataValue.bool(should_promote),
                    }
                )
                
                return {
                    "status": "success",
                    "version": version,
                    "metrics": new_metrics,
                    "promoted": should_promote,
                }
        
        return {"status": "success", "version": "unknown"}
    
    except Exception as e:
        context.log.error(f"Model training failed: {e}")
        raise


@op
def evaluate_ranking_model(context, model: dict) -> dict:
    """Evaluate model and check metrics."""
    context.log.info("Evaluating model...")
    
    try:
        evaluate_model()
        
        artifacts_dir = PROJECT_ROOT / "artifacts"
        metrics_file = artifacts_dir / "metrics.json"
        
        if metrics_file.exists():
            import json
            with open(metrics_file, "r") as f:
                metrics = json.load(f)
            
            context.log.info(f"Model evaluation metrics: {metrics}")
            
            # Check if metrics meet thresholds
            ndcg = metrics.get("ndcg@10", 0)
            mrr = metrics.get("mrr", 0)
            ctr = metrics.get("ctr@10", 0)
            
            thresholds_met = (
                ndcg >= 0.25 and
                mrr >= 0.20 and
                ctr >= 0.10
            )
            
            yield AssetMaterialization(
                asset_key="model_evaluation",
                metadata={
                    "ndcg@10": MetadataValue.float(ndcg),
                    "mrr": MetadataValue.float(mrr),
                    "ctr@10": MetadataValue.float(ctr),
                    "thresholds_met": MetadataValue.bool(thresholds_met),
                }
            )
            
            return {
                "status": "success",
                "metrics": metrics,
                "thresholds_met": thresholds_met,
            }
        else:
            raise Exception("Metrics file not created")
    
    except Exception as e:
        context.log.error(f"Model evaluation failed: {e}")
        raise


@job(config={"ops": {"train_ranking_model": {"config": {"retrain_threshold": 0.05}}}})
def ranking_pipeline():
    """Main ranking pipeline."""
    data = ingest_data()
    features = build_feature_store(data)
    model = train_ranking_model(features)
    evaluation = evaluate_ranking_model(model)
    return evaluation


@schedule(
    job=ranking_pipeline,
    cron_schedule="0 2 * * 0",  # Every Sunday at 2 AM
    default_status=DefaultScheduleStatus.RUNNING,
)
def weekly_retraining_schedule(context):
    """Weekly model retraining schedule."""
    return {}


@repository
def searchop_repository():
    """Dagster repository."""
    return [ranking_pipeline, weekly_retraining_schedule]

