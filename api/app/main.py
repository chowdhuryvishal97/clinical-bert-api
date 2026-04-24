import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.model import load_model, predict_sentence
from app.schemas import (
    BatchPredictItem,
    BatchPredictRequest,
    BatchPredictResponse,
    HealthResponse,
    PredictRequest,
    PredictResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield


app = FastAPI(
    title="Clinical assertion API",
    description="Real-time assertion classification using clinical-assertion-negation-bert.",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        from app.model import get_pipeline

        get_pipeline()
        loaded = True
    except RuntimeError:
        loaded = False
    return HealthResponse(status="ok", model_loaded=loaded)


@app.post("/predict", response_model=PredictResponse)
def predict(body: PredictRequest) -> PredictResponse:
    try:
        label, score = predict_sentence(body.sentence)
        return PredictResponse(label=label, score=score)
    except Exception as e:
        logger.exception("predict failed")
        raise HTTPException(status_code=500, detail="Inference failed") from e


@app.post("/predict/batch", response_model=BatchPredictResponse)
def predict_batch(body: BatchPredictRequest) -> BatchPredictResponse:
    results: list[BatchPredictItem] = []
    try:
        for s in body.sentences:
            label, score = predict_sentence(s)
            results.append(BatchPredictItem(label=label, score=score))
        return BatchPredictResponse(results=results)
    except Exception as e:
        logger.exception("batch predict failed")
        raise HTTPException(status_code=500, detail="Inference failed") from e
