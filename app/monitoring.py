"""Phase 10: Production Monitoring, Data Quality, Drift Detection & Observability.

This module provides privacy-first metrics collection, statistical drift computation
(PSI, KS-test, Total Variation Distance), severity classification, and a future
label-aware model performance evaluation framework.

Strict Privacy Rule:
NO raw student survey responses or personally identifiable records are stored in logs,
metrics, or telemetry. Only aggregate counts, summary statistics, and anonymized counters
are maintained in-memory.
"""

import time
import math
import threading
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats

# Authoritative feature lists
NUMERICAL_FEATURES = [
    "Age", "Avg_Daily_Usage_Hours", "Daily_Unlocks",
    "Sleep_Hours_Per_Night", "Study_Hours", "Physical_Activity_Hours"
]

CATEGORICAL_FEATURES = [
    "Gender", "Academic_Level", "Country",
    "Most_Used_Platform", "Stress_Level", "Purpose_Of_Use"
]

TOP10_COUNTRIES = [
    "Australia", "Canada", "France", "Germany", "India",
    "Mexico", "Other", "Turkey", "UK", "USA"
]

# Engineering Drift Severity Thresholds
# Note: These represent operational thresholds for investigation, not universal scientific constants.
PSI_NORMAL_THRESHOLD = 0.10
PSI_CRITICAL_THRESHOLD = 0.25

KS_PVALUE_THRESHOLD = 0.05
KS_STAT_CRITICAL_THRESHOLD = 0.15

TVD_NORMAL_THRESHOLD = 0.10
TVD_CRITICAL_THRESHOLD = 0.20


# =====================================================================
# Statistical Drift Detection Utilities
# =====================================================================

def calculate_psi(
    expected: Union[np.ndarray, pd.Series, List[float]],
    actual: Union[np.ndarray, pd.Series, List[float]],
    num_bins: int = 10,
    epsilon: float = 1e-4
) -> float:
    """Computes the Population Stability Index (PSI) between reference and production distributions.
    
    Formula:
        PSI = sum((Actual_% - Expected_%) * ln(Actual_% / Expected_%))
    """
    exp_arr = np.asarray(expected, dtype=float)
    act_arr = np.asarray(actual, dtype=float)

    # Filter out NaNs
    exp_arr = exp_arr[~np.isnan(exp_arr)]
    act_arr = act_arr[~np.isnan(act_arr)]

    if len(exp_arr) == 0 or len(act_arr) == 0:
        return 0.0

    # Determine quantile bin edges based on expected reference distribution
    quantiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(exp_arr, quantiles)
    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    # Remove duplicates from bin edges if quantiles collapse
    bin_edges = np.unique(bin_edges)
    if len(bin_edges) <= 2:
        # Fallback to uniform min-max binning
        min_v = min(np.min(exp_arr), np.min(act_arr))
        max_v = max(np.max(exp_arr), np.max(act_arr))
        if min_v == max_v:
            return 0.0
        bin_edges = np.linspace(min_v, max_v, num_bins + 1)
        bin_edges[0] = -np.inf
        bin_edges[-1] = np.inf

    # Calculate bin counts
    exp_counts, _ = np.histogram(exp_arr, bins=bin_edges)
    act_counts, _ = np.histogram(act_arr, bins=bin_edges)

    # Convert to proportions with epsilon smoothing to avoid log(0) or div-by-zero
    exp_pct = (exp_counts + epsilon) / (len(exp_arr) + epsilon * len(exp_counts))
    act_pct = (act_counts + epsilon) / (len(act_arr) + epsilon * len(act_counts))

    psi_val = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
    return float(max(0.0, psi_val))


def calculate_ks(
    expected: Union[np.ndarray, pd.Series, List[float]],
    actual: Union[np.ndarray, pd.Series, List[float]]
) -> Tuple[float, float]:
    """Computes two-sample Kolmogorov-Smirnov test statistic and asymptotic p-value."""
    exp_arr = np.asarray(expected, dtype=float)
    act_arr = np.asarray(actual, dtype=float)

    exp_arr = exp_arr[~np.isnan(exp_arr)]
    act_arr = act_arr[~np.isnan(act_arr)]

    if len(exp_arr) == 0 or len(act_arr) == 0:
        return 0.0, 1.0

    res = stats.ks_2samp(exp_arr, act_arr)
    return float(res.statistic), float(res.pvalue)


def calculate_tvd(
    expected_freqs: Dict[str, float],
    actual_freqs: Dict[str, float]
) -> float:
    """Computes Total Variation Distance (TVD) between categorical distributions.
    
    TVD = 0.5 * sum(|P(x) - Q(x)|) across all categories.
    Ranges from 0.0 (identical) to 1.0 (disjoint).
    """
    all_keys = set(expected_freqs.keys()).union(set(actual_freqs.keys()))
    if not all_keys:
        return 0.0

    tvd = 0.5 * sum(
        abs(expected_freqs.get(k, 0.0) - actual_freqs.get(k, 0.0))
        for k in all_keys
    )
    return float(tvd)


