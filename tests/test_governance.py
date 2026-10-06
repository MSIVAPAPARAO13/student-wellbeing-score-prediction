"""Unit tests for Phase 11: Verified Post-Deployment Feedback, Model Governance, Candidate Validation & Shadow Serving."""

import json
import hashlib
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.configuration import settings
from app.governance import (
    FeedbackRecord,
    FeedbackIngestionEngine,
    GovernanceEvaluator,
    ModelRegistryManager,
    ShadowServingManager,
    FEEDBACK_STATES,
    MODEL_LIFECYCLE_STATES
)

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_feedback_schema_and_states():
    """Verify feedback record initialization, schema fields, and lifecycle state constraints."""
    rec = FeedbackRecord(
        prediction_id="pred-001",
        predicted_score=6.25,
        model_version="phase5_tuned_extra_trees",
        model_hash=settings.MODEL_EXPECTED_HASH,
        lower_bound=5.66,
        upper_bound=6.84,
        requested_coverage=0.90,
        observed_score=6.10,
        verification_status="VERIFIED"
    )
    d = rec.to_dict()
    assert d["prediction_id"] == "pred-001"
    assert d["predicted_score"] == 6.25
    assert d["observed_score"] == 6.10
    assert d["verification_status"] in FEEDBACK_STATES
    assert d["verification_status"] == "VERIFIED"


def test_invalid_label_rejection():
    """Verify rejection of invalid, infinite, NaN, or out-of-domain observed scores."""
    engine = FeedbackIngestionEngine()
    raw_batch = [
        # Valid entry
        {
            "prediction_id": "valid-1",
            "predicted_score": 6.0,
            "model_version": "phase5_tuned_extra_trees",
            "model_hash": settings.MODEL_EXPECTED_HASH,
            "lower_bound": 5.4,
            "upper_bound": 6.6,
            "observed_score": 6.5,
            "verification_status": "VERIFIED"
        },
        # Out-of-bounds score (e.g. 15.0 when domain is [1.0, 10.0])
        {
            "prediction_id": "invalid-out-of-bounds",
            "predicted_score": 6.0,
            "model_version": "phase5_tuned_extra_trees",
            "model_hash": settings.MODEL_EXPECTED_HASH,
            "lower_bound": 5.4,
            "upper_bound": 6.6,
            "observed_score": 15.0,
            "verification_status": "VERIFIED"
        },
        # NaN score
        {
            "prediction_id": "invalid-nan",
            "predicted_score": 6.0,
            "model_version": "phase5_tuned_extra_trees",
            "model_hash": settings.MODEL_EXPECTED_HASH,
            "lower_bound": 5.4,
            "upper_bound": 6.6,
            "observed_score": float("nan"),
            "verification_status": "VERIFIED"
        },
        # Negative score
        {
            "prediction_id": "invalid-neg",
            "predicted_score": 6.0,
            "model_version": "phase5_tuned_extra_trees",
            "model_hash": settings.MODEL_EXPECTED_HASH,
            "lower_bound": 5.4,
            "upper_bound": 6.6,
            "observed_score": -2.5,
            "verification_status": "VERIFIED"
        }
    ]

    report = engine.ingest_records(raw_batch)
    assert report["total_received"] == 4
    assert report["verified"] == 1
    assert report["invalid_score"] == 3
    assert len(engine.get_verified_records()) == 1


def test_duplicate_feedback_handling():
    """Verify deduplication of feedback records sharing identical prediction_id."""
    engine = FeedbackIngestionEngine()
    entry = {
        "prediction_id": "dup-id-123",
        "predicted_score": 6.0,
        "model_version": "phase5_tuned_extra_trees",
        "model_hash": settings.MODEL_EXPECTED_HASH,
        "lower_bound": 5.4,
        "upper_bound": 6.6,
        "observed_score": 6.2,
        "verification_status": "VERIFIED"
    }

    report = engine.ingest_records([entry, entry])
    assert report["total_received"] == 2
    assert report["verified"] == 1
    assert report["duplicates"] == 1


def test_verified_vs_unverified_evaluation_isolation():
    """Ensure unverified or pending feedback is never used in evaluation calculations."""
    engine = FeedbackIngestionEngine()
    batch = [
        {
            "prediction_id": "rec-1",
            "predicted_score": 6.0,
            "model_version": "phase5_tuned_extra_trees",
            "model_hash": settings.MODEL_EXPECTED_HASH,
            "lower_bound": 5.4,
            "upper_bound": 6.6,
            "observed_score": 6.2,
            "verification_status": "VERIFIED"
        },
        {
            "prediction_id": "rec-2",
            "predicted_score": 7.0,
            "model_version": "phase5_tuned_extra_trees",
            "model_hash": settings.MODEL_EXPECTED_HASH,
            "lower_bound": 6.4,
            "upper_bound": 7.6,
            "observed_score": None,  # Pending
            "verification_status": "PENDING_VERIFICATION"
        }
    ]
    engine.ingest_records(batch)
    verified = engine.get_verified_records()
    assert len(verified) == 1
    assert verified[0].prediction_id == "rec-1"


