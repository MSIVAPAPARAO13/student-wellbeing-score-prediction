"""Unit tests for Phase 12.1: Holdout Lineage, Champion Evaluation Integrity & Schema Consistency Audit."""

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

@pytest.fixture(scope="module")
def dataset():
    data_path = ROOT_DIR / "ml" / "data" / "Student Social Media And Mental Health Impact.csv"
    raw_df = pd.read_csv(data_path).drop_duplicates()
    raw_df["Grouped_country"] = raw_df["Country"].apply(lambda c: c if c in TOP10_COUNTRIES else "Other")
    return raw_df


@pytest.fixture(scope="module")
def partitions(dataset):
    p5_train, p5_holdout = train_test_split(dataset, test_size=1000, random_state=42)
    p12_dev, p12_holdout = train_test_split(dataset, test_size=1000, random_state=1242)
    return p5_train, p5_holdout, p12_dev, p12_holdout


def compute_row_fingerprint(row):
    row_str = "|".join([f"{k}:{v}" for k, v in sorted(row.items())])
    return hashlib.sha256(row_str.encode("utf-8")).hexdigest()


def test_row_fingerprint_determinism(dataset):
    """Verify row fingerprinting is deterministic and sensitive to feature changes."""
    row = dataset.iloc[0].to_dict()
    fp1 = compute_row_fingerprint(row)
    fp2 = compute_row_fingerprint(row)
    assert fp1 == fp2, "Fingerprint is not deterministic across identical calls"

    # Perturb one feature
    perturbed = row.copy()
    perturbed["Study_Hours"] = float(perturbed["Study_Hours"]) + 1.0
    fp_perturbed = compute_row_fingerprint(perturbed)
    assert fp1 != fp_perturbed, "Fingerprint failed to detect feature perturbation"


def test_partition_intersection_logic(partitions):
    """Verify row-level partition intersections and quantify Champion holdout contamination."""
    p5_train, p5_holdout, p12_dev, p12_holdout = partitions

    p5_train_fps = set(p5_train.apply(compute_row_fingerprint, axis=1))
    p5_holdout_fps = set(p5_holdout.apply(compute_row_fingerprint, axis=1))
    p12_dev_fps = set(p12_dev.apply(compute_row_fingerprint, axis=1))
    p12_holdout_fps = set(p12_holdout.apply(compute_row_fingerprint, axis=1))

    # Champion contamination assertion: exactly 799 rows (79.9%)
    champ_contam = len(p5_train_fps.intersection(p12_holdout_fps))
    assert champ_contam == 799, f"Expected 799 contaminated rows, found {champ_contam}"

    # Champion unseen assertion: exactly 201 rows (20.1%)
    champ_unseen = len(p5_holdout_fps.intersection(p12_holdout_fps))
    assert champ_unseen == 201, f"Expected 201 unseen rows, found {champ_unseen}"

    # Candidate dev pool isolation assertion: exactly 0 rows
    cand_leak = len(p12_dev_fps.intersection(p12_holdout_fps))
    assert cand_leak == 0, f"Candidate training leakage detected: {cand_leak} rows"


