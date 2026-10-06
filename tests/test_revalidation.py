"""Unit tests for Phase 12: Controlled Model Improvement & Full ML Revalidation."""

import json
import hashlib
from pathlib import Path
import pytest
import numpy as np
import joblib

from app.configuration import settings
from app.governance import ModelRegistryManager

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_champion_immutability_and_hash():
    """Verify Champion model file and calibration remain completely untouched."""
    champ_path = ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib"
    assert champ_path.exists(), "Champion model file missing"
    with open(champ_path, "rb") as f:
        computed_hash = hashlib.sha256(f.read()).hexdigest()
    assert computed_hash.lower() == settings.MODEL_EXPECTED_HASH.lower(), "Champion SHA-256 altered!"

    calib_path = ROOT_DIR / "models" / "phase7_1_conformal_calibration.json"
    assert calib_path.exists(), "Champion calibration artifact missing"
    with open(calib_path, "r", encoding="utf-8") as f:
        calib_data = json.load(f)
    thresholds = calib_data["calibration_thresholds"]
    assert round(thresholds["0.80"]["threshold_q"], 4) == 0.4156
    assert round(thresholds["0.90"]["threshold_q"], 4) == 0.5942
    assert round(thresholds["0.95"]["threshold_q"], 4) == 0.7902


def test_candidate_v1_2_artifact_integrity():
    """Verify Candidate v1.2 joblib artifact and metadata integrity."""
    cand_path = ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib"
    assert cand_path.exists(), "Candidate v1.2 artifact does not exist"
    with open(cand_path, "rb") as f:
        cand_hash = hashlib.sha256(f.read()).hexdigest()

    meta_path = ROOT_DIR / "models" / "candidate_v1_2_metadata.json"
    assert meta_path.exists(), "Candidate v1.2 metadata missing"
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["artifact_hash"].lower() == cand_hash.lower()
    assert meta["data_mode"] == "SIMULATED_DEMONSTRATION"
    assert meta["model_version"] == "candidate_v1_2_revalidated"
    assert meta["hyperparameters"]["n_estimators"] == 250
    assert meta["hyperparameters"]["max_features"] == "sqrt"


def test_candidate_conformal_calibration_integrity():
    """Verify Candidate v1.2 conformal calibration schema and monotonicity."""
    calib_path = ROOT_DIR / "models" / "candidate_v1_2_conformal_calibration.json"
    assert calib_path.exists(), "Candidate conformal calibration missing"
    with open(calib_path, "r", encoding="utf-8") as f:
        calib = json.load(f)

    assert calib["candidate_version"] == "candidate_v1_2_revalidated"
    assert calib["data_mode"] == "SIMULATED_DEMONSTRATION"
    thresholds = calib["calibration_thresholds"]

    q80 = thresholds["0.80"]["threshold_q"]
    q90 = thresholds["0.90"]["threshold_q"]
    q95 = thresholds["0.95"]["threshold_q"]

    # Monotonicity of quantiles
    assert q80 < q90 < q95, f"Conformal quantiles violate monotonicity: q80={q80}, q90={q90}, q95={q95}"
    assert thresholds["0.90"]["empirical_holdout_coverage"] >= 0.85


def test_prediction_interval_ordering():
    """Verify Candidate v1.2 yields well-ordered prediction intervals: LB <= Pred <= UB."""
    cand_path = ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib"
    calib_path = ROOT_DIR / "models" / "candidate_v1_2_conformal_calibration.json"
    pipeline = joblib.load(cand_path)
    with open(calib_path, "r", encoding="utf-8") as f:
        calib = json.load(f)

    q90 = calib["calibration_thresholds"]["0.90"]["threshold_q"]

    # Sample input dataframe
    import pandas as pd
    sample_df = pd.DataFrame([{
        "Study_Hours": 5.0,
        "Age": 21,
        "Avg_Daily_Usage_Hours": 4.5,
        "Daily_Unlocks": 50,
        "Physical_Activity_Hours": 2.0,
        "Sleep_Hours_Per_Night": 7.0,
        "Stress_Level": "Moderate",
        "Gender": "Female",
        "Academic_Level": "Undergraduate",
        "Most_Used_Platform": "Instagram",
        "Purpose_Of_Use": "Social",
        "Grouped_country": "India"
    }])

    pred = float(pipeline.predict(sample_df)[0])
    lb = pred - q90
    ub = pred + q90

    assert lb < pred < ub, f"Prediction bounds ordering violated: {lb} <= {pred} <= {ub}"
    assert (ub - lb) == pytest.approx(2.0 * q90, rel=1e-4)


def test_registry_challenger_isolation_and_promotion_block():
    """Verify Candidate v1.2 is strictly registered as CHALLENGER and cannot be auto-promoted."""
    reg = ModelRegistryManager()
    challengers = reg.get_challengers()
    cand_versions = [c["model_version"] for c in challengers]
    assert "candidate_v1_2_revalidated" in cand_versions

    cand_entry = next(c for c in challengers if c["model_version"] == "candidate_v1_2_revalidated")
    assert cand_entry["status"] == "CHALLENGER"
    assert cand_entry["approval_status"] == "VALIDATING"
    assert cand_entry["deployment_status"] == "SHADOW_ONLY"
    assert cand_entry["shadow_serving_config"]["affect_user_response"] is False

    # Verify promotion gate blocks automatic promotion
    allowed, reason = reg.can_promote_challenger(
        "candidate_v1_2_revalidated",
        {"sample_count": 500, "empirical_coverage": 0.91},
        has_human_approval=False
    )
    assert allowed is False
    assert "Explicit human governance committee approval is required" in reason
