"""Unit tests for Phase 13: Real-World Production Validation & Controlled Shadow Observation."""

import json
import hashlib
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent

from app.main import app
from app.configuration import settings
from app.governance import (
    registry_manager,
    shadow_manager,
    feedback_engine,
    FeedbackIngestionEngine,
    ModelRegistryManager
)

CHAMPION_EXPECTED_HASH = "a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8"
CANDIDATE_EXPECTED_HASH = "aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc"
CHAMPION_CALIB_EXPECTED_HASH = "22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b"
CANDIDATE_CALIB_EXPECTED_HASH = "b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af"

SAMPLE_REQUEST_PAYLOAD = {
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


def test_champion_remains_production():
    """1. Assert production Champion is locked in production and matches authoritative hash."""
    champ = registry_manager.get_champion()
    assert champ["model_version"] == "phase5_tuned_extra_trees"
    assert champ["status"] == "CHAMPION"
    assert champ["approval_status"] == "APPROVED_FOR_PRODUCTION"
    assert champ["artifact_hash"].lower() == CHAMPION_EXPECTED_HASH.lower()


def test_candidate_remains_shadow_only():
    """2. Assert Candidate v1.2 remains challenger in shadow mode with zero user response routing."""
    challengers = registry_manager.get_challengers()
    cand = next((c for c in challengers if c["model_version"] == "candidate_v1_2_revalidated"), None)
    assert cand is not None, "Candidate v1.2 missing from registry!"
    assert cand["status"] == "CHALLENGER"
    assert cand["approval_status"] in ["VALIDATING", "SHADOW"]
    shadow_cfg = cand.get("shadow_serving_config", {})
    assert shadow_cfg.get("enabled") is True
    assert shadow_cfg.get("affect_user_response") is False


def test_candidate_cannot_alter_user_response():
    """3. Assert public /predict returns Champion prediction and calibration exclusively."""
    with TestClient(app) as client:
        response = client.post("/predict", json=SAMPLE_REQUEST_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert data["estimated_wellbeing_score"] == 6.67
        assert data["model_version"] == "phase5_tuned_extra_trees"
        assert "5-Fold Cross-Conformal" in data["uncertainty_method"]
        assert "prediction_interval" in data
        assert data["prediction_interval"]["nominal_coverage"] == 0.90
        assert abs(data["prediction_interval"]["width"] - 1.1884) < 1e-2
        assert 1.0 <= data["estimated_wellbeing_score"] <= 10.0
        assert data["prediction_interval"]["lower"] <= data["estimated_wellbeing_score"] <= data["prediction_interval"]["upper"]


def test_candidate_exception_isolation():
    """4. Assert that candidate scoring exception NEVER propagates into user response."""
    initial_exceptions = shadow_manager.shadow_exceptions
    shadow_manager.simulate_exception = True
    try:
        with TestClient(app) as client:
            response = client.post("/predict", json=SAMPLE_REQUEST_PAYLOAD)
            assert response.status_code == 200
            data = response.json()
            assert data["model_version"] == "phase5_tuned_extra_trees"
            assert shadow_manager.shadow_exceptions == initial_exceptions + 1
    finally:
        shadow_manager.simulate_exception = False


def test_candidate_timeout_isolation():
    """5. Assert that candidate scoring timeout NEVER propagates into user response."""
    initial_timeouts = shadow_manager.shadow_timeouts
    shadow_manager.simulate_timeout = True
    try:
        with TestClient(app) as client:
            response = client.post("/predict", json=SAMPLE_REQUEST_PAYLOAD)
            assert response.status_code == 200
            data = response.json()
            assert data["model_version"] == "phase5_tuned_extra_trees"
            assert shadow_manager.shadow_timeouts == initial_timeouts + 1
    finally:
        shadow_manager.simulate_timeout = False


def test_verified_feedback_status_enforcement():
    """6. Assert that feedback ingestion engine enforces proper verification status."""
    engine = FeedbackIngestionEngine()
    batch = [
        {
            "prediction_id": "test_pid_001",
            "predicted_score": 6.5,
            "model_version": "phase5_tuned_extra_trees",
            "model_hash": CHAMPION_EXPECTED_HASH,
            "lower_bound": 5.9,
            "upper_bound": 7.1,
            "observed_score": 6.8,
            "verification_status": "VERIFIED"
        }
    ]
    report = engine.ingest_records(batch)
    assert report["verified"] == 1
    records = engine.get_verified_records()
    assert len(records) == 1
    assert records[0].prediction_id == "test_pid_001"


def test_unverified_labels_excluded():
    """7. Assert that unverified labels (PENDING_VERIFICATION) are excluded from ground truth."""
    engine = FeedbackIngestionEngine()
    batch = [
        {
            "prediction_id": "test_pid_002",
            "predicted_score": 5.0,
            "model_version": "phase5_tuned_extra_trees",
            "model_hash": CHAMPION_EXPECTED_HASH,
            "lower_bound": 4.4,
            "upper_bound": 5.6,
            "observed_score": None,
            "verification_status": "PENDING_VERIFICATION"
        }
    ]
    engine.ingest_records(batch)
    records = engine.get_verified_records()
    assert len(records) == 0, "Unverified record must NOT be treated as ground truth!"


def test_rejected_labels_excluded():
    """8. Assert that out-of-domain or invalid observed scores are strictly rejected and excluded."""
    engine = FeedbackIngestionEngine()
    batch = [
        {
            "prediction_id": "test_pid_003",
            "predicted_score": 7.0,
            "model_version": "phase5_tuned_extra_trees",
            "model_hash": CHAMPION_EXPECTED_HASH,
            "lower_bound": 6.4,
            "upper_bound": 7.6,
            "observed_score": 15.0,  # Invalid: outside [1.0, 10.0]
            "verification_status": "VERIFIED"
        }
    ]
    report = engine.ingest_records(batch)
    assert report["invalid_score"] == 1
    records = engine.get_verified_records()
    assert len(records) == 0, "Rejected record must NOT be included in verified records!"


def test_duplicate_verified_labels_rejected():
    """9. Assert that duplicate prediction IDs in feedback are strictly rejected."""
    engine = FeedbackIngestionEngine()
    entry = {
        "prediction_id": "test_pid_dup",
        "predicted_score": 6.0,
        "model_version": "phase5_tuned_extra_trees",
        "model_hash": CHAMPION_EXPECTED_HASH,
        "lower_bound": 5.4,
        "upper_bound": 6.6,
        "observed_score": 6.2,
        "verification_status": "VERIFIED"
    }
    report = engine.ingest_records([entry, entry])
    assert report["duplicates"] == 1
    assert len(engine.get_verified_records()) == 1


def test_minimum_verified_label_counter():
    """10. Assert live verified label counter correctly reflects 0 / 100 at Phase 13 start."""
    counter = feedback_engine.get_verified_label_counter()
    assert counter["verified_count"] == 0
    assert counter["target_count"] == 100
    assert counter["display"] == "0 / 100"
    assert counter["threshold_met"] is False


def test_shadow_day_calculation():
    """11. Assert shadow day calculation tracks 14 days required and days remaining."""
    status = shadow_manager.get_shadow_status()
    assert status["shadow_start_timestamp"] == "2026-10-06T09:30:00Z"
    assert status["days_required"] == 14
    assert status["is_14_days_completed"] is False
    assert status["days_remaining"] == 14 - status["days_completed"]
    assert status["days_elapsed"] >= 0.0


def test_calibration_artifact_integrity():
    """12. Assert cryptographic SHA-256 integrity of both calibration artifacts."""
    champ_calib_path = ROOT_DIR / "models" / "phase7_1_conformal_calibration.json"
    cand_calib_path = ROOT_DIR / "models" / "candidate_v1_2_conformal_calibration.json"
    
    with open(champ_calib_path, "rb") as f:
        champ_calib_hash = hashlib.sha256(f.read()).hexdigest()
    with open(cand_calib_path, "rb") as f:
        cand_calib_hash = hashlib.sha256(f.read()).hexdigest()
        
    assert champ_calib_hash.lower() == CHAMPION_CALIB_EXPECTED_HASH.lower()
    assert cand_calib_hash.lower() == CANDIDATE_CALIB_EXPECTED_HASH.lower()


def test_model_artifact_hash_integrity():
    """13. Assert cryptographic SHA-256 integrity of both model joblib artifacts."""
    champ_path = ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib"
    cand_path = ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib"
    
    with open(champ_path, "rb") as f:
        champ_hash = hashlib.sha256(f.read()).hexdigest()
    with open(cand_path, "rb") as f:
        cand_hash = hashlib.sha256(f.read()).hexdigest()
        
    assert champ_hash.lower() == CHAMPION_EXPECTED_HASH.lower()
    assert cand_hash.lower() == CANDIDATE_EXPECTED_HASH.lower()


def test_monitoring_and_shadow_status_endpoints():
    """14. Assert /metrics and /governance/shadow/status endpoints are healthy and safe."""
    with TestClient(app) as client:
        # Check metrics
        m_resp = client.get("/metrics?format=json")
        assert m_resp.status_code == 200
        m_data = m_resp.json()
        assert "requests_total" in m_data
        
        # Check shadow status
        s_resp = client.get("/governance/shadow/status")
        assert s_resp.status_code == 200
        s_data = s_resp.json()
        assert "shadow_status" in s_data
        assert "verified_labels" in s_data
        assert s_data["governance_gate"]["promotion_state"] == "BLOCKED"
        assert s_data["governance_gate"]["verified_labels_met"] is False


def test_promotion_remains_blocked_below_required_gates():
    """15. Assert that Candidate promotion is strictly blocked when verified labels < 100."""
    reg = ModelRegistryManager()
    
    # 1. Blocked without human approval
    eval_metrics = {"sample_count": 500, "empirical_coverage": 0.92, "r2": 0.93}
    allowed, reason = reg.can_promote_challenger("candidate_v1_2_revalidated", eval_metrics, has_human_approval=False)
    assert allowed is False
    assert "human governance committee approval is required" in reason
    
    # 2. Blocked with insufficient samples (< 100)
    small_metrics = {"sample_count": 0, "empirical_coverage": 0.0}
    allowed_small, reason_small = reg.can_promote_challenger("candidate_v1_2_revalidated", small_metrics, has_human_approval=True)
    assert allowed_small is False
    assert "Insufficient evaluation samples" in reason_small