def test_champion_contamination_detection(partitions):
    """Verify Champion demonstrates memorization on contaminated holdout rows vs normal generalization on unseen rows."""
    p5_train, p5_holdout, p12_dev, p12_holdout = partitions
    champ = joblib.load(ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib")

    feature_cols = [
        "Study_Hours", "Age", "Avg_Daily_Usage_Hours", "Daily_Unlocks",
        "Physical_Activity_Hours", "Sleep_Hours_Per_Night", "Stress_Level",
        "Gender", "Academic_Level", "Most_Used_Platform", "Purpose_Of_Use",
        "Grouped_country"
    ]
    target_col = "Mental_Health_Score"

    contam_idx = p12_holdout.index.intersection(p5_train.index)
    unseen_idx = p12_holdout.index.intersection(p5_holdout.index)

    y_cont = p12_holdout.loc[contam_idx, target_col].values
    preds_cont = champ.predict(p12_holdout.loc[contam_idx, feature_cols])
    rmse_cont = np.sqrt(np.mean((y_cont - preds_cont)**2))

    y_unseen = p12_holdout.loc[unseen_idx, target_col].values
    preds_unseen = champ.predict(p12_holdout.loc[unseen_idx, feature_cols])
    rmse_unseen = np.sqrt(np.mean((y_unseen - preds_unseen)**2))

    # Contaminated rows show near-zero memorization error (< 0.05)
    assert rmse_cont < 0.05, f"Contaminated RMSE unexpectedly high: {rmse_cont}"
    # Unseen rows show realistic survey generalization error (> 0.30)
    assert rmse_unseen > 0.30, f"Unseen RMSE unexpectedly low: {rmse_unseen}"


def test_candidate_isolation(partitions):
    """Verify Candidate training pool has zero intersection with its evaluation holdout."""
    _, _, p12_dev, p12_holdout = partitions
    dev_set = set(p12_dev.index)
    holdout_set = set(p12_holdout.index)
    assert len(dev_set.intersection(holdout_set)) == 0, "Candidate training pool overlaps with holdout"


def test_prediction_array_identity(partitions):
    """Verify Champion and Candidate produce distinct predictions on the Phase 12 holdout."""
    _, _, _, p12_holdout = partitions
    feature_cols = [
        "Study_Hours", "Age", "Avg_Daily_Usage_Hours", "Daily_Unlocks",
        "Physical_Activity_Hours", "Sleep_Hours_Per_Night", "Stress_Level",
        "Gender", "Academic_Level", "Most_Used_Platform", "Purpose_Of_Use",
        "Grouped_country"
    ]
    champ = joblib.load(ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib")
    cand = joblib.load(ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib")

    champ_preds = champ.predict(p12_holdout[feature_cols])
    cand_preds = cand.predict(p12_holdout[feature_cols])

    diffs = np.abs(champ_preds - cand_preds)
    assert np.max(diffs) > 1.0, "Models lack substantial prediction divergence"
    assert np.sum(diffs == 0) == 0, "Models share identical prediction records"


def test_calibration_source_hash():
    """Verify candidate calibration artifact references candidate artifact SHA-256."""
    cand_path = ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib"
    with open(cand_path, "rb") as f:
        cand_hash = hashlib.sha256(f.read()).hexdigest()

    calib_path = ROOT_DIR / "models" / "candidate_v1_2_conformal_calibration.json"
    with open(calib_path, "r", encoding="utf-8") as f:
        calib = json.load(f)

    assert calib["source_model_hash"].lower() == cand_hash.lower()
    thresholds = calib["calibration_thresholds"]
    assert thresholds["0.80"]["threshold_q"] == 0.4244
    assert thresholds["0.90"]["threshold_q"] == 0.5984
    assert thresholds["0.95"]["threshold_q"] == 0.7788


def test_feature_schema_consistency():
    """Verify both Champion and Candidate expect 12 input features."""
    champ = joblib.load(ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib")
    cand = joblib.load(ROOT_DIR / "models" / "candidate_v1_2_revalidated.joblib")

    # In both ColumnTransformers, count columns across transformers
    champ_preproc = champ.named_steps["preprocessor"]
    cand_preproc = cand.named_steps["preprocessor"]

    champ_cols = []
    for _, _, cols in champ_preproc.transformers:
        champ_cols.extend(cols if isinstance(cols, list) else [cols])
    cand_cols = []
    for _, _, cols in cand_preproc.transformers:
        cand_cols.extend(cols if isinstance(cols, list) else [cols])

    assert len(set(champ_cols)) == 12
    assert len(set(cand_cols)) == 12
    assert set(champ_cols) == set(cand_cols)


def test_stress_level_category_consistency():
    """Verify production Champion encodes Stress_Level with 4 ordinal categories: ['Low', 'Medium', 'High', 'Very High']."""
    champ = joblib.load(ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib")
    encoder = champ.named_steps["preprocessor"].named_transformers_["ordinal"].named_steps["encoder"]
    categories = encoder.categories_[0].tolist()
    expected = ["Low", "Medium", "High", "Very High"]
    assert categories == expected, f"Unexpected Stress_Level categories in Champion: {categories}"


def test_preprocessing_metadata_consistency():
    """Verify production Champion uses log1p + StandardScaler on Study_Hours, not RobustScaler."""
    champ = joblib.load(ROOT_DIR / "models" / "phase5_tuned_extra_trees.joblib")
    skewed_steps = champ.named_steps["preprocessor"].named_transformers_["skewed"].named_steps
    step_names = list(skewed_steps.keys())
    assert "log" in step_names, "Missing log transformation step on Study_Hours in production Champion"
    assert "scaler" in step_names
    from sklearn.preprocessing import StandardScaler
    assert isinstance(skewed_steps["scaler"], StandardScaler), "Study_Hours scaler is not StandardScaler"
