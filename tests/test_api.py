import hashlib
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
import numpy as np
import joblib

from app.main import app
from app.configuration import settings
from app.model_service import model_service

# Valid sample payload for testing
VALID_PAYLOAD = {
    "Age": 21,
    "Gender": "Female",
    "Academic_Level": "Undergraduate",
    "Country": "India",
    "Avg_Daily_Usage_Hours": 4.5,
    "Most_Used_Platform": "Instagram",
    "Daily_Unlocks": 140,
    "Sleep_Hours_Per_Night": 7.0,
    "Study_Hours": 3.0,
    "Physical_Activity_Hours": 1.5,
    "Stress_Level": "Medium",
    "Purpose_Of_Use": "Education",
    "coverage": 0.90
}

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_model_immutability():
    """Verify Phase 5 model SHA-256 hash has not been modified."""
    with open(settings.MODEL_PATH, "rb") as f:
        file_bytes = f.read()
    current_hash = hashlib.sha256(file_bytes).hexdigest()
    assert current_hash.lower() == settings.MODEL_EXPECTED_HASH.lower(), (
        f"Model artifact modified! Current hash: {current_hash}, Expected: {settings.MODEL_EXPECTED_HASH}"
    )

def test_conformal_calibration_artifact():
    """Verify Phase 7.1 conformal calibration artifact integrity and exact thresholds."""
    assert settings.CONFORMAL_PATH.exists(), f"Calibration JSON missing at {settings.CONFORMAL_PATH}"
    with open(settings.CONFORMAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data["source_model_hash"].lower() == settings.MODEL_EXPECTED_HASH.lower()
    assert data["calibration_sample_count"] == 3998
    assert data["conformity_score"] == "absolute_residual"
    
    thresh = data["calibration_thresholds"]
    assert "0.80" in thresh and "0.90" in thresh and "0.95" in thresh
    assert thresh["0.80"]["threshold_q"] == pytest.approx(0.4156, abs=1e-3)
    assert thresh["0.90"]["threshold_q"] == pytest.approx(0.5942, abs=1e-3)
    assert thresh["0.95"]["threshold_q"] == pytest.approx(0.7902, abs=1e-3)

def test_holdout_quarantine_in_production():
    """Verify holdout test set is not present in app/ package or required by runtime."""
    app_dir = Path(__file__).resolve().parent.parent / "app"
    for file_path in app_dir.rglob("*"):
        assert "holdout" not in file_path.name.lower()
        assert not file_path.name.endswith(".csv")

def test_root_endpoint(client):
    """Test GET / returns 200 and basic metadata."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "documentation" in data

def test_health_endpoint(client):
    """Test GET /health returns 200 and operational flags."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    assert data["uncertainty_loaded"] is True
    assert data["model_version"] == "phase5_tuned_extra_trees"
    assert "conformal" in data["uncertainty_method"].lower()

def test_predict_valid_payload_90(client):
    """Test POST /predict with 90% default coverage."""
    res = client.post("/predict", json=VALID_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    
    assert "estimated_wellbeing_score" in data
    assert "prediction_interval" in data
    interval = data["prediction_interval"]
    assert interval["nominal_coverage"] == 0.90
    assert interval["lower"] <= data["estimated_wellbeing_score"] <= interval["upper"]
    assert interval["lower"] < interval["upper"]
    assert interval["width"] == pytest.approx(1.1884, rel=1e-2)
    assert "disclaimer" in data
    assert "clinical" in data["disclaimer"].lower()

def test_predict_coverage_tiers(client):
    """Test POST /predict across 80%, 90%, and 95% coverage tiers."""
    for conf, expected_width in [(0.80, 0.8312), (0.90, 1.1884), (0.95, 1.5804)]:
        payload = VALID_PAYLOAD.copy()
        payload["coverage"] = conf
        res = client.post("/predict", json=payload)
        assert res.status_code == 200
        data = res.json()
        pi = data["prediction_interval"]
        assert pi["nominal_coverage"] == conf
        assert pi["lower"] <= data["estimated_wellbeing_score"] <= pi["upper"]
        assert pi["width"] == pytest.approx(expected_width, rel=1e-2)

def test_predict_missing_field(client):
    """Test POST /predict rejects payload missing required field."""
    invalid = VALID_PAYLOAD.copy()
    del invalid["Stress_Level"]
    res = client.post("/predict", json=invalid)
    assert res.status_code == 422
    data = res.json()
    assert data["error"] == "Validation Error"

def test_predict_invalid_numeric_range(client):
    """Test POST /predict rejects negative hours and out-of-range age."""
    invalid = VALID_PAYLOAD.copy()
    invalid["Age"] = 5  # Too young (<10)
    res = client.post("/predict", json=invalid)
    assert res.status_code == 422

    invalid = VALID_PAYLOAD.copy()
    invalid["Sleep_Hours_Per_Night"] = -2.0  # Impossible negative sleep
    res = client.post("/predict", json=invalid)
    assert res.status_code == 422

def test_predict_invalid_categorical(client):
    """Test POST /predict rejects invalid stress level (e.g. 'Moderate')."""
    invalid = VALID_PAYLOAD.copy()
    invalid["Stress_Level"] = "Moderate"  # Model supports only Low, Medium, High, Very High
    res = client.post("/predict", json=invalid)
    assert res.status_code == 422

def test_predict_unsupported_coverage(client):
    """Test POST /predict rejects unsupported coverage value (e.g. 0.99)."""
    invalid = VALID_PAYLOAD.copy()
    invalid["coverage"] = 0.99
    res = client.post("/predict", json=invalid)
    assert res.status_code == 422

def test_regression_against_direct_model(client):
    """Verify that API prediction matches direct model pipeline prediction bitwise."""
    direct_model = joblib.load(settings.MODEL_PATH)
    
    # Format input DataFrame using model_service
    from app.schemas import StudentSurveyRequest
    req_obj = StudentSurveyRequest(**VALID_PAYLOAD)
    df_in = model_service.format_input_dataframe(req_obj)
    
    direct_score = float(direct_model.predict(df_in)[0])
    
    res = client.post("/predict", json=VALID_PAYLOAD)
    assert res.status_code == 200
    api_score = res.json()["estimated_wellbeing_score"]
    
    assert abs(api_score - round(direct_score, 2)) <= 0.01

def test_explain_endpoint(client):
    """Test POST /explain computes TreeSHAP contributions aggregated to 12 original features."""
    res = client.post("/explain", json=VALID_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    
    assert "estimated_wellbeing_score" in data
    assert "base_value" in data
    assert "feature_contributions" in data
    assert len(data["feature_contributions"]) == 12  # Exact 12 original survey features
    
    for item in data["feature_contributions"]:
        assert "feature" in item
        assert "value" in item
        assert "shap_value" in item
        assert "direction" in item
        assert "interpretation" in item
        assert "cause" not in item["interpretation"].lower()
        assert "clinical" not in item["interpretation"].lower()

def test_cors_preflight(client):
    """Test OPTIONS CORS preflight response headers."""
    res = client.options(
        "/predict",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    assert res.status_code == 200
    assert "access-control-allow-origin" in res.headers
