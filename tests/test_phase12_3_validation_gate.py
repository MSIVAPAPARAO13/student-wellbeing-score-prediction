"""Unit tests for Phase 12.3: Candidate Validation Gate & Shadow-Readiness."""

import json
import hashlib
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import joblib
import shap
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent

from app.main import app
from app.governance import registry_manager, shadow_manager
from app.model_service import model_service
from app.schemas import StudentSurveyRequest, PredictionResponse

CHAMPION_EXPECTED_HASH = "a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8"
CANDIDATE_EXPECTED_HASH = "aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc"
CHAMPION_CALIB_EXPECTED_HASH = "22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b"
CANDIDATE_CALIB_EXPECTED_HASH = "b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af"


def test_champion_sha256_exact_match():
    """1. Assert production Champion artifact SHA-256 matches authoritative hash bit-for-bit."""
    path = ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib"
    assert path.exists(), "Champion model artifact missing!"
    with open(path, "rb") as f:
        computed = hashlib.sha256(f.read()).hexdigest()
    assert computed.lower() == CHAMPION_EXPECTED_HASH.lower()


def test_candidate_sha256_exact_match():
    """2. Assert Candidate v1.2 artifact SHA-256 matches authoritative hash bit-for-bit."""
    path = ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib"
    assert path.exists(), "Candidate model artifact missing!"
    with open(path, "rb") as f:
        computed = hashlib.sha256(f.read()).hexdigest()
    assert computed.lower() == CANDIDATE_EXPECTED_HASH.lower()


def test_champion_calibration_hash_exact_match():
    """3. Assert Phase 7.1 Champion calibration artifact SHA-256 and source model linkage."""
    path = ROOT_DIR / "models" / "phase7_1_conformal_calibration.json"
    assert path.exists(), "Champion calibration artifact missing!"
    with open(path, "rb") as f:
        computed = hashlib.sha256(f.read()).hexdigest()
    assert computed.lower() == CHAMPION_CALIB_EXPECTED_HASH.lower()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["source_model_hash"].lower() == CHAMPION_EXPECTED_HASH.lower()


def test_candidate_calibration_hash_exact_match():
    """4. Assert Phase 12 Candidate calibration artifact SHA-256 and source model linkage."""
    path = ROOT_DIR / "models" / "candidate_v1_2_conformal_calibration.json"
    assert path.exists(), "Candidate calibration artifact missing!"
    with open(path, "rb") as f:
        computed = hashlib.sha256(f.read()).hexdigest()
    assert computed.lower() == CANDIDATE_CALIB_EXPECTED_HASH.lower()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["source_model_hash"].lower() == CANDIDATE_EXPECTED_HASH.lower()


def test_candidate_registry_state_validating_challenger():
    """5. Confirm Candidate v1.2 is registered as CHALLENGER with VALIDATING status."""
    challengers = registry_manager.get_challengers()
    cand = next((c for c in challengers if c["model_version"] == "candidate_v1_2_revalidated"), None)
    assert cand is not None, "Candidate v1.2 not registered in model_registry.json"
    assert cand["status"] == "CHALLENGER"
    assert cand["approval_status"] == "VALIDATING"
    assert cand["deployment_status"] == "SHADOW_ONLY"


def test_champion_registry_state_active_production():
    """6. Confirm Champion is registered as CHAMPION with ACTIVE deployment status."""
    champ = registry_manager.get_champion()
    assert champ["model_version"] == "phase5_tuned_extra_trees"
    assert champ["status"] == "CHAMPION"
    assert champ["approval_status"] == "APPROVED_FOR_PRODUCTION"
    assert champ["deployment_status"] == "ACTIVE"
    assert champ["artifact_hash"].lower() == CHAMPION_EXPECTED_HASH.lower()


