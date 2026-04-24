from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    sentence: str = Field(..., min_length=1, description="Clinical sentence to classify.")


class PredictResponse(BaseModel):
    label: str
    score: float


class BatchPredictRequest(BaseModel):
    sentences: list[str] = Field(..., min_length=1)


class BatchPredictItem(BaseModel):
    label: str
    score: float


class BatchPredictResponse(BaseModel):
    results: list[BatchPredictItem]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
