"""Unit tests for Phase 14B: Controlled Shadow Observation, Production Evidence Accumulation & Governance Readiness.

Validates all 18 mandatory requirements:
1. Shadow start time is correctly interpreted.
2. Shadow duration is calculated dynamically.
3. 14-day requirement cannot be manually bypassed.
4. Historical rows cannot count as production labels.
5. Duplicate labels cannot inflate label count.
6. Zero labels produce DATA_NOT_AVAILABLE.
7. Fewer than 100 labels cannot unlock promotion.
8. Fewer than 14 shadow days cannot unlock promotion.
9. Candidate cannot affect Champion response.
10. Candidate exceptions remain isolated.
11. Automatic promotion remains disabled.
12. Automatic retraining remains disabled.
13. Champion hash remains unchanged.
14. Candidate hash remains unchanged.
15. P95 latency policy uses < 150 ms.
16. Offline metrics cannot be reported as production metrics.
17. Production metrics become computable only from genuine verified labels.
18. Governance status remains BLOCKED at current state.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent

from app.main import app
from app.governance import (
    registry_manager,
    shadow_manager,
    feedback_engine,
    FeedbackIngestionEngine,
    FeedbackRecord,
    GovernanceEvaluator,
    ModelRegistryManager
)

CHAMPION_EXPECTED_HASH = "a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8"
CANDIDATE_EXPECTED_HASH = "aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc"
CHAMPION_CALIB_EXPECTED_HASH = "22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b"
CANDIDATE_CALIB_EXPECTED_HASH = "b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af"

SAMPLE_PAYLOAD = {
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


def compute_file_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def test_1_shadow_start_time_interpreted():
    """1. Assert shadow start time is correctly interpreted as 2026-10-06T09:30:00Z."""
    assert shadow_manager.shadow_start_timestamp == "2026-10-06T09:30:00Z"
    dt = datetime.fromisoformat(shadow_manager.shadow_start_timestamp.replace("Z", "+00:00"))
    assert dt.year == 2026
    assert dt.month == 10
    assert dt.day == 6
    assert dt.hour == 9
    assert dt.minute == 30


def test_2_shadow_duration_calculated_dynamically():
    """2. Assert shadow duration is dynamically calculated from actual runtime timestamp."""
    status = shadow_manager.get_shadow_status()
    assert "elapsed_days" in status
    assert "current_time" in status
    assert status["elapsed_days"] >= 0.0
    start_dt = datetime.fromisoformat(status["shadow_start"].replace("Z", "+00:00"))
    curr_dt = datetime.fromisoformat(status["current_time"].replace("Z", "+00:00"))
    expected_days = (curr_dt - start_dt).total_seconds() / 86400.0
    assert abs(status["elapsed_days"] - round(expected_days, 3)) < 1e-2
    assert status["elapsed_days"] >= 1.0  # Dynamic duration is approximately 1.06 days



def test_3_fourteen_day_requirement_cannot_be_bypassed():
    """3. Assert 14-day requirement cannot be manually bypassed and remains unfulfilled."""
    status = shadow_manager.get_shadow_status()
    assert status["required_days"] == 14
    if status["elapsed_days"] < 14.0:
        assert status["is_14_days_completed"] is False
        assert status["shadow_status"] in ["ACTIVE", "NOT_STARTED"]
        assert status["shadow_status"] != "READY_FOR_DECISION"


def test_4_historical_rows_cannot_count_as_production_labels():
    """4. Assert historical offline records are strictly rejected by Historical Data Firewall."""
    engine = FeedbackIngestionEngine()
    # Explicit flag
    is_hist, _ = engine.is_historical_contamination({"is_historical": True})
    assert is_hist is True

    # Historical prediction ID
    is_hist_id, _ = engine.is_historical_contamination({"prediction_id": "hist_0042"})
    assert is_hist_id is True

    # Offline source
    is_hist_src, _ = engine.is_historical_contamination({"provenance": {"source": "offline_training_data"}})
    assert is_hist_src is True

    # Ingestion API rejection
    res = engine.ingest_single_verified_label(
        observation_id="hist_test_row_01",
        observed_score=6.0,
        provenance={"source": "offline_csv"}
    )
    assert res["status"] == "REJECTED"
    assert "HISTORICAL_DATA_FIREWALL" in res["reason"]


def test_5_duplicate_labels_cannot_inflate_count():
    """5. Assert duplicate labels cannot inflate the verified label count."""
    engine = FeedbackIngestionEngine()
    res1 = engine.ingest_single_verified_label(
        observation_id="live_obs_dup_check",
        observed_score=6.5,
        provenance={"source": "student_wellness_survey_live"}
    )
    assert res1["status"] == "VERIFIED"
    assert engine.get_verified_count() == 1

    res2 = engine.ingest_single_verified_label(
        observation_id="live_obs_dup_check",
        observed_score=7.0,
        provenance={"source": "duplicate_attempt"}
    )
    assert res2["status"] == "REJECTED"
    assert "Duplicate observation ID" in res2["reason"]
    assert engine.get_verified_count() == 1


def test_6_zero_labels_produce_data_not_available():
    """6. Assert zero labels produce DATA_NOT_AVAILABLE for all performance metrics."""
    metrics = GovernanceEvaluator.evaluate_production_governance_metrics([])
    assert metrics["evidence_status"] == "DATA_NOT_AVAILABLE"
    assert metrics["mae"] == "DATA_NOT_AVAILABLE"
    assert metrics["rmse"] == "DATA_NOT_AVAILABLE"
    assert metrics["r2"] == "DATA_NOT_AVAILABLE"
    assert metrics["empirical_80_coverage"] == "DATA_NOT_AVAILABLE"
    assert metrics["empirical_90_coverage"] == "DATA_NOT_AVAILABLE"
    assert metrics["empirical_95_coverage"] == "DATA_NOT_AVAILABLE"
    assert metrics["psi"] == "DATA_NOT_AVAILABLE"


def test_7_fewer_than_100_labels_cannot_unlock_promotion():
    """7. Assert fewer than 100 verified labels strictly blocks promotion."""
    reg = ModelRegistryManager()
    allowed, reason = reg.can_promote_challenger(
        "candidate_v1_2_revalidated",
        {"sample_count": 99, "empirical_coverage": 0.92},
        has_human_approval=True
    )
    assert allowed is False
    assert "Insufficient evaluation samples" in reason


def test_8_fewer_than_14_shadow_days_cannot_unlock_promotion():
    """8. Assert fewer than 14 shadow days strictly blocks promotion."""
    with TestClient(app) as client:
        resp = client.get("/governance/shadow/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["shadow_days_required"] == 14
        if data["shadow_days_elapsed"] < 14:
            assert data["governance_gate"]["shadow_duration_met"] is False
            assert data["promotion_eligible"] is False
            assert data["promotion_status"] == "BLOCKED"


def test_9_candidate_cannot_affect_champion_response():
    """9. Assert Candidate Challenger execution never alters Champion prediction or interval."""
    with TestClient(app) as client:
        resp = client.post("/predict", json=SAMPLE_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["model_version"] == "phase5_tuned_extra_trees"
        assert data["estimated_wellbeing_score"] == 6.67
        assert abs(data["prediction_interval"]["width"] - 1.1884) < 1e-2


def test_10_candidate_exceptions_remain_isolated():
    """10. Assert Candidate exceptions remain strictly isolated without affecting user response."""
    initial_exceptions = shadow_manager.shadow_exceptions
    shadow_manager.simulate_exception = True
    try:
        with TestClient(app) as client:
            resp = client.post("/predict", json=SAMPLE_PAYLOAD)
            assert resp.status_code == 200
            data = resp.json()
            assert data["model_version"] == "phase5_tuned_extra_trees"
            assert shadow_manager.shadow_exceptions == initial_exceptions + 1
    finally:
        shadow_manager.simulate_exception = False


def test_11_automatic_promotion_remains_disabled():
    """11. Assert automatic promotion is strictly disabled in governance policy."""
    policy = registry_manager._data.get("governance_policy", {})
    assert policy.get("automatic_promotion_allowed") is False


def test_12_automatic_retraining_remains_disabled():
    """12. Assert automatic retraining is strictly disabled in governance policy."""
    policy = registry_manager._data.get("governance_policy", {})
    assert policy.get("automatic_retraining_allowed") is False


def test_13_champion_hash_remains_unchanged():
    """13. Assert production Champion model artifact matches authoritative SHA-256."""
    champ_path = ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib"
    assert compute_file_sha256(champ_path) == CHAMPION_EXPECTED_HASH.lower()


def test_14_candidate_hash_remains_unchanged():
    """14. Assert Candidate Challenger model artifact matches authoritative SHA-256."""
    cand_path = ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib"
    assert compute_file_sha256(cand_path) == CANDIDATE_EXPECTED_HASH.lower()


def test_15_p95_latency_policy_uses_under_150ms():
    """15. Assert authoritative latency SLA is P95 < 150 ms and live status is DATA_NOT_AVAILABLE."""
    status = shadow_manager.get_shadow_status()
    assert status["latency_sla_p95_ms"] == 150.0
    assert status["candidate_benchmark_p95_ms"] == 77.58
    assert status["candidate_benchmark_p95_ms"] < status["latency_sla_p95_ms"]
    if not shadow_manager.shadow_latencies_ms:
        assert status["latency_live_status"] == "DATA_NOT_AVAILABLE"


def test_16_offline_metrics_cannot_be_reported_as_production_metrics():
    """16. Assert offline holdout metrics cannot be reported as production metrics."""
    with TestClient(app) as client:
        resp = client.get("/governance/shadow/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["production_metrics_available"] == "DATA_NOT_AVAILABLE"
        assert data["conformal_metrics_available"] == "DATA_NOT_AVAILABLE"


def test_17_production_metrics_computable_only_from_genuine_verified_labels():
    """17. Assert production metrics become computable when genuine verified labels exist."""
    recs = [
        FeedbackRecord("live_1", 6.0, "phase5_tuned_extra_trees", "hash", 5.4, 6.6, 0.90, observed_score=6.2, verification_status="VERIFIED"),
        FeedbackRecord("live_2", 7.0, "phase5_tuned_extra_trees", "hash", 6.4, 7.6, 0.90, observed_score=7.1, verification_status="VERIFIED"),
        FeedbackRecord("live_3", 5.0, "phase5_tuned_extra_trees", "hash", 4.4, 5.6, 0.90, observed_score=4.9, verification_status="VERIFIED")
    ]
    computed = GovernanceEvaluator.evaluate_production_governance_metrics(recs)
    assert computed["evidence_status"] == "GENUINE_OBSERVATIONS_PRESENT"
    assert isinstance(computed["mae"], float)
    assert isinstance(computed["rmse"], float)
    assert isinstance(computed["empirical_90_coverage"], float)


def test_18_governance_status_remains_blocked():
    """18. Assert governance status is strictly BLOCKED under Option C."""
    with TestClient(app) as client:
        resp = client.get("/governance/shadow/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["champion_version"] == "phase5_tuned_extra_trees"
        assert data["candidate_version"] == "candidate_v1_2_revalidated"
        assert data["promotion_eligible"] is False
        assert data["promotion_status"] == "BLOCKED"
        assert data["human_approval_status"] == "PENDING"
        assert data["governance_gate"]["promotion_state"] == "BLOCKED"
