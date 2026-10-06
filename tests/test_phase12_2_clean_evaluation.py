"""Unit tests for Phase 12.2: Clean Champion vs Candidate Head-to-Head Evaluation."""

import json
import hashlib
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split

ROOT_DIR = Path(__file__).resolve().parent.parent
from app.monitoring import TOP10_COUNTRIES

CHAMP_EXPECTED_HASH = "a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8"
CAND_EXPECTED_HASH = "aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc"

@pytest.fixture(scope="module")
def clean_eval_data():
    data_path = ROOT_DIR / "ml" / "data" / "Student Social Media And Mental Health Impact.csv"
    raw_df = pd.read_csv(data_path).drop_duplicates()
    raw_df["Grouped_country"] = raw_df["Country"].apply(lambda c: c if c in TOP10_COUNTRIES else "Other")

    p5_train, p5_holdout = train_test_split(raw_df, test_size=1000, random_state=42)
    p12_dev, p12_holdout = train_test_split(raw_df, test_size=1000, random_state=1242)

    def compute_fingerprint(row):
        row_str = "|".join([f"{k}:{v}" for k, v in sorted(row.items())])
        return hashlib.sha256(row_str.encode("utf-8")).hexdigest()

    clean_idx = p5_holdout.index.intersection(p12_holdout.index)
    clean_df = raw_df.loc[clean_idx].copy()
    clean_df["row_fingerprint"] = clean_df.apply(compute_fingerprint, axis=1)

    return {
        "raw_df": raw_df,
        "p5_train": p5_train,
        "p5_holdout": p5_holdout,
        "p12_dev": p12_dev,
        "p12_holdout": p12_holdout,
        "clean_df": clean_df
    }


def test_champion_sha_matches_expected():
    """1. Verify production Champion artifact SHA-256 matches expected authoritative hash."""
    champ_path = ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib"
    assert champ_path.exists()
    with open(champ_path, "rb") as f:
        computed = hashlib.sha256(f.read()).hexdigest()
    assert computed.lower() == CHAMP_EXPECTED_HASH.lower()


def test_candidate_sha_matches_expected():
    """2. Verify Candidate artifact SHA-256 matches expected authoritative hash."""
    cand_path = ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib"
    assert cand_path.exists()
    with open(cand_path, "rb") as f:
        computed = hashlib.sha256(f.read()).hexdigest()
    assert computed.lower() == CAND_EXPECTED_HASH.lower()


def test_clean_common_evaluation_size(clean_eval_data):
    """3. Verify clean common evaluation subset size is exactly 201 records."""
    assert len(clean_eval_data["clean_df"]) == 201


def test_clean_set_unique_fingerprints(clean_eval_data):
    """4. Verify clean set has exactly 201 unique cryptographic fingerprints."""
    assert clean_eval_data["clean_df"]["row_fingerprint"].nunique() == 201


def test_clean_set_zero_overlap_phase5_train(clean_eval_data):
    """5. Verify clean common subset has zero overlap with Phase 5 Champion training data."""
    clean_set = set(clean_eval_data["clean_df"].index)
    p5_train_set = set(clean_eval_data["p5_train"].index)
    assert len(clean_set.intersection(p5_train_set)) == 0


def test_clean_set_zero_overlap_phase12_dev(clean_eval_data):
    """6. Verify clean common subset has zero overlap with Phase 12 Candidate dev pool."""
    clean_set = set(clean_eval_data["clean_df"].index)
    p12_dev_set = set(clean_eval_data["p12_dev"].index)
    assert len(clean_set.intersection(p12_dev_set)) == 0


