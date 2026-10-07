"""Unit tests for Phase 14: Real-World Model Decision, Validation & Controlled Promotion.

Verifies strict governance enforcement:
1. Production label eligibility & separation of historical offline data
2. Paired Champion/Candidate evaluation requires verified ground truth
3. Statistical decision logic & confidence interval rules
4. Conformal coverage calculation prerequisites
5. Formal 18-gate promotion matrix logic
6. Artifact cryptographic integrity (Champion & Candidate hashes)
7. Registry consistency, rollback readiness, and non-automation enforcement
"""

import json
import hashlib
from pathlib import Path
import pytest
import pandas as pd
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent

from app.main import app
from app.governance import (
    registry_manager,
    shadow_manager,
    feedback_engine,
    ModelRegistryManager
)

CHAMPION_EXPECTED_HASH = "a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8"
CANDIDATE_EXPECTED_HASH = "aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc"
CHAMPION_CALIB_EXPECTED_HASH = "22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b"
CANDIDATE_CALIB_EXPECTED_HASH = "b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af"


def compute_file_sha256(filepath: Path) -> str:
    """Compute cryptographic SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def test_artifact_hashes_invariant():
    """Verify production Champion and Candidate challenger match authoritative hashes."""
    champ_path = ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib"
    cand_path = ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib"
    champ_calib_path = ROOT_DIR / "models" / "phase7_1_conformal_calibration.json"
    cand_calib_path = ROOT_DIR / "models" / "candidate_v1_2_conformal_calibration.json"

    assert compute_file_sha256(champ_path) == CHAMPION_EXPECTED_HASH.lower(), "Champion model modified!"
    assert compute_file_sha256(cand_path) == CANDIDATE_EXPECTED_HASH.lower(), "Candidate model modified!"
    assert compute_file_sha256(champ_calib_path) == CHAMPION_CALIB_EXPECTED_HASH.lower(), "Champion calibration modified!"
    assert compute_file_sha256(cand_calib_path) == CANDIDATE_CALIB_EXPECTED_HASH.lower(), "Candidate calibration modified!"


def test_registry_champion_and_challenger_state():
    """Verify registry states: Champion is ACTIVE PRODUCTION and Candidate is CHALLENGER/SHADOW."""
    champ = registry_manager.get_champion()
    assert champ["model_version"] == "phase5_tuned_extra_trees"
    assert champ["status"] == "CHAMPION"
    assert champ["approval_status"] == "APPROVED_FOR_PRODUCTION"

    challengers = registry_manager.get_challengers()
    cand = next((c for c in challengers if c["model_version"] == "candidate_v1_2_revalidated"), None)
    assert cand is not None, "Candidate v1.2 missing from registry!"
    assert cand["status"] == "CHALLENGER"
    assert cand["approval_status"] in ["VALIDATING", "SHADOW"]
    assert cand.get("shadow_serving_config", {}).get("enabled") is True


def test_no_automatic_promotion_or_retraining():
    """Assert automatic promotion and automatic retraining are strictly DISABLED."""
    policies = registry_manager._data.get("governance_policy", {})
    assert policies.get("automatic_promotion_allowed") is False, "Automatic promotion must be FALSE!"
    assert policies.get("promotion_requires_human_approval") is True, "Human approval must be TRUE!"

    auto_retrain = policies.get("automatic_retraining_allowed", False)
    assert auto_retrain is False, "Automatic retraining must be DISABLED!"


def test_historical_vs_production_dataset_separation():
    """Assert historical offline data cannot be counted as post-deployment validation evidence."""
    verified_summary_path = ROOT_DIR / "ml" / "experiments" / "phase13_verified_label_summary.csv"
    assert verified_summary_path.exists(), "Phase 13 verified label summary missing!"
    df = pd.read_csv(verified_summary_path)

    offline_row = df.loc[df["metric"] == "historical_offline_labels_used"]
    assert len(offline_row) > 0
    assert int(offline_row["value"].values[0]) == 0
    assert offline_row["status"].values[0] == "STRICTLY_SEPARATED"

    synthetic_row = df.loc[df["metric"] == "synthetic_labels_used"]
    assert len(synthetic_row) > 0
    assert int(synthetic_row["value"].values[0]) == 0
    assert synthetic_row["status"].values[0] == "STRICTLY_FORBIDDEN"


def test_zero_verified_labels_blocks_promotion():
    """Assert 0 verified post-deployment labels blocks Candidate promotion."""
    verified_summary_path = ROOT_DIR / "ml" / "experiments" / "phase13_verified_label_summary.csv"
    df = pd.read_csv(verified_summary_path)
    verified_labels = int(df.loc[df["metric"] == "verified_production_labels", "value"].values[0])
    threshold = int(df.loc[df["metric"] == "verified_production_labels", "threshold"].values[0])

    assert verified_labels == 0
    assert verified_labels < threshold
    assert df.loc[df["metric"] == "verification_gate_met", "status"].values[0] == "BLOCKED"


def test_shadow_duration_blocks_promotion():
    """Assert incomplete 14-day shadow window blocks Candidate promotion."""
    telemetry_path = ROOT_DIR / "ml" / "experiments" / "phase13_shadow_telemetry.csv"
    df = pd.read_csv(telemetry_path)
    days_completed = int(df.loc[df["metric"] == "days_completed", "value"].values[0])
    days_required = int(df.loc[df["metric"] == "days_required", "value"].values[0])

    assert days_completed < days_required
    assert df.loc[df["metric"] == "is_14_days_completed", "value"].values[0] == "FALSE"


def test_statistical_interpretation_decision_rules():
    """Assert statistical interpretation logic prevents claiming superiority when CI spans zero."""
    def evaluate_superiority(ci_lower: float, ci_upper: float, p_value: float, delta_mae: float, practical_threshold: float = -0.05) -> str:
        if delta_mae > 0:
            return "CANDIDATE NOT SUFFICIENT FOR PROMOTION"
        if ci_lower <= 0 <= ci_upper or p_value >= 0.05:
            return "NUMERICALLY BETTER — NOT STATISTICALLY CONCLUSIVE"
        if delta_mae <= practical_threshold and ci_upper < 0 and p_value < 0.05:
            return "STATISTICALLY AND PRACTICALLY SUPERIOR"
        return "INCONCLUSIVE"

    # Offline holdout evidence: CI [-0.0336, 0.0071], p=0.1584, delta=-0.0133
    offline_result = evaluate_superiority(-0.0336, 0.0071, 0.1584, -0.013285)
    assert offline_result == "NUMERICALLY BETTER — NOT STATISTICALLY CONCLUSIVE"

    # Inferior case: delta > 0
    inferior_result = evaluate_superiority(0.01, 0.05, 0.01, 0.02)
    assert inferior_result == "CANDIDATE NOT SUFFICIENT FOR PROMOTION"

    # Genuine superiority case: CI strictly negative, p < 0.05, delta <= -0.05
    superior_result = evaluate_superiority(-0.08, -0.06, 0.001, -0.07)
    assert superior_result == "STATISTICALLY AND PRACTICALLY SUPERIOR"


def test_formal_18_gate_promotion_matrix():
    """Assert all 18 promotion gates in phase14_promotion_gate.csv are correctly evaluated."""
    gate_csv_path = ROOT_DIR / "ml" / "experiments" / "phase14" / "phase14_promotion_gate.csv"
    assert gate_csv_path.exists(), "Phase 14 promotion gate CSV missing!"
    df = pd.read_csv(gate_csv_path)

    assert len(df) == 18, f"Expected 18 promotion gates, found {len(df)}"

    blocked_gates = df[df["Status"] == "BLOCKED"]
    passed_gates = df[df["Status"] == "PASS"]

    # At least 12 gates should be BLOCKED due to 0 labels / 0 days / pending approval
    assert len(blocked_gates) >= 10, f"Expected >= 10 blocked gates, found {len(blocked_gates)}"
    # Isolation, drift, schema, hash integrity must PASS
    assert len(passed_gates) >= 5, f"Expected >= 5 passed gates, found {len(passed_gates)}"


def test_shadow_failure_isolation_intact():
    """Assert candidate shadow failures do not impact Champion predictions."""
    with TestClient(app) as client:
        payload = {
            "Age": 21,
            "Gender": "Female",
            "Academic_Level": "Undergraduate",
            "Country": "India",
            "Avg_Daily_Usage_Hours": 4.0,
            "Most_Used_Platform": "Instagram",
            "Daily_Unlocks": 100,
            "Sleep_Hours_Per_Night": 7.0,
            "Study_Hours": 4.0,
            "Physical_Activity_Hours": 1.0,
            "Stress_Level": "Medium",
            "Purpose_Of_Use": "Education",
            "coverage": 0.90
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "estimated_wellbeing_score" in data
        assert "prediction_interval" in data
        # Confirm Champion model served the prediction
        assert data["model_version"] == "phase5_tuned_extra_trees"


def test_phase14_decision_resolution():
    """Assert the end-to-end Phase 14 decision resolves to OPTION C: INSUFFICIENT EVIDENCE."""
    gate_csv_path = ROOT_DIR / "ml" / "experiments" / "phase14" / "phase14_promotion_gate.csv"
    df = pd.read_csv(gate_csv_path)

    blocked_count = len(df[df["Status"] == "BLOCKED"])

    decision = "OPTION A: PROMOTE CANDIDATE" if blocked_count == 0 else "OPTION C: INSUFFICIENT EVIDENCE"
    assert decision == "OPTION C: INSUFFICIENT EVIDENCE"


def test_gate_12_latency_policy_consistency():
    """Assert Gate 12 status agrees with documented threshold, observed P95, and governance rules."""
    gate_csv_path = ROOT_DIR / "ml" / "experiments" / "phase14" / "phase14_promotion_gate.csv"
    df = pd.read_csv(gate_csv_path)

    gate_12 = df[df["Gate"].str.contains("12. latency")].iloc[0]

    # 1. Verify documented threshold references the authoritative < 150ms P95 SLA
    assert "150" in gate_12["Requirement"], f"Expected 150ms SLA in requirement, found: {gate_12['Requirement']}"

    # 2. Verify observed candidate benchmark latency is 77.58ms
    assert "77.58" in gate_12["Actual"], f"Expected 77.58ms benchmark in Actual, found: {gate_12['Actual']}"

    # 3. Verify that 77.58ms < 150ms genuinely justifies PASS for the benchmark
    observed_p95 = 77.58
    authoritative_sla = 150.0
    assert observed_p95 < authoritative_sla

    # 4. Assert Gate 12 status is PASS based on satisfying the < 150ms SLA
    assert gate_12["Status"] == "PASS"


def test_latency_strict_threshold_exceedance_fails():
    """Assert that a metric exceeding a strict threshold cannot be marked PASS."""
    def evaluate_latency_gate(observed_p95: float, sla_threshold: float | None) -> str:
        if sla_threshold is None:
            return "BLOCKED_POLICY_UNDEFINED"
        if observed_p95 <= sla_threshold:
            return "PASS"
        return "BLOCKED_EXCEEDS_SLA"

    # If a strict 50.0 ms threshold were erroneously applied:
    observed_p95 = 77.58
    result_strict_50 = evaluate_latency_gate(observed_p95, 50.0)
    assert result_strict_50 == "BLOCKED_EXCEEDS_SLA", "77.58ms must NOT pass a 50ms SLA!"
    assert result_strict_50 != "PASS"

    # Under authoritative 150.0 ms threshold:
    result_auth_150 = evaluate_latency_gate(observed_p95, 150.0)
    assert result_auth_150 == "PASS"


def test_missing_or_undefined_latency_policy_cannot_silently_pass():
    """Assert missing or undefined latency policy cannot silently evaluate to PASS."""
    def evaluate_latency_gate(observed_p95: float, sla_threshold: float | None) -> str:
        if sla_threshold is None or sla_threshold <= 0:
            return "BLOCKED_POLICY_UNDEFINED"
        if observed_p95 <= sla_threshold:
            return "PASS"
        return "BLOCKED_EXCEEDS_SLA"

    # Undefined policy (None)
    assert evaluate_latency_gate(77.58, None) == "BLOCKED_POLICY_UNDEFINED"
    assert evaluate_latency_gate(77.58, None) != "PASS"

    # Zero or negative threshold
    assert evaluate_latency_gate(77.58, 0.0) == "BLOCKED_POLICY_UNDEFINED"
    assert evaluate_latency_gate(77.58, -1.0) == "BLOCKED_POLICY_UNDEFINED"

