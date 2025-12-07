"""FastAPI application for ranking service."""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import Response  # noqa: E402

from src.api.router_rank import router  # noqa: E402
from src.api.schemas import HealthResponse  # noqa: E402
from src.api.monitoring import get_metrics, get_metrics_content_type, model_version  # noqa: E402
from src.utils.config import CURRENT_MODEL_VERSION_FILE  # noqa: E402
from src.utils.logging_utils import setup_logging  # noqa: E402

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("Starting ranking service...")
    
    # Set model version metric
    if CURRENT_MODEL_VERSION_FILE.exists():
        version = CURRENT_MODEL_VERSION_FILE.read_text().strip()
        model_version.labels(version=version).set(1)
        logger.info(f"Model version: {version}")
    else:
        logger.warning("No model version found")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ranking service...")


app = FastAPI(
    title="SearchOp Ranking API",
    description="AI Ranking & Recommendations for E-Commerce Search",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(router)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    version = None
    if CURRENT_MODEL_VERSION_FILE.exists():
        version = CURRENT_MODEL_VERSION_FILE.read_text().strip()
    
    return HealthResponse(status="healthy", version=version)


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "SearchOp Ranking API",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "rank": "/rank",
            "docs": "/docs",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