def test_champion_predictions_length(clean_eval_data):
    """7. Verify Champion predictions array length equals 201."""
    champ = joblib.load(ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib")
    feature_cols = [
        "Study_Hours", "Age", "Avg_Daily_Usage_Hours", "Daily_Unlocks",
        "Physical_Activity_Hours", "Sleep_Hours_Per_Night", "Stress_Level",
        "Gender", "Academic_Level", "Most_Used_Platform", "Purpose_Of_Use",
        "Grouped_country"
    ]
    preds = champ.predict(clean_eval_data["clean_df"][feature_cols])
    assert len(preds) == 201


def test_candidate_predictions_length(clean_eval_data):
    """8. Verify Candidate predictions array length equals 201."""
    cand = joblib.load(ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib")
    feature_cols = [
        "Study_Hours", "Age", "Avg_Daily_Usage_Hours", "Daily_Unlocks",
        "Physical_Activity_Hours", "Sleep_Hours_Per_Night", "Stress_Level",
        "Gender", "Academic_Level", "Most_Used_Platform", "Purpose_Of_Use",
        "Grouped_country"
    ]
    preds = cand.predict(clean_eval_data["clean_df"][feature_cols])
    assert len(preds) == 201


def test_prediction_arrays_not_identical(clean_eval_data):
    """9. Verify Champion and Candidate prediction arrays are distinct."""
    feature_cols = [
        "Study_Hours", "Age", "Avg_Daily_Usage_Hours", "Daily_Unlocks",
        "Physical_Activity_Hours", "Sleep_Hours_Per_Night", "Stress_Level",
        "Gender", "Academic_Level", "Most_Used_Platform", "Purpose_Of_Use",
        "Grouped_country"
    ]
    champ = joblib.load(ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib")
    cand = joblib.load(ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib")

    champ_preds = champ.predict(clean_eval_data["clean_df"][feature_cols])
    cand_preds = cand.predict(clean_eval_data["clean_df"][feature_cols])

    diffs = np.abs(champ_preds - cand_preds)
    assert np.max(diffs) > 0.5
    assert np.sum(diffs == 0) == 0


def test_metrics_computed_from_exact_same_rows(clean_eval_data):
    """10. Verify metrics are evaluated on the exact same row indices."""
    comp_csv = ROOT_DIR / "ml" / "experiments" / "phase12_2_prediction_comparison.csv"
    assert comp_csv.exists()
    comp_df = pd.read_csv(comp_csv)
    assert len(comp_df) == 201
    assert set(comp_df["row_fingerprint"]) == set(clean_eval_data["clean_df"]["row_fingerprint"])


def test_candidate_calibration_hash_matches_candidate():
    """11. Verify candidate calibration source model hash matches candidate artifact hash."""
    calib_path = ROOT_DIR / "models" / "candidate_v1_2_conformal_calibration.json"
    with open(calib_path, "r", encoding="utf-8") as f:
        calib = json.load(f)
    assert calib["source_model_hash"].lower() == CAND_EXPECTED_HASH.lower()


def test_champion_calibration_hash_matches_champion():
    """12. Verify champion calibration source model hash matches champion artifact hash."""
    calib_path = ROOT_DIR / "models" / "phase7_1_conformal_calibration.json"
    with open(calib_path, "r", encoding="utf-8") as f:
        calib = json.load(f)
    assert calib["source_model_hash"].lower() == CHAMP_EXPECTED_HASH.lower()


def test_no_production_model_artifact_modified():
    """13. Verify production Champion model artifact remains completely unmodified."""
    champ_path = ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib"
    with open(champ_path, "rb") as f:
        assert hashlib.sha256(f.read()).hexdigest().lower() == CHAMP_EXPECTED_HASH.lower()


def test_no_calibration_artifact_modified():
    """14. Verify Champion calibration quantiles remain strictly identical."""
    calib_path = ROOT_DIR / "models" / "phase7_1_conformal_calibration.json"
    with open(calib_path, "r", encoding="utf-8") as f:
        calib = json.load(f)
    t = calib["calibration_thresholds"]
    assert round(t["0.80"]["threshold_q"], 4) == 0.4156
    assert round(t["0.90"]["threshold_q"], 4) == 0.5942
    assert round(t["0.95"]["threshold_q"], 4) == 0.7902
