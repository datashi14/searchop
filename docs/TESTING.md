# Testing Guide

This document describes the comprehensive testing strategy for SearchOp, implementing a 4-layer testing pyramid for AI/ML systems.

## Testing Pyramid

```
        /\
       /  \  Layer 4: E2E Tests (API smoke tests)
      /____\
     /      \  Layer 3: Model Evaluation (metric gates)
    /________\
   /          \  Layer 2: Integration Tests (data pipelines)
  /____________\
 /              \  Layer 1: Unit Tests (pure code)
/________________\
```

## Layer 1: Unit Tests

**Goal**: Fast tests (< 1-2s each) that verify pure code logic without data dependencies.

**Location**: `tests/unit/`

**Tests**:
- `test_config.py`: Configuration and path validation
- `test_feature_funcs.py`: Feature engineering functions
- `test_ranker_api_contract.py`: API request/response schemas

**Run**:
```bash
pytest tests/unit -v
```

**What they catch**:
- Broken imports
- Incorrect function logic
- Schema validation issues
- Configuration errors

## Layer 2: Integration Tests

**Goal**: Verify data pipelines produce valid, consistent data.

**Location**: `tests/integration/`

**Tests**:
- `test_catalog_schema.py`: Catalog data schema and invariants
- `test_events_schema.py`: Events data schema and funnel logic
- `test_feature_store_schema.py`: Feature store structure and constraints

**Run**:
```bash
# Generate data first
PYTHONPATH=. python src/data_ingestion/generate_synthetic_data.py
PYTHONPATH=. python src/data_ingestion/build_feature_store.py

# Run tests
pytest tests/integration -v -m integration
```

**What they catch**:
- Schema violations
- Data quality issues
- Broken pipeline logic
- Invariant violations

## Layer 3: Model Evaluation Tests

**Goal**: Enforce hard thresholds on model performance metrics.

**Location**: `tests/model/`

**Tests**:
- `test_offline_metrics.py`: NDCG@10, MRR, CTR gates and regression checks

**Run**:
```bash
# Train and evaluate model first
PYTHONPATH=. python src/models/train_ranking_model.py
PYTHONPATH=. python src/models/evaluate_model.py

# Run metric gates
pytest tests/model -v -m model
```

**Metric Thresholds**:
- NDCG@10: ≥ 0.25 (minimum)
- MRR: ≥ 0.20 (minimum)
- CTR@10: ≥ 0.10 (minimum)
- Regression: No more than 10% drop from baseline

**What they catch**:
- Model performance degradation
- Broken feature engineering
- Training pipeline issues
- Data drift affecting model quality

## Layer 4: E2E Tests

**Goal**: Smoke tests for the deployed API service.

**Location**: `tests/e2e/`

**Tests**:
- `test_rank_service_smoke.py`: Health checks, ranking endpoint, latency SLO

**Run**:
```bash
# Start API server
uvicorn src.api.main:app --reload &

# Run tests
pytest tests/e2e -v -m e2e
```

**What they catch**:
- API deployment issues
- Service unavailability
- Response format errors
- Latency violations

## Running All Tests

### Fast Tests (CI-friendly)
```bash
pytest tests/unit tests/integration -v --tb=short
```

### Full Test Suite
```bash
# 1. Generate data
PYTHONPATH=. python src/data_ingestion/generate_synthetic_data.py
PYTHONPATH=. python src/data_ingestion/build_feature_store.py

# 2. Unit & integration tests
pytest tests/unit tests/integration -v

# 3. Model evaluation (if model exists)
PYTHONPATH=. python src/models/train_ranking_model.py
PYTHONPATH=. python src/models/evaluate_model.py
pytest tests/model -v -m model

# 4. E2E tests (if API running)
pytest tests/e2e -v -m e2e
```

## CI/CD Integration

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs:

1. **Lint & Type Check**: `ruff` and `mypy`
2. **Unit Tests**: Fast code tests
3. **Integration Tests**: Data pipeline validation
4. **Model Evaluation**: Only on main branch or with `run-eval` label
5. **E2E Tests**: Only on main branch

### PR Requirements

A PR cannot be merged unless:
- ✅ All linting passes
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Model metrics meet thresholds (if model changed)

## Test Markers

Use pytest markers to control test execution:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.model`: Model evaluation tests
- `@pytest.mark.e2e`: End-to-end tests
- `@pytest.mark.slow`: Slow tests (skipped in fast CI)

**Examples**:
```bash
# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run integration and model tests
pytest -m "integration or model"
```

## Adding New Tests

### Unit Test Example
```python
# tests/unit/test_new_feature.py
import pytest

def test_new_feature_function():
    result = new_feature_function(input_data)
    assert result == expected_output
```

### Integration Test Example
```python
# tests/integration/test_new_pipeline.py
@pytest.mark.integration
def test_new_pipeline_schema():
    df = pd.read_parquet(NEW_PIPELINE_OUTPUT)
    assert "required_column" in df.columns
    assert df["required_column"].notnull().all()
```

### Model Test Example
```python
# tests/model/test_new_metric.py
@pytest.mark.model
def test_new_metric_gate():
    metrics = json.loads(Path("artifacts/metrics.json").read_text())
    assert metrics["new_metric"] >= 0.5, "Metric too low"
```

## Best Practices

1. **Fast First**: Unit tests should be < 1s each
2. **Data Independence**: Unit tests shouldn't require data files
3. **Clear Assertions**: Use descriptive error messages
4. **Isolation**: Tests should not depend on each other
5. **Deterministic**: Tests should produce consistent results
6. **Coverage**: Aim for >80% code coverage on critical paths

## Troubleshooting

### Tests fail with "ModuleNotFoundError"
```bash
export PYTHONPATH=.
# or
PYTHONPATH=. pytest tests/...
```

### Integration tests fail with "File not found"
Generate data first:
```bash
PYTHONPATH=. python src/data_ingestion/generate_synthetic_data.py
PYTHONPATH=. python src/data_ingestion/build_feature_store.py
```

### Model tests fail with "metrics.json missing"
Run evaluation first:
```bash
PYTHONPATH=. python src/models/evaluate_model.py
```

### E2E tests fail with connection errors
Start the API server:
```bash
uvicorn src.api.main:app --reload
```


