"""Unit tests for Phase 10: Production Monitoring, Data Quality, Drift Detection, and Observability."""

import json
import hashlib
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.configuration import settings
from app.monitoring import (
    calculate_psi,
    calculate_ks,
    calculate_tvd,
    classify_drift_severity,
    evaluate_future_labels,
    metrics_collector,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES
)

client = TestClient(app)


def test_model_hash_monitoring():
    """Verify production model artifact SHA-256 matches frozen Phase 5 authoritative hash."""
    assert settings.MODEL_PATH.exists(), f"Model path {settings.MODEL_PATH} does not exist"
    with open(settings.MODEL_PATH, "rb") as f:
        computed_hash = hashlib.sha256(f.read()).hexdigest()
    assert computed_hash.lower() == settings.MODEL_EXPECTED_HASH.lower(), (
        f"Model hash mismatch! Computed: {computed_hash}, Expected: {settings.MODEL_EXPECTED_HASH}"
    )


def test_calibration_hash_monitoring():
    """Verify conformal calibration artifact integrity and source model hash linkage."""
    assert settings.CONFORMAL_PATH.exists(), f"Calibration path {settings.CONFORMAL_PATH} missing"
    with open(settings.CONFORMAL_PATH, "r", encoding="utf-8") as f:
        calib_data = json.load(f)

    assert "source_model_hash" in calib_data
    assert calib_data["source_model_hash"].lower() == settings.MODEL_EXPECTED_HASH.lower()
    assert "calibration_thresholds" in calib_data
    thresholds = calib_data["calibration_thresholds"]
    assert "0.80" in thresholds
    assert "0.90" in thresholds
    assert "0.95" in thresholds
    assert abs(thresholds["0.80"]["threshold_q"] - 0.4156) < 1e-3
    assert abs(thresholds["0.90"]["threshold_q"] - 0.5942) < 1e-3
    assert abs(thresholds["0.95"]["threshold_q"] - 0.7902) < 1e-3


def test_psi_identical_distributions():
    """Verify PSI is near zero and classified as Normal when comparing identical distributions."""
    np.random.seed(42)
    ref = np.random.normal(5.0, 1.5, size=2000)
    prod = np.random.normal(5.0, 1.5, size=2000)

    psi_val = calculate_psi(ref, prod)
    assert psi_val < 0.10, f"Expected PSI < 0.10 for identical distributions, got {psi_val}"
    severity = classify_drift_severity(psi=psi_val)
    assert severity == "Normal"


def test_psi_shifted_distributions():
    """Verify PSI detects strong distribution shift and triggers Critical classification."""
    np.random.seed(42)
    ref = np.random.normal(5.0, 1.0, size=2000)
    prod = np.random.normal(8.0, 1.5, size=2000)  # Significant shift

    psi_val = calculate_psi(ref, prod)
    assert psi_val >= 0.25, f"Expected PSI >= 0.25 for heavily shifted distributions, got {psi_val}"
    severity = classify_drift_severity(psi=psi_val)
    assert severity == "Critical"


def test_ks_statistic_monitoring():
    """Verify Kolmogorov-Smirnov test behavior for matching vs shifted samples."""
    np.random.seed(42)
    ref = np.random.uniform(1.0, 10.0, size=1000)
    prod_same = np.random.uniform(1.0, 10.0, size=1000)
    prod_drift = np.random.uniform(5.0, 15.0, size=1000)

    ks_stat_same, p_same = calculate_ks(ref, prod_same)
    assert p_same > 0.01, f"Expected high p-value for identical distributions, got {p_same}"

    ks_stat_drift, p_drift = calculate_ks(ref, prod_drift)
    assert p_drift < 0.001, f"Expected tiny p-value for shifted distributions, got {p_drift}"
    assert ks_stat_drift > 0.20


