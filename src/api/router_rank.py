"""Ranking endpoint router."""
from fastapi import APIRouter, HTTPException
from typing import List
import time

from src.api.schemas import RankRequest, RankResponse, RankedProduct
from src.api.monitoring import (
    request_count, request_latency, active_requests
)
from src.models.inference import rank_products, load_model, load_feature_store
from src.utils.logging_utils import setup_logging

logger = setup_logging()

router = APIRouter(prefix="/rank", tags=["ranking"])


@router.post("", response_model=RankResponse)
async def rank(request: RankRequest):
    """Rank products by query."""
    active_requests.inc()
    start_time = time.time()
    
    try:
        logger.info(f"Ranking request: query='{request.query}', products={len(request.products)}")
        
        # Convert products to dict format
        products = [
            {
                "id": p.id,
                "title": p.title,
                "price": p.price,
                "category": p.category,
                "description": getattr(p, "description", None),
                "brand": getattr(p, "brand", None),
                "rating": getattr(p, "rating", None),
            }
            for p in request.products
        ]
        
        # Load model and feature store (could be cached in production)
        model, feature_cols, _ = load_model()
        feature_store = load_feature_store()
        
        # Rank products
        ranked = rank_products(
            query=request.query,
            products=products,
            model=model,
            feature_cols=feature_cols,
            feature_store=feature_store
        )
        
        # Convert to response format
        ranked_products = [
            RankedProduct(id=r["id"], score=r["score"], title=r["title"])
            for r in ranked
        ]
        
        latency = time.time() - start_time
        request_latency.observe(latency)
        request_count.labels(status="success").inc()
        
        logger.info(f"Ranking complete: {len(ranked_products)} products, latency={latency:.3f}s")
        
        return RankResponse(
            ranked_products=ranked_products,
            query=request.query,
            num_products=len(ranked_products)
        )
    
    except Exception as e:
        latency = time.time() - start_time
        request_latency.observe(latency)
        request_count.labels(status="error").inc()
        logger.error(f"Ranking error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ranking failed: {str(e)}")
    
    finally:
        active_requests.dec()

