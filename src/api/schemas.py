"""API request/response schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional


class Product(BaseModel):
    """Product schema."""
    id: int = Field(..., description="Product ID")
    title: str = Field(..., description="Product title")
    price: float = Field(..., ge=0, description="Product price")
    category: str = Field(..., description="Product category")
    description: Optional[str] = Field(None, description="Product description")
    brand: Optional[str] = Field(None, description="Product brand")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Product rating")


class RankRequest(BaseModel):
    """Ranking request schema."""
    query: str = Field(..., min_length=1, description="Search query")
    user_id: str = Field(..., description="User ID")
    products: List[Product] = Field(..., min_items=1, description="List of candidate products to rank")


class RankedProduct(BaseModel):
    """Ranked product schema."""
    id: int = Field(..., description="Product ID")
    score: float = Field(..., ge=0, le=1, description="Ranking score")
    title: str = Field(..., description="Product title")


class RankResponse(BaseModel):
    """Ranking response schema."""
    ranked_products: List[RankedProduct] = Field(..., description="Ranked products")
    query: str = Field(..., description="Original query")
    num_products: int = Field(..., description="Number of products ranked")


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Service status")
    version: Optional[str] = Field(None, description="Model version")


