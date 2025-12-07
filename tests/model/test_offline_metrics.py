"""Test model evaluation metrics and gates."""
import pytest
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
METRICS_FILE = ARTIFACTS_DIR / "metrics.json"
BASELINE_METRICS_FILE = ARTIFACTS_DIR / "baseline_metrics.json"


@pytest.mark.model
def test_metrics_file_exists():
    """Test that metrics file exists after evaluation."""
    if not METRICS_FILE.exists():
        pytest.skip("metrics.json missing – run: python src/models/evaluate_model.py")


@pytest.mark.model
def test_model_ndcg_gate():
    """Test that NDCG@10 meets minimum threshold."""
    if not METRICS_FILE.exists():
        pytest.skip("metrics.json missing – run: python src/models/evaluate_model.py")
    
    metrics = json.loads(METRICS_FILE.read_text())
    ndcg10 = metrics.get("ndcg@10")
    
    assert ndcg10 is not None, "ndcg@10 missing in metrics"
    # Hard guardrail – adjust to your baseline
    assert ndcg10 >= 0.25, f"NDCG@10 too low: {ndcg10:.4f} (minimum: 0.25)"


@pytest.mark.model
def test_model_mrr_gate():
    """Test that MRR meets minimum threshold."""
    if not METRICS_FILE.exists():
        pytest.skip("metrics.json missing – run: python src/models/evaluate_model.py")
    
    metrics = json.loads(METRICS_FILE.read_text())
    mrr = metrics.get("mrr")
    
    assert mrr is not None, "mrr missing in metrics"
    # Hard guardrail
    assert mrr >= 0.20, f"MRR too low: {mrr:.4f} (minimum: 0.20)"


@pytest.mark.model
def test_model_ctr_gate():
    """Test that CTR@10 meets minimum threshold."""
    if not METRICS_FILE.exists():
        pytest.skip("metrics.json missing – run: python src/models/evaluate_model.py")
    
    metrics = json.loads(METRICS_FILE.read_text())
    ctr = metrics.get("ctr@10")
    
    assert ctr is not None, "ctr@10 missing in metrics"
    # Hard guardrail
    assert ctr >= 0.10, f"CTR@10 too low: {ctr:.4f} (minimum: 0.10)"


@pytest.mark.model
def test_model_regression_guardrail():
    """Test that model hasn't regressed significantly from baseline."""
    if not METRICS_FILE.exists():
        pytest.skip("metrics.json missing – run: python src/models/evaluate_model.py")
    
    if not BASELINE_METRICS_FILE.exists():
        pytest.skip("baseline_metrics.json missing – will be created on first run")
    
    current = json.loads(METRICS_FILE.read_text())
    baseline = json.loads(BASELINE_METRICS_FILE.read_text())
    
    # Check NDCG@10 regression (max 10% drop)
    current_ndcg = current.get("ndcg@10")
    baseline_ndcg = baseline.get("ndcg@10")
    
    if current_ndcg is not None and baseline_ndcg is not None:
        assert current_ndcg >= 0.90 * baseline_ndcg, \
            f"NDCG@10 regressed >10%: {current_ndcg:.4f} vs {baseline_ndcg:.4f}"
    
    # Check MRR regression (max 10% drop)
    current_mrr = current.get("mrr")
    baseline_mrr = baseline.get("mrr")
    
    if current_mrr is not None and baseline_mrr is not None:
        assert current_mrr >= 0.90 * baseline_mrr, \
            f"MRR regressed >10%: {current_mrr:.4f} vs {baseline_mrr:.4f}"


@pytest.mark.model
def test_metrics_structure():
    """Test that metrics file has expected structure."""
    if not METRICS_FILE.exists():
        pytest.skip("metrics.json missing – run: python src/models/evaluate_model.py")
    
    metrics = json.loads(METRICS_FILE.read_text())
    
    required_keys = {"ndcg@10", "mrr", "ctr@10", "num_queries", "num_evaluated"}
    assert required_keys.issubset(metrics.keys()), \
        f"Missing keys in metrics: {required_keys - set(metrics.keys())}"
    
    # Check types
    assert isinstance(metrics["ndcg@10"], (int, float))
    assert isinstance(metrics["mrr"], (int, float))
    assert isinstance(metrics["ctr@10"], (int, float))
    assert isinstance(metrics["num_queries"], int)
    assert isinstance(metrics["num_evaluated"], int)