def test_metric_calculations_and_interval_coverage():
    """Verify correctness of MAE, RMSE, R², empirical coverage, and width calculations."""
    records = []
    # 5 test records: errors [0.1, -0.2, 0.0, 0.1, -0.1]
    # Width = 1.0 (LB = pred - 0.5, UB = pred + 0.5)
    for i, (pred, obs) in enumerate([(5.0, 5.1), (6.0, 5.8), (7.0, 7.0), (8.0, 8.1), (9.0, 8.9)]):
        records.append(FeedbackRecord(
            prediction_id=f"test-{i}",
            predicted_score=pred,
            model_version="phase5_tuned_extra_trees",
            model_hash=settings.MODEL_EXPECTED_HASH,
            lower_bound=pred - 0.5,
            upper_bound=pred + 0.5,
            observed_score=obs,
            verification_status="VERIFIED"
        ))

    metrics = GovernanceEvaluator.evaluate_performance(records, nominal_coverage=0.90)
    assert metrics["sample_count"] == 5
    assert metrics["sample_status"] == "INSUFFICIENT_SAMPLE"  # Under 30 threshold
    assert abs(metrics["mae"] - 0.10) < 1e-2
    assert metrics["empirical_coverage"] == 1.0  # All 5 within ±0.5
    assert metrics["mean_interval_width"] == 1.0


def test_registry_integrity_and_champion_linkage():
    """Verify Model Registry structure, Champion identification, and artifact SHA-256 match."""
    reg = ModelRegistryManager()
    valid, msg = reg.verify_champion_integrity()
    assert valid is True, f"Champion integrity failed: {msg}"

    champ = reg.get_champion()
    assert champ["model_version"] == "phase5_tuned_extra_trees"
    assert champ["status"] == "CHAMPION"
    assert champ["artifact_hash"].lower() == settings.MODEL_EXPECTED_HASH.lower()
    assert champ["approval_status"] == "APPROVED_FOR_PRODUCTION"


def test_challenger_isolation_and_promotion_restrictions():
    """Verify candidate challenger models cannot be promoted automatically or without human approval."""
    reg = ModelRegistryManager()
    challengers = reg.get_challengers()
    assert len(challengers) >= 1
    cand = challengers[0]
    assert cand["status"] == "CHALLENGER"
    assert cand["approval_status"] == "SHADOW"

    # Attempt automatic promotion without human approval
    eval_metrics = {"sample_count": 500, "empirical_coverage": 0.92, "r2": 0.93}
    allowed, reason = reg.can_promote_challenger(cand["model_version"], eval_metrics, has_human_approval=False)
    assert allowed is False
    assert "human governance committee approval is required" in reason

    # Attempt promotion with insufficient samples (< 100)
    small_metrics = {"sample_count": 40, "empirical_coverage": 0.92}
    allowed, reason = reg.can_promote_challenger(cand["model_version"], small_metrics, has_human_approval=True)
    assert allowed is False
    assert "Insufficient evaluation samples" in reason


def test_governance_rules_no_automatic_retraining():
    """Verify governance policy strictly disallows automatic retraining."""
    reg = ModelRegistryManager()
    policy = reg._data.get("governance_policy", {})
    assert policy.get("automatic_retraining_allowed") is False
    assert policy.get("automatic_promotion_allowed") is False


def test_shadow_serving_isolation():
    """Verify shadow serving logs comparison data without altering primary prediction."""
    shadow = ShadowServingManager()
    rec = shadow.evaluate_shadow(champion_pred=6.50, challenger_pred=6.42, prediction_id="shadow-01")
    assert rec["champion_prediction"] == 6.50
    assert rec["challenger_prediction"] == 6.42
    assert abs(rec["difference"] - 0.08) < 1e-4

    summary = shadow.get_summary()
    assert summary["sample_count"] >= 1
    assert summary["mean_absolute_difference"] > 0.0


def test_read_only_governance_endpoints(client):
    """Verify GET /governance/champion, /governance/registry, and /governance/shadow return HTTP 200."""
    r_champ = client.get("/governance/champion")
    assert r_champ.status_code == 200
    data_champ = r_champ.json()
    assert data_champ["integrity_verified"] is True
    assert data_champ["champion"]["status"] == "CHAMPION"

    r_reg = client.get("/governance/registry")
    assert r_reg.status_code == 200
    data_reg = r_reg.json()
    assert data_reg["champion_version"] == "phase5_tuned_extra_trees"
    assert len(data_reg["challengers"]) >= 1
    assert "audit_log" in data_reg

    r_shad = client.get("/governance/shadow")
    assert r_shad.status_code == 200


def test_production_safety_predict_endpoint_unaffected(client):
    """Verify /predict output strictly reflects the Champion model and is unaffected by candidate models."""
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
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["model_version"] == "phase5_tuned_extra_trees"
    assert res_data["estimated_wellbeing_score"] == 6.67
    assert res_data["prediction_interval"]["nominal_coverage"] == 0.90
    assert abs(res_data["prediction_interval"]["width"] - 1.1884) < 1e-2
