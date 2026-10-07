"""Tests for Phase 15: Final Real-World Validation & Model Decision.

Validates:
1. Eligibility Gate Verification (Shadow duration < 14 days, Verified labels < 100, Paired rows = 0).
2. Phase 15 state evaluates strictly to BLOCKED / INSUFFICIENT EVIDENCE.
3. Historical offline records (4,998) cannot count as production evidence.
4. Champion model integrity (phase5_tuned_extra_trees.joblib invariant).
5. Candidate model integrity (candidate_v1_2_revalidated.joblib invariant).
6. Point prediction metrics truthfully report DATA_NOT_AVAILABLE in absence of ground truth.
7. Conformal uncertainty artifacts are preserved without retraining.
8. Conformal empirical coverage on production reports DATA_NOT_AVAILABLE.
9. Operational latency adheres to authoritative SLA P95 < 150 ms.
10. Drift monitoring reports DATA_NOT_AVAILABLE.
11. Final Decision evaluates strictly to OPTION C — INSUFFICIENT EVIDENCE.
12. Promotion remains strictly BLOCKED and human approval remains REQUIRED.
"""

import json
import hashlib
from pathlib import Path
import pytest

from app.governance import (
    registry_manager,
    shadow_manager,
    feedback_engine,
    GovernanceEvaluator
)

ROOT_DIR = Path(__file__).resolve().parent.parent

CHAMPION_EXPECTED_HASH = "a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8"
CANDIDATE_EXPECTED_HASH = "aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc"
CHAMPION_CALIB_EXPECTED_HASH = "22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b"
CANDIDATE_CALIB_EXPECTED_HASH = "b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af"


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def test_1_eligibility_gate_unfulfilled():
    """Verify that mandatory Phase 15 promotion prerequisites are checked and unfulfilled."""
    stat = shadow_manager.get_shadow_status()
    label_stat = feedback_engine.get_verified_label_counter()

    # Requirement 1: Shadow duration >= 14 days
    assert stat["required_days"] == 14
    assert stat["elapsed_days"] < 14.0
    assert stat["is_14_days_completed"] is False

    # Requirement 2: Verified post-deployment labels >= 100
    assert label_stat["target_count"] == 100
    assert label_stat["verified_count"] < 100
    assert label_stat["threshold_met"] is False

    # Requirement 3: Paired observations exist
    assert label_stat["paired_rows"] == 0


def test_2_phase15_blocked_due_to_insufficient_evidence():
    """Assert Phase 15 state evaluates to BLOCKED with reason INSUFFICIENT REAL-WORLD EVIDENCE."""
    stat = shadow_manager.get_shadow_status()
    label_stat = feedback_engine.get_verified_label_counter()

    is_eligible = stat["is_14_days_completed"] and label_stat["threshold_met"] and (label_stat["paired_rows"] >= 100)
    assert is_eligible is False

    # Final decision must be Option C
    decision = "INSUFFICIENT EVIDENCE" if not is_eligible else "EVALUATE"
    assert decision == "INSUFFICIENT EVIDENCE"


def test_3_historical_offline_data_excluded():
    """Verify that historical offline records cannot be counted as production evidence."""
    is_hist, reason = feedback_engine.is_historical_contamination({"is_historical": True})
    assert is_hist is True

    is_hist_src, _ = feedback_engine.is_historical_contamination({"provenance": {"source": "offline_training_csv"}})
    assert is_hist_src is True

    # Rejection of historical record ingestion
    res = feedback_engine.ingest_single_verified_label(
        observation_id="hist_batch_phase15",
        observed_score=5.5,
        provenance={"source": "offline_dataset"}
    )
    assert res["status"] == "REJECTED"


def test_4_champion_model_integrity_invariant():
    """Assert Champion model file exists and SHA-256 signature is bit-for-bit unchanged."""
    champ_path = ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib"
    assert champ_path.exists()
    assert compute_sha256(champ_path) == CHAMPION_EXPECTED_HASH


def test_5_candidate_model_integrity_invariant():
    """Assert Candidate challenger model file exists and SHA-256 signature is bit-for-bit unchanged."""
    cand_path = ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib"
    assert cand_path.exists()
    assert compute_sha256(cand_path) == CANDIDATE_EXPECTED_HASH


