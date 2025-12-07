# Technical Context

## Technologies

### Core Stack
- **Python 3.11+**: Primary language
- **FastAPI**: Web framework for API service
- **LightGBM / scikit-learn**: ML models
- **Pandas**: Data processing
- **Parquet**: Feature store format

### Infrastructure
- **Docker**: Containerization
- **Kubernetes**: Orchestration (kind/minikube for local)
- **Dagster**: Pipeline orchestration
- **Prometheus**: Metrics collection
- **uvicorn**: ASGI server

### Development Tools
- **pytest**: Testing framework
- **GitHub Actions**: CI/CD
- **mypy/ruff**: Code quality (optional)

## Dependencies
- fastapi
- uvicorn
- pandas
- numpy
- lightgbm
- scikit-learn
- dagster
- prometheus-client
- pyarrow (for Parquet)

## Development Setup
- Python virtual environment
- Docker for containerization
- Kubernetes cluster (kind/minikube) for local testing
- GitHub repository for CI/CD

## Technical Constraints
- Synthetic data for reproducibility
- Local model registry (can be extended to S3)
- Basic monitoring (can be extended to full Grafana dashboards)


