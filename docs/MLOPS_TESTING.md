# MLOps Testing Strategy

## Philosophy

> "Treat AI code like any other high-risk system. Make it impossible to merge unless it has fast automated tests, offline model evals with hard thresholds, and deployment safety nets."

## The Problem with LLM-Generated Code

When using LLMs to generate code, you need extra safeguards:
- LLMs can hallucinate subtle bugs
- Changes might break data contracts
- Model performance can degrade silently
- API contracts might drift

## Our Solution: 4-Layer Testing Pyramid

### Layer 1: Pure Code Tests (No Data, No GPU)

**Purpose**: Catch "LLM hallucinated something slightly wrong" bugs early.

**Examples**:
- Config paths exist
- Feature functions return expected columns
- API schemas validate correctly

**Speed**: < 1-2s per test

**Run in CI**: Always

### Layer 2: Data & Pipeline Tests

**Purpose**: Ensure data pipelines produce sane data every time.

**Tests**:
- Schema validation (columns, dtypes, non-null)
- Invariant checks (uniqueness, ranges, logical relationships)
- Data quality gates

**Run in CI**: Always (after data generation)

### Layer 3: Model Evaluation Tests (Metric Gates)

**Purpose**: Prevent performance degradation from being merged.

**Metrics**:
- NDCG@10 ≥ 0.25 (hard threshold)
- MRR ≥ 0.20 (hard threshold)
- CTR@10 ≥ 0.10 (hard threshold)
- Regression guardrail: max 10% drop from baseline

**Run in CI**: On main branch or PRs with `run-eval` label

### Layer 4: API & E2E Tests

**Purpose**: Verify deployed service works correctly.

**Tests**:
- Health checks
- Ranking endpoint functionality
- Response schema validation
- Latency SLO (< 500ms)

**Run in CI**: On main branch

## CI Pipeline Gates

```
PR Created
    ↓
[Lint & Type Check] → Fail? → Block merge
    ↓ Pass
[Unit Tests] → Fail? → Block merge
    ↓ Pass
[Integration Tests] → Fail? → Block merge
    ↓ Pass
[Model Eval] (if model changed) → Fail? → Block merge
    ↓ Pass
[E2E Tests] (on main) → Fail? → Block merge
    ↓ Pass
✅ Merge Allowed
```

## Deployment Safety (Future)

Once deployed to production:

### Shadow Mode
- Send copy of traffic to new model
- Log decisions without impacting users
- Compare metrics offline

### Canary Deployment
- Route 1-5% of traffic to new version
- Monitor:
  - Latency SLO (p95 < 150ms)
  - Error rate
  - Click-through rate
- Auto-rollback if degraded

## Answering "Did you use AI?"

> "Yes, I used an LLM as a coding assistant, but everything is under test: data contracts, metrics, and e2e smoke tests. I never merge changes unless CI is green and offline metrics meet strict thresholds."

This demonstrates:
- Understanding of MLOps best practices
- Quality assurance mindset
- Production-ready thinking

## Key Takeaways

1. **Tests are gatekeepers, not vibes**: Hard thresholds prevent bad code from merging
2. **Fast feedback loop**: Unit tests catch issues in seconds
3. **Data contracts**: Integration tests ensure pipelines don't break silently
4. **Performance gates**: Model tests prevent regression
5. **E2E validation**: Smoke tests verify deployment works

## References

- [Testing ML Systems](https://www.evidentlyai.com/blog/ml-testing)
- [MLOps Testing Best Practices](https://neptune.ai/blog/mlops-testing)
- [Continuous Testing for ML](https://www.thoughtworks.com/insights/blog/testing-machine-learning-systems)