def test_production_route_still_points_to_champion():
    """7. Assert live /predict route executes through the Champion pipeline."""
    with TestClient(app) as client:
        payload = {
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
        res = client.post("/predict", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["model_version"] == "phase5_tuned_extra_trees"
        assert "5-Fold Cross-Conformal" in data["uncertainty_method"]
        # Champion prediction for this exact vector is 6.67
        assert abs(data["estimated_wellbeing_score"] - 6.67) < 0.05


def test_candidate_is_not_production_default():
    """8. Assert Candidate v1.2 is NOT the active serving model in ModelService."""
    from app.configuration import settings
    assert settings.MODEL_PATH.name == "phase5_tuned_extra_trees.joblib"
    assert settings.MODEL_EXPECTED_HASH.lower() == CHAMPION_EXPECTED_HASH.lower()
    assert settings.MODEL_EXPECTED_HASH.lower() != CANDIDATE_EXPECTED_HASH.lower()
    assert registry_manager.get_champion()["model_version"] == "phase5_tuned_extra_trees"


def test_prediction_schema_compatibility():
    """9. Assert Candidate consumes the 12 canonical features and produces compliant scores."""
    cand_path = ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib"
    cand = joblib.load(cand_path)

    sample_dict = {
        "Study_Hours": 3.0,
        "Age": 21,
        "Avg_Daily_Usage_Hours": 4.5,
        "Daily_Unlocks": 140,
        "Physical_Activity_Hours": 1.5,
        "Sleep_Hours_Per_Night": 7.0,
        "Stress_Level": "Medium",
        "Gender": "Female",
        "Academic_Level": "Undergraduate",
        "Most_Used_Platform": "Instagram",
        "Purpose_Of_Use": "Education",
        "Grouped_country": "India"
    }
    input_df = pd.DataFrame([sample_dict])
    pred = cand.predict(input_df)[0]
    assert isinstance(pred, (float, np.floating))
    assert 1.0 <= pred <= 10.0


def test_shap_additivity_threshold():
    """10. Verify Candidate TreeSHAP explanation additivity is within numeric tolerance."""
    cand_path = ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib"
    cand = joblib.load(cand_path)
    cand_tree = cand.named_steps["model"]
    cand_preproc = cand.named_steps["preprocessor"]

    sample_df = pd.DataFrame([{
        "Study_Hours": 4.0,
        "Age": 22,
        "Avg_Daily_Usage_Hours": 5.0,
        "Daily_Unlocks": 120,
        "Physical_Activity_Hours": 2.0,
        "Sleep_Hours_Per_Night": 8.0,
        "Stress_Level": "High",
        "Gender": "Male",
        "Academic_Level": "Graduate",
        "Most_Used_Platform": "YouTube",
        "Purpose_Of_Use": "Entertainment",
        "Grouped_country": "Other"
    }])
    trans_x = cand_preproc.transform(sample_df)
    explainer = shap.TreeExplainer(cand_tree)
    shap_vals = explainer.shap_values(trans_x)[0]
    base_val = explainer.expected_value
    if isinstance(base_val, np.ndarray):
        base_val = base_val[0]
    pred_val = cand_tree.predict(trans_x)[0]

    additivity_error = abs(pred_val - (base_val + np.sum(shap_vals)))
    assert additivity_error < 1e-10, f"SHAP additivity error too large: {additivity_error}"


def test_calibration_artifacts_validity():
    """11. Verify candidate calibration quantiles monotonicity and nominal coverage levels."""
    path = ROOT_DIR / "models" / "candidate_v1_2_conformal_calibration.json"
    with open(path, "r", encoding="utf-8") as f:
        cal = json.load(f)

    thresh = cal["calibration_thresholds"]
    q80 = thresh["0.80"]["threshold_q"]
    q90 = thresh["0.90"]["threshold_q"]
    q95 = thresh["0.95"]["threshold_q"]

    assert abs(q80 - 0.4244) < 1e-3
    assert abs(q90 - 0.5984) < 1e-3
    assert abs(q95 - 0.7788) < 1e-3
    assert q80 < q90 < q95, "Calibration quantiles must be strictly monotonically increasing"


def test_shadow_serving_isolation():
    """12. Assert shadow serving telemetry operates in isolation without user response impact."""
    rec = shadow_manager.evaluate_shadow(champion_pred=6.50, challenger_pred=6.42, prediction_id="unit-test-shadow")
    assert rec["champion_prediction"] == 6.50
    assert rec["challenger_prediction"] == 6.42
    assert abs(rec["difference"] - 0.08) < 1e-4

    cand_config = registry_manager.get_challengers()[1]["shadow_serving_config"]
    assert cand_config["affect_user_response"] is False
    assert cand_config["enabled"] is True


def test_no_automatic_promotion_rule():
    """13. Assert governance policy strictly blocks candidate promotion without human approval."""
    can_promote, reason = registry_manager.can_promote_challenger(
        "candidate_v1_2_revalidated",
        evaluation_metrics={"sample_count": 201, "empirical_coverage": 0.9104},
        has_human_approval=False
    )
    assert can_promote is False
    assert "human governance" in reason.lower()


def test_no_automatic_retraining_rule():
    """14. Assert central governance policy strictly forbids automated retraining."""
    policy = registry_manager._data["governance_policy"]
    assert policy["automatic_retraining_allowed"] is False
    assert policy["automatic_promotion_allowed"] is False
    assert policy["promotion_requires_human_approval"] is True