def test_categorical_tvd():
    """Verify Total Variation Distance correctly bounds categorical divergence."""
    ref_freqs = {"A": 0.50, "B": 0.30, "C": 0.20}
    same_freqs = {"A": 0.50, "B": 0.30, "C": 0.20}
    tvd_same = calculate_tvd(ref_freqs, same_freqs)
    assert tvd_same == 0.0
    assert classify_drift_severity(tvd=tvd_same) == "Normal"

    # Moderate shift
    mod_freqs = {"A": 0.40, "B": 0.35, "C": 0.25}
    tvd_mod = calculate_tvd(ref_freqs, mod_freqs)
    assert 0.0 < tvd_mod < 0.20

    # Severe disjoint shift
    crit_freqs = {"A": 0.0, "B": 0.0, "C": 0.0, "D": 1.0}
    tvd_crit = calculate_tvd(ref_freqs, crit_freqs)
    assert tvd_crit == 1.0
    assert classify_drift_severity(tvd=tvd_crit) == "Critical"


def test_drift_edge_cases():
    """Verify graceful handling of empty inputs, NaNs, and single-value inputs."""
    # Empty inputs
    assert calculate_psi([], []) == 0.0
    ks_stat, ks_p = calculate_ks([], [])
    assert ks_stat == 0.0 and ks_p == 1.0
    assert calculate_tvd({}, {}) == 0.0

    # All NaNs
    nan_arr = np.array([np.nan, np.nan])
    assert calculate_psi(nan_arr, nan_arr) == 0.0

    # Single-value arrays
    single = np.array([5.0, 5.0, 5.0, 5.0])
    assert calculate_psi(single, single) == 0.0


def test_future_label_evaluation_framework():
    """Verify evaluation of regression accuracy and prediction intervals when ground truth exists."""
    y_true = np.array([5.0, 6.0, 7.0, 8.0])
    y_pred = np.array([5.1, 5.9, 7.2, 7.8])
    lb = np.array([4.5, 5.3, 6.6, 7.2])
    ub = np.array([5.7, 6.5, 7.8, 8.4])

    eval_out = evaluate_future_labels(y_true, y_pred, lb, ub, nominal_coverage=0.90)

    assert eval_out["sample_count"] == 4
    assert abs(eval_out["mae"] - 0.15) < 1e-2
    assert eval_out["r2"] > 0.95
    assert eval_out["empirical_coverage"] == 1.0  # All 4 in bounds
    assert eval_out["mean_interval_width"] == 1.20


def test_privacy_in_memory_metrics():
    """Verify privacy constraints: no survey answers, names, or raw inputs in metrics."""
    metrics_summary = metrics_collector.get_summary_statistics()
    prom_text = metrics_collector.export_prometheus()

    # Disallowed strings that would indicate leaking raw student survey payloads
    forbidden_tokens = [
        "Study_Hours", "Avg_Daily_Usage_Hours", "Daily_Unlocks",
        "Physical_Activity_Hours", "Sleep_Hours_Per_Night",
        "Stress_Level", "Academic_Level", "Most_Used_Platform"
    ]
    for token in forbidden_tokens:
        assert token not in prom_text, f"Forbidden feature token {token} found in Prometheus export!"

    # Ensure summary structure only contains aggregate metrics
    assert "requests_total" in metrics_summary
    assert "status_codes_total" in metrics_summary
    assert "latency_ms" in metrics_summary
    assert "predicted_score_distribution" in metrics_summary


def test_metrics_endpoint_prometheus():
    """Verify GET /metrics returns HTTP 200 with standard Prometheus formatted counters."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
    content = response.text
    assert "api_requests_total" in content
    assert "predictions_total" in content
    assert "explanations_total" in content


def test_metrics_endpoint_json():
    """Verify GET /metrics?format=json returns HTTP 200 with valid JSON summary statistics."""
    response = client.get("/metrics?format=json")
    assert response.status_code == 200
    data = response.json()
    assert "requests_total" in data
    assert "status_codes_total" in data
    assert "predictions_total" in data
    assert "latency_ms" in data
