"""Unit tests for Phase 13A: Model-Driven UI Integrity Hardening."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent

from app.main import app

# Sample Payload A: Moderate Profile
PAYLOAD_A = {
    "Age": 22,
    "Gender": "Male",
    "Academic_Level": "Graduate",
    "Country": "USA",
    "Avg_Daily_Usage_Hours": 2.5,
    "Most_Used_Platform": "YouTube",
    "Daily_Unlocks": 75,
    "Sleep_Hours_Per_Night": 8.0,
    "Study_Hours": 5.0,
    "Physical_Activity_Hours": 2.5,
    "Stress_Level": "Low",
    "Purpose_Of_Use": "Education",
    "coverage": 0.90
}

# Sample Payload B: High Screen Time & Stress Profile
PAYLOAD_B = {
    "Age": 19,
    "Gender": "Female",
    "Academic_Level": "Undergraduate",
    "Country": "Canada",
    "Avg_Daily_Usage_Hours": 9.0,
    "Most_Used_Platform": "TikTok",
    "Daily_Unlocks": 260,
    "Sleep_Hours_Per_Night": 4.5,
    "Study_Hours": 1.5,
    "Physical_Activity_Hours": 0.0,
    "Stress_Level": "Very High",
    "Purpose_Of_Use": "Entertainment",
    "coverage": 0.90
}


def test_no_hardcoded_sample_inputs_in_frontend():
    """1. Assert frontend JavaScript does not contain hardcoded benchmark samples or load-sample buttons."""
    js_path = ROOT_DIR / "script.js"
    html_path = ROOT_DIR / "index.html"
    assert js_path.exists()
    assert html_path.exists()

    js_content = js_path.read_text(encoding="utf-8")
    html_content = html_path.read_text(encoding="utf-8")

    # Benchmark loader button must be completely removed
    assert "demo-sample-btn" not in html_content
    assert "demoSampleBtn" not in js_content
    assert "Load Benchmark Sample" not in html_content
    assert "Load Benchmark Sample" not in js_content


def test_no_hardcoded_prediction_or_interval_numbers_in_frontend():
    """2. Assert frontend code does not hardcode static prediction or interval values."""
    js_content = (ROOT_DIR / "script.js").read_text(encoding="utf-8")
    html_content = (ROOT_DIR / "index.html").read_text(encoding="utf-8")

    # Ensure no hardcoded specific prediction and interval values
    forbidden_values = ["6.67", "6.07", "7.26", "1.1884"]
    for val in forbidden_values:
        assert val not in js_content, f"Hardcoded value {val} found in script.js!"
        assert val not in html_content, f"Hardcoded value {val} found in index.html!"


def test_no_client_side_score_categories_in_frontend():
    """3. Assert frontend does not fabricate categorical bins or clinical labels."""
    js_content = (ROOT_DIR / "script.js").read_text(encoding="utf-8")
    html_content = (ROOT_DIR / "index.html").read_text(encoding="utf-8")

    forbidden_categories = [
        "Lower Score",
        "Moderate Score",
        "Higher Score",
        "Balanced Baseline",
        "Resilient Habits",
        "Elevated Daily Strain",
        "score-status-badge"
    ]
    for cat in forbidden_categories:
        assert cat not in js_content, f"Forbidden category '{cat}' found in script.js!"
        assert cat not in html_content, f"Forbidden category '{cat}' found in index.html!"


def test_no_deprecated_render_urls_in_frontend():
    """4. Assert no references to deprecated Render URLs in frontend code."""
    js_content = (ROOT_DIR / "script.js").read_text(encoding="utf-8")
    html_content = (ROOT_DIR / "index.html").read_text(encoding="utf-8")

    assert "mansik-santulan-score.onrender.com" not in js_content
    assert "mansik-santulan-score.onrender.com" not in html_content


def test_predict_api_returns_all_required_model_fields():
    """5. Assert /predict response provides all dynamic metadata fields required by the frontend."""
    with TestClient(app) as client:
        res = client.post("/predict", json=PAYLOAD_A)
        assert res.status_code == 200
        data = res.json()

        # Continuous score
        assert isinstance(data["estimated_wellbeing_score"], (int, float))
        assert 1.0 <= data["estimated_wellbeing_score"] <= 10.0

        # Conformal interval
        pi = data["prediction_interval"]
        assert "lower" in pi and "upper" in pi and "width" in pi and "nominal_coverage" in pi
        assert pi["lower"] <= data["estimated_wellbeing_score"] <= pi["upper"]
        assert pi["nominal_coverage"] == 0.90
        assert pi["width"] > 0

        # Model and uncertainty metadata
        assert "model_version" in data and len(data["model_version"]) > 0
        assert "uncertainty_method" in data and len(data["uncertainty_method"]) > 0
        assert "disclaimer" in data and "clinical" in data["disclaimer"].lower()


def test_explain_api_returns_dynamic_feature_attributions():
    """6. Assert /explain returns dynamic TreeSHAP contributions, base value, and directions."""
    with TestClient(app) as client:
        res = client.post("/explain", json=PAYLOAD_A)
        assert res.status_code == 200
        data = res.json()

        assert "estimated_wellbeing_score" in data
        assert "base_value" in data
        assert isinstance(data["base_value"], (int, float))
        assert "positive_contributors" in data
        assert "negative_contributors" in data
        assert "feature_contributions" in data
        assert len(data["feature_contributions"]) == 12


def test_model_predictions_vary_dynamically_across_different_inputs():
    """7. Assert that predictions and explanations genuinely vary between two distinct profiles."""
    with TestClient(app) as client:
        res_a = client.post("/predict", json=PAYLOAD_A)
        res_b = client.post("/predict", json=PAYLOAD_B)
        assert res_a.status_code == 200
        assert res_b.status_code == 200

        data_a = res_a.json()
        data_b = res_b.json()

        score_a = data_a["estimated_wellbeing_score"]
        score_b = data_b["estimated_wellbeing_score"]

        # Scores must not be identical across radically different input profiles
        assert score_a != score_b, f"Scores should vary: Score A={score_a}, Score B={score_b}"

        # Explainability must also differ
        exp_a = client.post("/explain", json=PAYLOAD_A).json()
        exp_b = client.post("/explain", json=PAYLOAD_B).json()
        assert exp_a["feature_contributions"] != exp_b["feature_contributions"]


def test_invalid_input_fails_cleanly_without_fallback():
    """8. Assert that invalid inputs return HTTP 422 and never produce fabricated fallback scores."""
    with TestClient(app) as client:
        invalid_payload = dict(PAYLOAD_A, Age=5)  # Age < 10 violates schema
        res = client.post("/predict", json=invalid_payload)
        assert res.status_code == 422
        data = res.json()
        assert "estimated_wellbeing_score" not in data


def test_health_api_returns_dynamic_runtime_metadata():
    """9. Assert /health returns verified runtime model and uncertainty state."""
    from app.model_service import model_service
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "ok"
        assert data["model_loaded"] is True
        assert data["uncertainty_loaded"] is True
        assert data["model_hash_verified"] is True
        assert data["model_version"] == model_service.model_version
        assert data["uncertainty_method"] == model_service.uncertainty_method


def test_country_grouping_explicit_behavior():
    """10. Assert country grouping explicitly handles top-10 ('USA') vs non-standard ('United States') vs unknown ('Brazil')."""
    from app.model_service import model_service
    from app.schemas import StudentSurveyRequest

    # Case 1: Exact top 10 member 'USA' -> retained as 'USA'
    req_usa = StudentSurveyRequest(**dict(PAYLOAD_A, Country="USA"))
    df_usa = model_service.format_input_dataframe(req_usa)
    assert df_usa["Grouped_country"].iloc[0] == "USA"

    # Case 2: 'United States' is not in TOP10_COUNTRIES -> mapped to 'Other'
    req_us = StudentSurveyRequest(**dict(PAYLOAD_A, Country="United States"))
    df_us = model_service.format_input_dataframe(req_us)
    assert df_us["Grouped_country"].iloc[0] == "Other"

    # Case 3: Unknown country 'Brazil' -> mapped to 'Other'
    req_unk = StudentSurveyRequest(**dict(PAYLOAD_A, Country="Brazil"))
    df_unk = model_service.format_input_dataframe(req_unk)
    assert df_unk["Grouped_country"].iloc[0] == "Other"


def test_metadata_consistency_across_endpoints_and_artifacts():
    """11. Assert model_version and uncertainty_method are unified and consistent across all endpoints and artifacts."""
    import json
    registry_path = ROOT_DIR / "models" / "model_registry.json"
    conformal_path = ROOT_DIR / "models" / "phase7_1_conformal_calibration.json"

    with open(registry_path, "r", encoding="utf-8") as f:
        champ_reg = json.load(f)["champion"]
    with open(conformal_path, "r", encoding="utf-8") as f:
        conf_art = json.load(f)

    expected_model_version = champ_reg["model_version"]
    expected_uncertainty_method = conf_art["method"]

    with TestClient(app) as client:
        health_res = client.get("/health")
        predict_res = client.post("/predict", json=PAYLOAD_A)
        explain_res = client.post("/explain", json=PAYLOAD_A)

        assert health_res.status_code == 200
        assert predict_res.status_code == 200
        assert explain_res.status_code == 200

        health_data = health_res.json()
        predict_data = predict_res.json()
        explain_data = explain_res.json()

        # All endpoints must agree with the authoritative registry champion version
        assert health_data["model_version"] == expected_model_version
        assert predict_data["model_version"] == expected_model_version
        assert explain_data["model_version"] == expected_model_version

        # Health and predict must agree with the conformal calibration artifact method
        assert health_data["uncertainty_method"] == expected_uncertainty_method
        assert predict_data["uncertainty_method"] == expected_uncertainty_method

