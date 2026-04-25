import logging
import os
import re

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TextClassificationPipeline,
)

logger = logging.getLogger(__name__)

MODEL_ID = os.environ.get("CLINICAL_BERT_MODEL_ID", "bvanaken/clinical-assertion-negation-bert")
ENTITY = "[entity]"
MAX_LENGTH = int(os.environ.get("MODEL_MAX_LENGTH", "256"))

_pipeline: TextClassificationPipeline | None = None


def wrap_span(text: str, start: int, end: int) -> str:
    return text[:start] + f"{ENTITY} " + text[start:end] + f" {ENTITY}" + text[end:]


def to_model_input(sentence: str) -> str:
    """
    The checkpoint expects the asserted concept wrapped in [entity] ... [entity].
    Heuristics cover common clinical patterns; unknown text falls back to full-sentence wrap.
    """
    s = sentence.strip()
    if not s:
        return f"{ENTITY} {ENTITY}"

    # Hypothetical "If ... experiences <concept>, ..." — raw span scores PRESENT; a short
    # possibility preamble shifts mass to POSSIBLE (API: CONDITIONAL) for this pattern.
    if s.lower().startswith("if "):
        m = re.search(r"\bexperiences\s+([^,]+)", s, re.I)
        if m:
            ph = m.group(1).strip()
            return f"There is a possibility of {ENTITY} {ph} {ENTITY}. {s}"

    m = re.search(r"\bdenies\s+(.+?)\s*\.?\s*$", s, re.I)
    if m:
        ph = m.group(1).rstrip(".")
        i = s.lower().find(ph.lower())
        if i >= 0:
            return wrap_span(s, i, i + len(ph))

    m = re.search(r"\bhistory\s+of\s+(.+?)\s*\.?\s*$", s, re.I)
    if m:
        ph = m.group(1).rstrip(".")
        i = s.lower().find(ph.lower())
        if i >= 0:
            return wrap_span(s, i, i + len(ph))

    m = re.search(r"\bexperiences\s+([^,]+)", s, re.I)
    if m:
        ph = m.group(1).strip()
        i = s.lower().find(ph.lower())
        if i >= 0:
            return wrap_span(s, i, i + len(ph))

    m = re.search(r"\bsigns\s+of\s+(\w+)", s, re.I)
    if m:
        ph = m.group(1)
        i = s.lower().find(ph.lower())
        if i >= 0:
            return wrap_span(s, i, i + len(ph))

    return f"{ENTITY} {s} {ENTITY}"


def to_api_label(hf_label: str) -> str:
    if hf_label == "POSSIBLE":
        return "CONDITIONAL"
    return hf_label


def get_pipeline() -> TextClassificationPipeline:
    if _pipeline is None:
        raise RuntimeError("Model not loaded; call load_model() during application startup.")
    return _pipeline


def load_model() -> TextClassificationPipeline:
    global _pipeline
    device = int(os.environ.get("MODEL_DEVICE", "-1"))
    logger.info("Loading model %s (device=%s)", MODEL_ID, device)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
    _pipeline = TextClassificationPipeline(
        model=model,
        tokenizer=tokenizer,
        device=device,
        top_k=None,
        truncation=True,
        max_length=MAX_LENGTH,
    )
    _pipeline(to_model_input("The patient denies chest pain."))
    logger.info("Model ready")
    return _pipeline


def _first_prediction(pipe_out):
    """Normalize pipeline output to a single dict with label and score."""
    first = pipe_out[0]
    if isinstance(first, list):
        first = first[0]
    if not isinstance(first, dict):
        raise TypeError(f"Unexpected pipeline output: {pipe_out!r}")
    return first


def predict_sentence(sentence: str) -> tuple[str, float]:
    pipe = get_pipeline()
    marked = to_model_input(sentence)
    result = _first_prediction(pipe(marked))
    label = to_api_label(str(result["label"]))
    score = float(result["score"])
    return label, score
