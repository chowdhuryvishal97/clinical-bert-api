# Clinical assertion real-time API

FastAPI service that runs [bvanaken/clinical-assertion-negation-bert](https://huggingface.co/bvanaken/clinical-assertion-negation-bert) for clinical assertion classification (PRESENT, ABSENT, CONDITIONAL).

## Overview

- **POST `/predict`** — classify a single sentence; returns top label and softmax score.
- **POST `/predict/batch`** — classify multiple sentences.
- **GET `/health`** — liveness and model-loaded flag.

The Hugging Face model expects the target concept delimited with `[entity] ... [entity]`. This API accepts a plain `sentence` and applies small pattern-based heuristics (e.g. “denies …”, “history of …”) so callers do not need to mark entities. The model’s `POSSIBLE` label is exposed as **`CONDITIONAL`** to match common clinical wording.

## Local development

Python 3.12+ recommended.

```bash
python -m venv .venv
.venv\Scripts\activate # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Run tests (downloads the model on first run; allow a few minutes):

```bash
pytest
```

Lint and format:

```bash
black --check app tests
flake8 app tests
```

## Docker

```bash
docker build -t clinical-bert-api .
docker run --rm -p 8080:8080 clinical-bert-api
```


## Quick checks

- **Health:** [http://localhost:8080/health](http://localhost:8080/health)  
  Expect JSON like: `{"status":"ok","model_loaded":true}`

- **Predict (PowerShell):**

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8080/predict" `
  -ContentType "application/json" `
  -Body '{"sentence":"The patient denies chest pain."}'
```

- **Predict (curl, if installed):**

```bash
curl -s -X POST "http://localhost:8080/predict" ^
  -H "Content-Type: application/json" ^
  -d "{\"sentence\":\"The patient denies chest pain.\"}"
```

Other endpoints:

- **`POST /predict/batch`** — body: `{"sentences": ["...", "..."]}`
- **OpenAPI docs:** [http://localhost:8080/docs](http://localhost:8080/docs)



## Example (Python)

```python
import requests

base = "http://localhost:8080"
r = requests.post(f"{base}/predict", json={"sentence": "The patient denies chest pain."})
print(r.json())  # {"label": "ABSENT", "score": ...}
```

### Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CLINICAL_BERT_MODEL_ID` | `bvanaken/clinical-assertion-negation-bert` | Hugging Face model id |
| `MODEL_DEVICE` | `-1` | `-1` CPU, `0` first CUDA GPU |
| `MODEL_MAX_LENGTH` | `256` | Tokenizer truncation |
| `PORT` | `8080` | Uvicorn listen port (Cloud Run sets this) |

## Tradeoffs and known limitations

- Entity wrapping is heuristic; unusual phrasing may mis-scope the `[entity]` span and affect labels.
- Sentences that begin with **If** and describe **experiences &lt;concept&gt;** are prefixed with a short “possibility of [entity] …” clause so the checkpoint’s `POSSIBLE` head activates (mapped to **`CONDITIONAL`**). Without that cue, this model often scores those spans as `PRESENT`.
- `CONDITIONAL` is the API name for the model’s `POSSIBLE` class.
- First request after deploy may be slow while weights load; CI/local first run downloads the model from Hugging Face.
