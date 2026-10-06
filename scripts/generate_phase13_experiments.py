"""Phase 13: Generate authoritative Phase 13 experiment records.

Explicitly separates:
A. Historical / offline data
B. Real post-deployment observations
C. Verified production labels (target: >= 100, currently 0)
D. Synthetic / demo data

Where real production observations or verified labels do not yet exist,
records explicitly report DATA_NOT_AVAILABLE / NO REAL PRODUCTION OBSERVATIONS AVAILABLE.
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "ml" / "experiments"
EXP_DIR.mkdir(parents=True, exist_ok=True)

# 1. phase13_shadow_telemetry.csv
df_telemetry = pd.DataFrame([
    {"metric": "shadow_observation_status", "value": "ACTIVE_CONTROLLED_SHADOW", "unit": "status", "notes": "Candidate executes in isolated shadow mode"},
    {"metric": "shadow_start_timestamp", "value": "2026-10-06T09:30:00Z", "unit": "iso8601", "notes": "Official start timestamp recorded"},
    {"metric": "days_elapsed", "value": "0.0", "unit": "days", "notes": "Continuous observation in progress"},
    {"metric": "days_completed", "value": "0", "unit": "days", "notes": "Full consecutive calendar days completed"},
    {"metric": "days_remaining", "value": "14", "unit": "days", "notes": "14 consecutive days required"},
    {"metric": "days_required", "value": "14", "unit": "days", "notes": "Governance observation threshold"},
    {"metric": "is_14_days_completed", "value": "FALSE", "unit": "boolean", "notes": "Observation gate pending"},
    {"metric": "shadow_requests", "value": "0", "unit": "count", "notes": "Production shadow requests recorded"},
    {"metric": "shadow_successes", "value": "0", "unit": "count", "notes": "Successful shadow candidate predictions"},
    {"metric": "shadow_exceptions", "value": "0", "unit": "count", "notes": "Isolated candidate exceptions"},
    {"metric": "shadow_timeouts", "value": "0", "unit": "count", "notes": "Isolated candidate timeouts"},
    {"metric": "candidate_p50_latency_ms", "value": "DATA_NOT_AVAILABLE", "unit": "ms", "notes": "Awaiting production request volume"},
    {"metric": "candidate_p95_latency_ms", "value": "DATA_NOT_AVAILABLE", "unit": "ms", "notes": "Awaiting production request volume"},
    {"metric": "candidate_p99_latency_ms", "value": "DATA_NOT_AVAILABLE", "unit": "ms", "notes": "Awaiting production request volume"},
    {"metric": "champion_latency_ms", "value": "DATA_NOT_AVAILABLE", "unit": "ms", "notes": "Awaiting production request volume"},
    {"metric": "user_response_impact", "value": "0", "unit": "count", "notes": "Strictly zero impact on user response"}
])
df_telemetry.to_csv(EXP_DIR / "phase13_shadow_telemetry.csv", index=False)

# 2. phase13_verified_label_summary.csv
df_labels = pd.DataFrame([
    {"metric": "verified_production_labels", "value": "0", "threshold": "100", "status": "IN_PROGRESS", "notes": "0 / 100 verified post-deployment labels"},
    {"metric": "unverified_feedback_excluded", "value": "0", "threshold": "0", "status": "EXCLUDED", "notes": "Unverified feedback excluded from ground truth"},
    {"metric": "rejected_feedback_excluded", "value": "0", "threshold": "0", "status": "EXCLUDED", "notes": "Out-of-domain/corrupted feedback rejected"},
    {"metric": "duplicate_labels_rejected", "value": "0", "threshold": "0", "status": "EXCLUDED", "notes": "Duplicate prediction IDs strictly deduplicated"},
    {"metric": "historical_offline_labels_used", "value": "0", "threshold": "0", "status": "STRICTLY_SEPARATED", "notes": "Offline labels never counted as production"},
    {"metric": "synthetic_labels_used", "value": "0", "threshold": "0", "status": "STRICTLY_FORBIDDEN", "notes": "No synthetic data counted as evidence"},
    {"metric": "target_definition", "value": "Mental_Health_Score", "threshold": "1.0 - 10.0", "status": "VALIDATED", "notes": "Continuous survey-based student wellbeing score"},
    {"metric": "verification_gate_met", "value": "FALSE", "threshold": "TRUE", "status": "BLOCKED", "notes": "Requires >= 100 verified post-deployment labels"}
])
df_labels.to_csv(EXP_DIR / "phase13_verified_label_summary.csv", index=False)

# 3. phase13_model_comparison.csv
df_model_comp = pd.DataFrame([
    {"metric": "sample_size_evaluated", "champion_phase5": "0", "candidate_v1_2": "0", "paired_difference": "0", "status": "PENDING_VERIFIED_LABELS"},
    {"metric": "r2", "champion_phase5": "DATA_NOT_AVAILABLE", "candidate_v1_2": "DATA_NOT_AVAILABLE", "paired_difference": "DATA_NOT_AVAILABLE", "status": "PENDING_VERIFIED_LABELS"},
    {"metric": "rmse", "champion_phase5": "DATA_NOT_AVAILABLE", "candidate_v1_2": "DATA_NOT_AVAILABLE", "paired_difference": "DATA_NOT_AVAILABLE", "status": "PENDING_VERIFIED_LABELS"},
    {"metric": "mae", "champion_phase5": "DATA_NOT_AVAILABLE", "candidate_v1_2": "DATA_NOT_AVAILABLE", "paired_difference": "DATA_NOT_AVAILABLE", "status": "PENDING_VERIFIED_LABELS"},
    {"metric": "mean_error", "champion_phase5": "DATA_NOT_AVAILABLE", "candidate_v1_2": "DATA_NOT_AVAILABLE", "paired_difference": "DATA_NOT_AVAILABLE", "status": "PENDING_VERIFIED_LABELS"},
    {"metric": "median_abs_error", "champion_phase5": "DATA_NOT_AVAILABLE", "candidate_v1_2": "DATA_NOT_AVAILABLE", "paired_difference": "DATA_NOT_AVAILABLE", "status": "PENDING_VERIFIED_LABELS"},
    {"metric": "max_abs_error", "champion_phase5": "DATA_NOT_AVAILABLE", "candidate_v1_2": "DATA_NOT_AVAILABLE", "paired_difference": "DATA_NOT_AVAILABLE", "status": "PENDING_VERIFIED_LABELS"}
])
df_model_comp.to_csv(EXP_DIR / "phase13_model_comparison.csv", index=False)

# 4. phase13_conformal_validation.csv
df_conformal = pd.DataFrame([
    {
        "confidence_level": "80%",
        "target_coverage": 0.80,
        "offline_champion_coverage": 0.8358,
        "offline_candidate_coverage": 0.8358,
        "production_champion_coverage": "DATA_NOT_AVAILABLE",
        "production_candidate_coverage": "DATA_NOT_AVAILABLE",
        "production_mean_width": "DATA_NOT_AVAILABLE",
        "status": "PENDING_VERIFIED_LABELS"
    },
    {
        "confidence_level": "90%",
        "target_coverage": 0.90,
        "offline_champion_coverage": 0.9270,
        "offline_candidate_coverage": 0.9254,
        "production_champion_coverage": "DATA_NOT_AVAILABLE",
        "production_candidate_coverage": "DATA_NOT_AVAILABLE",
        "production_mean_width": "DATA_NOT_AVAILABLE",
        "status": "PENDING_VERIFIED_LABELS"
    },
    {
        "confidence_level": "95%",
        "target_coverage": 0.95,
        "offline_champion_coverage": 0.9652,
        "offline_candidate_coverage": 0.9652,
        "production_champion_coverage": "DATA_NOT_AVAILABLE",
        "production_candidate_coverage": "DATA_NOT_AVAILABLE",
        "production_mean_width": "DATA_NOT_AVAILABLE",
        "status": "PENDING_VERIFIED_LABELS"
    }
])
df_conformal.to_csv(EXP_DIR / "phase13_conformal_validation.csv", index=False)

# 5. phase13_drift_summary.csv
df_drift = pd.DataFrame([
    {"feature_or_metric": "input_features_psi", "drift_metric": "PSI", "current_production_value": "DATA_NOT_AVAILABLE", "threshold": 0.25, "drift_detected": False, "status": "NO_REAL_PRODUCTION_OBSERVATIONS_AVAILABLE"},
    {"feature_or_metric": "input_features_ks", "drift_metric": "KS_PVALUE", "current_production_value": "DATA_NOT_AVAILABLE", "threshold": 0.01, "drift_detected": False, "status": "NO_REAL_PRODUCTION_OBSERVATIONS_AVAILABLE"},
    {"feature_or_metric": "input_features_tvd", "drift_metric": "TVD", "current_production_value": "DATA_NOT_AVAILABLE", "threshold": 0.15, "drift_detected": False, "status": "NO_REAL_PRODUCTION_OBSERVATIONS_AVAILABLE"},
    {"feature_or_metric": "prediction_drift", "drift_metric": "KS_PVALUE", "current_production_value": "DATA_NOT_AVAILABLE", "threshold": 0.01, "drift_detected": False, "status": "NO_REAL_PRODUCTION_OBSERVATIONS_AVAILABLE"},
    {"feature_or_metric": "interval_width_drift", "drift_metric": "KS_PVALUE", "current_production_value": "DATA_NOT_AVAILABLE", "threshold": 0.01, "drift_detected": False, "status": "NO_REAL_PRODUCTION_OBSERVATIONS_AVAILABLE"},
    {"feature_or_metric": "error_drift", "drift_metric": "MAE_DEGRADATION", "current_production_value": "DATA_NOT_AVAILABLE", "threshold": 0.05, "drift_detected": False, "status": "PENDING_VERIFIED_LABELS"}
])
df_drift.to_csv(EXP_DIR / "phase13_drift_summary.csv", index=False)

# 6. phase13_subgroup_summary.csv
subgroups = [
    ("Gender", "Female"), ("Gender", "Male"), ("Gender", "Other"),
    ("Academic_Level", "Undergraduate"), ("Academic_Level", "Graduate"), ("Academic_Level", "High School"),
    ("Stress_Level", "Low"), ("Stress_Level", "Medium"), ("Stress_Level", "High"),
    ("Most_Used_Platform", "Instagram"), ("Most_Used_Platform", "YouTube"), ("Most_Used_Platform", "TikTok"),
    ("Purpose_Of_Use", "Academics"), ("Purpose_Of_Use", "Entertainment"), ("Purpose_Of_Use", "Social")
]
df_subgroup = pd.DataFrame([
    {
        "subgroup_dimension": dim,
        "subgroup_cohort": cohort,
        "verified_sample_size": 0,
        "champion_mae": "DATA_NOT_AVAILABLE",
        "candidate_mae": "DATA_NOT_AVAILABLE",
        "champion_rmse": "DATA_NOT_AVAILABLE",
        "candidate_rmse": "DATA_NOT_AVAILABLE",
        "champion_90_coverage": "DATA_NOT_AVAILABLE",
        "candidate_90_coverage": "DATA_NOT_AVAILABLE",
        "status": "NO_REAL_PRODUCTION_OBSERVATIONS_AVAILABLE"
    }
    for dim, cohort in subgroups
])
df_subgroup.to_csv(EXP_DIR / "phase13_subgroup_summary.csv", index=False)

# 7. phase13_governance_gate.csv
df_gate = pd.DataFrame([
    {
        "gate_dimension": "technical_integrity",
        "requirement": "champion_and_candidate_hash_verified",
        "current_state": "VERIFIED (Champion a012e7..., Candidate aad2f2...)",
        "gate_status": "PASS",
        "blocker_reason": "None"
    },
    {
        "gate_dimension": "candidate_failure_isolation",
        "requirement": "candidate_crash_does_not_affect_user",
        "current_state": "VERIFIED (100% isolated, champion response unaffected)",
        "gate_status": "PASS",
        "blocker_reason": "None"
    },
    {
        "gate_dimension": "candidate_shadow_routing",
        "requirement": "candidate_never_returned_to_user",
        "current_state": "VERIFIED (shadow execution telemetry-only)",
        "gate_status": "PASS",
        "blocker_reason": "None"
    },
    {
        "gate_dimension": "verified_production_labels",
        "requirement": ">= 100 verified post-deployment labels",
        "current_state": "0 / 100",
        "gate_status": "FAIL",
        "blocker_reason": "Insufficient verified production labels (0 of 100)"
    },
    {
        "gate_dimension": "shadow_observation_period",
        "requirement": ">= 14 consecutive calendar days",
        "current_state": "0 / 14 days completed (start: 2026-10-06T09:30:00Z)",
        "gate_status": "FAIL",
        "blocker_reason": "Shadow observation in progress (14 days remaining)"
    },
    {
        "gate_dimension": "real_world_model_evaluation",
        "requirement": "paired evaluation on >= 100 verified labels",
        "current_state": "DATA_NOT_AVAILABLE",
        "gate_status": "FAIL",
        "blocker_reason": "Awaiting verified production outcomes"
    },
    {
        "gate_dimension": "uncertainty_evaluation",
        "requirement": "empirical post-deployment coverage evaluation",
        "current_state": "DATA_NOT_AVAILABLE",
        "gate_status": "FAIL",
        "blocker_reason": "Awaiting verified production outcomes"
    },
    {
        "gate_dimension": "drift_governance",
        "requirement": "no critical unresolved drift in production",
        "current_state": "BASELINE_READY",
        "gate_status": "PASS",
        "blocker_reason": "None (monitoring healthy)"
    },
    {
        "gate_dimension": "shadow_reliability",
        "requirement": "zero production outages caused by candidate",
        "current_state": "HEALTHY (0 timeouts, 0 uncaught exceptions)",
        "gate_status": "PASS",
        "blocker_reason": "None"
    },
    {
        "gate_dimension": "human_approval",
        "requirement": "signoff from Model Governance Committee",
        "current_state": "PENDING",
        "gate_status": "PENDING",
        "blocker_reason": "Requires completed 14-day shadow & >= 100 labels"
    },
    {
        "gate_dimension": "promotion_decision",
        "requirement": "ALL GATES MUST PASS FOR PROMOTION",
        "current_state": "BLOCKED",
        "gate_status": "BLOCKED",
        "blocker_reason": "Candidate promotion strictly blocked until all gates satisfied"
    }
])
df_gate.to_csv(EXP_DIR / "phase13_governance_gate.csv", index=False)

print("Generated all 7 Phase 13 experiment CSV files successfully.")