def test_6_point_prediction_metrics_data_not_available():
    """Assert production point prediction metrics truthfully return DATA_NOT_AVAILABLE when ground truth is missing."""
    gov_metrics = GovernanceEvaluator.evaluate_production_governance_metrics([])
    assert gov_metrics["mae"] == "DATA_NOT_AVAILABLE"
    assert gov_metrics["rmse"] == "DATA_NOT_AVAILABLE"
    assert gov_metrics["r2"] == "DATA_NOT_AVAILABLE"
    assert gov_metrics["median_absolute_error"] == "DATA_NOT_AVAILABLE"
    assert gov_metrics["mean_error"] == "DATA_NOT_AVAILABLE"
    assert gov_metrics["paired_mae_differences"] == "DATA_NOT_AVAILABLE"
    assert gov_metrics["per_observation_winner"] == "DATA_NOT_AVAILABLE"


def test_7_conformal_calibration_artifacts_preserved():
    """Assert existing conformal calibration artifacts remain byte-for-byte intact without retraining."""
    champ_calib_path = ROOT_DIR / "models" / "phase7_1_conformal_calibration.json"
    cand_calib_path = ROOT_DIR / "models" / "candidate_v1_2_conformal_calibration.json"
    assert champ_calib_path.exists()
    assert cand_calib_path.exists()
    assert compute_sha256(champ_calib_path) == CHAMPION_CALIB_EXPECTED_HASH
    assert compute_sha256(cand_calib_path) == CANDIDATE_CALIB_EXPECTED_HASH


def test_8_conformal_coverage_data_not_available():
    """Assert empirical production conformal coverage returns DATA_NOT_AVAILABLE in absence of ground truth."""
    gov_metrics = GovernanceEvaluator.evaluate_production_governance_metrics([])
    assert gov_metrics["empirical_80_coverage"] == "DATA_NOT_AVAILABLE"
    assert gov_metrics["empirical_90_coverage"] == "DATA_NOT_AVAILABLE"
    assert gov_metrics["empirical_95_coverage"] == "DATA_NOT_AVAILABLE"
    assert gov_metrics["mean_interval_width"] == "DATA_NOT_AVAILABLE"


def test_9_operational_latency_sla():
    """Assert candidate benchmark latency satisfies authoritative SLA P95 < 150 ms."""
    stat = shadow_manager.get_shadow_status()
    assert stat["candidate_benchmark_p95_ms"] == 77.58
    assert stat["latency_sla_p95_ms"] == 150.0
    assert stat["candidate_benchmark_p95_ms"] < stat["latency_sla_p95_ms"]
    assert stat["latency_live_status"] in ["DATA_NOT_AVAILABLE", "OBSERVED"]


def test_10_drift_metrics_data_not_available():
    """Assert production drift statistics return DATA_NOT_AVAILABLE."""
    gov_metrics = GovernanceEvaluator.evaluate_production_governance_metrics([])
    assert gov_metrics["psi"] == "DATA_NOT_AVAILABLE"
    assert gov_metrics["ks_statistic"] == "DATA_NOT_AVAILABLE"
    assert gov_metrics["tvd"] == "DATA_NOT_AVAILABLE"
    assert gov_metrics["drift_status"] == "DATA_NOT_AVAILABLE"


def test_11_final_decision_option_c_retains_champion():
    """Assert final governance outcome is strictly OPTION C — INSUFFICIENT EVIDENCE, retaining Champion."""
    stat = shadow_manager.get_shadow_status()
    label_stat = feedback_engine.get_verified_label_counter()

    eligible = stat["is_14_days_completed"] and label_stat["threshold_met"]
    decision = "C. INSUFFICIENT EVIDENCE" if not eligible else "A. PROMOTE CANDIDATE"
    assert decision == "C. INSUFFICIENT EVIDENCE"

    # Champion must remain active
    champ = registry_manager.get_champion()
    assert champ["model_version"] == "phase5_tuned_extra_trees"
    assert champ["status"] == "CHAMPION"


def test_12_human_approval_required_no_auto_promotion():
    """Assert automatic promotion and automatic retraining are strictly disabled and human approval is required."""
    policy = registry_manager._data.get("governance_policy", {})
    assert policy.get("automatic_promotion_allowed") is False
    assert policy.get("automatic_retraining_allowed") is False
    assert policy.get("promotion_requires_human_approval") is True