def classify_drift_severity(
    psi: Optional[float] = None,
    ks_stat: Optional[float] = None,
    ks_p: Optional[float] = None,
    tvd: Optional[float] = None
) -> str:
    """Classifies drift severity into 'Normal', 'Warning', or 'Critical' based on monitored metrics."""
    # Check Critical conditions
    if psi is not None and psi >= PSI_CRITICAL_THRESHOLD:
        return "Critical"
    if tvd is not None and tvd >= TVD_CRITICAL_THRESHOLD:
        return "Critical"
    if ks_stat is not None and ks_p is not None:
        if ks_stat >= KS_STAT_CRITICAL_THRESHOLD and ks_p < 0.01:
            return "Critical"

    # Check Warning conditions
    if psi is not None and psi >= PSI_NORMAL_THRESHOLD:
        return "Warning"
    if tvd is not None and tvd >= TVD_NORMAL_THRESHOLD:
        return "Warning"
    if ks_p is not None and ks_p < KS_PVALUE_THRESHOLD:
        return "Warning"

    return "Normal"


# =====================================================================
# Label-Aware Future Model Evaluation Framework
# =====================================================================

def evaluate_future_labels(
    y_true: Union[np.ndarray, List[float], pd.Series],
    y_pred: Union[np.ndarray, List[float], pd.Series],
    lower_bounds: Optional[Union[np.ndarray, List[float], pd.Series]] = None,
    upper_bounds: Optional[Union[np.ndarray, List[float], pd.Series]] = None,
    nominal_coverage: float = 0.90
) -> Dict[str, float]:
    """Evaluates regression accuracy and prediction interval coverage when verified production labels exist.
    
    This function must NOT be called with fabricated labels.
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)

    if len(yt) == 0 or len(yp) == 0:
        raise ValueError("Cannot evaluate empty ground truth or prediction array")
    if len(yt) != len(yp):
        raise ValueError(f"Length mismatch: {len(yt)} ground-truth labels vs {len(yp)} predictions")

    residuals = yt - yp
    mae = float(np.mean(np.abs(residuals)))
    rmse = float(np.sqrt(np.mean(residuals ** 2)))
    
    # R-squared calculation
    ss_tot = np.sum((yt - np.mean(yt)) ** 2)
    ss_res = np.sum(residuals ** 2)
    r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

    eval_result = {
        "sample_count": len(yt),
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
    }

    if lower_bounds is not None and upper_bounds is not None:
        lb = np.asarray(lower_bounds, dtype=float)
        ub = np.asarray(upper_bounds, dtype=float)
        if len(lb) == len(yt) and len(ub) == len(yt):
            covered = (yt >= lb) & (yt <= ub)
            emp_coverage = float(np.mean(covered))
            widths = ub - lb
            mean_width = float(np.mean(widths))
            eval_result.update({
                "nominal_coverage": nominal_coverage,
                "empirical_coverage": round(emp_coverage, 4),
                "coverage_error": round(emp_coverage - nominal_coverage, 4),
                "mean_interval_width": round(mean_width, 4)
            })

    return eval_result


# =====================================================================
# In-Memory Privacy-Safe Production Metrics Collector
# =====================================================================

class ProductionMetricsCollector:
    """Thread-safe in-memory metrics collector for production API observability.
    
    Preserves student privacy: no raw inputs, no survey answers, no identifiers stored.
    Maintains rolling buffers for percentiles and Prometheus-format counters.
    """

    def __init__(self, buffer_size: int = 1000):
        self._lock = threading.Lock()
        self._buffer_size = buffer_size

        # Counters
        self.api_requests_total: Dict[str, int] = {
            "/": 0,
            "/health": 0,
            "/predict": 0,
            "/explain": 0,
            "/docs": 0,
            "/metrics": 0,
            "other": 0
        }
        self.api_status_total: Dict[int, int] = {
            200: 0,
            400: 0,
            422: 0,
            500: 0,
            503: 0
        }
        self.predictions_total: int = 0
        self.explanations_total: int = 0
        self.validation_failures_total: int = 0

        # Latency samples (duration in ms) per endpoint
        self._latencies: Dict[str, List[float]] = {
            "/health": [],
            "/predict": [],
            "/explain": []
        }

        # Rolling buffers for prediction monitoring (strictly numeric float values)
        self._predicted_scores: List[float] = []
        self._interval_widths_90: List[float] = []

    def record_request(self, endpoint: str, status_code: int, duration_ms: float):
        """Records endpoint call, HTTP status, and duration."""
        with self._lock:
            norm_endpoint = endpoint if endpoint in self.api_requests_total else "other"
            self.api_requests_total[norm_endpoint] = self.api_requests_total.get(norm_endpoint, 0) + 1
            self.api_status_total[status_code] = self.api_status_total.get(status_code, 0) + 1

            if endpoint in self._latencies:
                buf = self._latencies[endpoint]
                buf.append(duration_ms)
                if len(buf) > self._buffer_size:
                    self._latencies[endpoint] = buf[-self._buffer_size:]

    def record_prediction(self, estimated_score: float, interval_width_90: Optional[float] = None):
        """Records predicted wellbeing score and 90% conformal interval width."""
        with self._lock:
            self.predictions_total += 1
            self._predicted_scores.append(float(estimated_score))
            if len(self._predicted_scores) > self._buffer_size:
                self._predicted_scores = self._predicted_scores[-self._buffer_size:]

            if interval_width_90 is not None:
                self._interval_widths_90.append(float(interval_width_90))
                if len(self._interval_widths_90) > self._buffer_size:
                    self._interval_widths_90 = self._interval_widths_90[-self._buffer_size:]

    def record_explanation(self):
        """Records explanation generation invocation."""
        with self._lock:
            self.explanations_total += 1

    def record_validation_failure(self):
        """Records incoming schema/range validation failure."""
        with self._lock:
            self.validation_failures_total += 1

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Returns consolidated API and prediction distribution summary stats."""
        with self._lock:
            def _stats(arr: List[float]) -> Dict[str, Optional[float]]:
                if not arr:
                    return {"count": 0, "p50": None, "p95": None, "p99": None, "mean": None}
                s_arr = np.sort(np.asarray(arr))
                return {
                    "count": len(s_arr),
                    "mean": round(float(np.mean(s_arr)), 2),
                    "min": round(float(np.min(s_arr)), 2),
                    "p50": round(float(np.percentile(s_arr, 50)), 2),
                    "p95": round(float(np.percentile(s_arr, 95)), 2),
                    "p99": round(float(np.percentile(s_arr, 99)), 2),
                    "max": round(float(np.max(s_arr)), 2),
                }

            pred_stats = _stats(self._predicted_scores)
            width_stats = _stats(self._interval_widths_90)

            return {
                "requests_total": dict(self.api_requests_total),
                "status_codes_total": dict(self.api_status_total),
                "predictions_total": self.predictions_total,
                "explanations_total": self.explanations_total,
                "validation_failures_total": self.validation_failures_total,
                "latency_ms": {
                    "/health": _stats(self._latencies["/health"]),
                    "/predict": _stats(self._latencies["/predict"]),
                    "/explain": _stats(self._latencies["/explain"]),
                },
                "predicted_score_distribution": pred_stats,
                "conformal_interval_90_width_distribution": width_stats,
            }

    def export_prometheus(self) -> str:
        """Exports metrics in standard Prometheus exposition format."""
        with self._lock:
            lines = [
                "# HELP api_requests_total Total number of HTTP requests processed by endpoint",
                "# TYPE api_requests_total counter",
            ]
            for ep, count in self.api_requests_total.items():
                lines.append(f'api_requests_total{{endpoint="{ep}"}} {count}')

            lines.extend([
                "# HELP api_status_codes_total Total HTTP response status codes returned",
                "# TYPE api_status_codes_total counter",
            ])
            for st, count in self.api_status_total.items():
                lines.append(f'api_status_codes_total{{status="{st}"}} {count}')

            lines.extend([
                "# HELP predictions_total Total number of wellbeing score predictions served",
                "# TYPE predictions_total counter",
                f"predictions_total {self.predictions_total}",
                "# HELP explanations_total Total number of TreeSHAP explanations served",
                "# TYPE explanations_total counter",
                f"explanations_total {self.explanations_total}",
                "# HELP validation_failures_total Total number of schema validation rejections",
                "# TYPE validation_failures_total counter",
                f"validation_failures_total {self.validation_failures_total}",
            ])

            # Latency p50 and p95 gauges
            lines.extend([
                "# HELP api_latency_ms Summary latency percentiles per endpoint",
                "# TYPE api_latency_ms gauge",
            ])
            for ep, lats in self._latencies.items():
                if lats:
                    p50 = float(np.percentile(lats, 50))
                    p95 = float(np.percentile(lats, 95))
                    lines.append(f'api_latency_ms{{endpoint="{ep}",quantile="0.50"}} {p50:.2f}')
                    lines.append(f'api_latency_ms{{endpoint="{ep}",quantile="0.95"}} {p95:.2f}')

            # Prediction score summary
            if self._predicted_scores:
                p_mean = float(np.mean(self._predicted_scores))
                lines.extend([
                    "# HELP predicted_wellbeing_score_mean Running mean of predicted scores",
                    "# TYPE predicted_wellbeing_score_mean gauge",
                    f"predicted_wellbeing_score_mean {p_mean:.4f}"
                ])

            return "\n".join(lines) + "\n"


# Global singleton instance
metrics_collector = ProductionMetricsCollector()
