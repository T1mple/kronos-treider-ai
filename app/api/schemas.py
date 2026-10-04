from pydantic import BaseModel, Field

class ResearchRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT", min_length=3, max_length=20)
    interval: str = "1h"
    limit: int = Field(default=500, ge=50, le=1000)
    train_size: int = Field(default=300, ge=20, le=900)
    test_size: int = Field(default=50, ge=5, le=300)
    step: int = Field(default=50, ge=1, le=300)

class PaperOrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
