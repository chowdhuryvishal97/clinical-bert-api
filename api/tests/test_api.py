import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True


@pytest.mark.parametrize(
    "sentence,expected_label",
    [
        ("The patient denies chest pain.", "ABSENT"),
        ("He has a history of hypertension.", "PRESENT"),
        (
            "If the patient experiences dizziness, reduce the dosage.",
            "CONDITIONAL",
        ),
        ("No signs of pneumonia were observed.", "ABSENT"),
    ],
)
def test_predict_assignment_cases(client: TestClient, sentence: str, expected_label: str):
    r = client.post("/predict", json={"sentence": sentence})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["label"] == expected_label
    assert 0.0 <= body["score"] <= 1.0


def test_predict_validation(client: TestClient):
    r = client.post("/predict", json={})
    assert r.status_code == 422


def test_predict_batch(client: TestClient):
    r = client.post(
        "/predict/batch",
        json={
            "sentences": [
                "The patient denies chest pain.",
                "He has a history of hypertension.",
            ]
        },
    )
    assert r.status_code == 200
    data = r.json()["results"]
    assert len(data) == 2
    assert data[0]["label"] == "ABSENT"
    assert data[1]["label"] == "PRESENT"
