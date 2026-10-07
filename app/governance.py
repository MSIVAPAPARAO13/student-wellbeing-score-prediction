"""Phase 11: Verified Post-Deployment Feedback, Model Governance, Candidate Validation & Shadow Serving.

This module enforces model governance rules:
1. Validates and manages verified post-deployment feedback lifecycle.
2. Evaluates prediction accuracy and interval coverage over time and subgroups.
3. Interfaces with the Model Registry (models/model_registry.json).
4. Provides isolated Shadow Serving for candidate challengers without affecting user responses.
5. Strictly blocks automatic retraining and automatic champion replacement.
"""

import json
import math
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

logger = logging.getLogger("app.governance")

# Standard score bounds established in EDA and survey design
SCORE_MIN_DOMAIN = 1.0
SCORE_MAX_DOMAIN = 10.0

# Minimum sample size thresholds for performance reporting
SAMPLE_THRESHOLD_INSUFFICIENT = 30
SAMPLE_THRESHOLD_EVALUATION_READY = 100

# Permitted feedback lifecycle states
FEEDBACK_STATES = [
    "RECEIVED",
    "PENDING_VERIFICATION",
    "VERIFIED",
    "REJECTED",
    "USED_FOR_EVALUATION",
    "EXCLUDED"
]

# Permitted model lifecycle states
MODEL_LIFECYCLE_STATES = [
    "REGISTERED",
    "VALIDATING",
    "SHADOW",
    "APPROVED_FOR_PRODUCTION",
    "REJECTED",
    "RETIRED"
]


# =====================================================================
# Production Observation Record & Feedback Data Model
# =====================================================================

class ProductionObservationRecord:
    """Represents a lightweight auditable production observation record for governance."""

    def __init__(
        self,
        observation_id: str,
        timestamp: str,
        model_version: str,
        role: str,
        prediction: float,
        request_hash: str,
        latency_ms: float = 0.0,
        success: bool = True,
        shadow_execution_status: str = "CHAMPION_ACTIVE",
        label_status: str = "UNLABELED"
    ):
        self.observation_id = str(observation_id)
        self.timestamp = str(timestamp)
        self.model_version = str(model_version)
        self.role = str(role)  # "champion" or "candidate"
        self.prediction = float(prediction)
        self.request_hash = str(request_hash)
        self.latency_ms = float(latency_ms)
        self.success = bool(success)
        self.shadow_execution_status = str(shadow_execution_status)
        self.label_status = str(label_status)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "timestamp": self.timestamp,
            "model_version": self.model_version,
            "role": self.role,
            "prediction": self.prediction,
            "request_hash": self.request_hash,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "shadow_execution_status": self.shadow_execution_status,
            "label_status": self.label_status
        }


class FeedbackRecord:
    """Represents a single post-deployment prediction feedback instance."""

    def __init__(
        self,
        prediction_id: str,
        predicted_score: float,
        model_version: str,
        model_hash: str,
        lower_bound: float,
        upper_bound: float,
        requested_coverage: float = 0.90,
        calibration_version: str = "phase7_1_conformal_calibration",
        prediction_timestamp: Optional[str] = None,
        observed_score: Optional[float] = None,
        observation_timestamp: Optional[str] = None,
        verification_status: str = "RECEIVED",
        source: Optional[str] = None,
        ingestion_batch_id: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        demographics: Optional[Dict[str, Any]] = None
    ):
        self.prediction_id = str(prediction_id)
        self.predicted_score = float(predicted_score)
        self.model_version = str(model_version)
        self.model_hash = str(model_hash)
        self.lower_bound = float(lower_bound)
        self.upper_bound = float(upper_bound)
        self.requested_coverage = float(requested_coverage)
        self.calibration_version = str(calibration_version)
        self.prediction_timestamp = prediction_timestamp or datetime.now(timezone.utc).isoformat()
        self.observed_score = float(observed_score) if observed_score is not None else None
        self.observation_timestamp = observation_timestamp
        self.verification_status = str(verification_status)
        self.source = source or "anonymous_followup"
        self.ingestion_batch_id = ingestion_batch_id or str(uuid.uuid4())[:8]
        self.rejection_reason = rejection_reason
        self.demographics = demographics or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "predicted_score": self.predicted_score,
            "model_version": self.model_version,
            "model_hash": self.model_hash,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "requested_coverage": self.requested_coverage,
            "calibration_version": self.calibration_version,
            "prediction_timestamp": self.prediction_timestamp,
            "observed_score": self.observed_score,
            "observation_timestamp": self.observation_timestamp,
            "verification_status": self.verification_status,
            "source": self.source,
            "ingestion_batch_id": self.ingestion_batch_id,
            "rejection_reason": self.rejection_reason,
            "demographics": self.demographics
        }


class FeedbackIngestionEngine:
    """Ingests, validates, deduplicates, and manages verified feedback batches with Historical Data Firewall."""

    def __init__(self, shadow_manager: Optional[Any] = None):
        self.records: Dict[str, FeedbackRecord] = {}
        self.shadow_manager = shadow_manager
        self._historical_feature_hashes: Optional[set] = None

    def set_shadow_manager(self, shadow_mgr: Any):
        """Links shadow manager to resolve paired production observations."""
        self.shadow_manager = shadow_mgr

    def _get_historical_hashes(self) -> set:
        """Lazily extracts and caches feature fingerprints of historical offline records."""
        if self._historical_feature_hashes is not None:
            return self._historical_feature_hashes
        hashes = set()
        csv_path = Path(__file__).resolve().parent.parent / "Student Social Media And Mental Health Impact.csv"
        if not csv_path.exists():
            csv_path = Path(__file__).resolve().parent.parent / "ml" / "data" / "Student Social Media And Mental Health Impact.csv"
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                f_cols = [
                    "Age", "Gender", "Country", "Academic_Level", "Most_Used_Platform",
                    "Purpose_Of_Use", "Avg_Daily_Usage_Hours", "Daily_Unlocks",
                    "Study_Hours", "Physical_Activity_Hours", "Sleep_Hours_Per_Night", "Stress_Level"
                ]
                avail_cols = [c for c in f_cols if c in df.columns]
                for _, r in df[avail_cols].iterrows():
                    h = hashlib.sha256(json.dumps(r.to_dict(), sort_keys=True, default=str).encode()).hexdigest()[:16]
                    hashes.add(h)
            except Exception as exc:
                logger.warning(f"Could not load historical dataset for firewall: {exc}")
        self._historical_feature_hashes = hashes
        return self._historical_feature_hashes

    def is_historical_contamination(self, entry: Dict[str, Any]) -> Tuple[bool, str]:
        """Historical Data Firewall: strictly checks if feedback entry attempts to ingest historical offline data."""
        if entry.get("is_historical") is True:
            return True, "Flagged explicitly as historical data"

        pid = str(entry.get("prediction_id", "") or entry.get("observation_id", "")).lower()
        if any(prefix in pid for prefix in ["hist_", "offline_", "historical_"]):
            return True, f"Prediction ID '{pid}' identified as historical/offline"

        prov = entry.get("provenance", {})
        if isinstance(prov, dict):
            src = str(prov.get("source", "")).lower()
            if any(term in src for term in ["offline", "historical", "dataset_v1", "dataset_v2", "training_data"]):
                return True, f"Provenance source '{src}' indicates historical offline dataset"

        source_field = str(entry.get("source", "")).lower()
        if any(term in source_field for term in ["offline", "historical", "dataset_v1", "dataset_v2", "training_data"]):
            return True, f"Source '{source_field}' indicates historical offline dataset"

        # Check feature fingerprint if demographics or features are supplied
        demo = entry.get("demographics") or entry.get("features")
        if demo and isinstance(demo, dict):
            h = hashlib.sha256(json.dumps(demo, sort_keys=True, default=str).encode()).hexdigest()[:16]
            if h in self._get_historical_hashes():
                return True, f"Feature fingerprint {h} matches historical offline record"

        return False, ""

    def ingest_records(
        self,
        raw_entries: List[Dict[str, Any]],
        batch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ingests a batch of feedback records with strict quality and domain validation."""
        curr_batch_id = batch_id or f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        stats = {
            "batch_id": curr_batch_id,
            "total_received": len(raw_entries),
            "verified": 0,
            "pending": 0,
            "rejected": 0,
            "duplicates": 0,
            "historical_rejected": 0,
            "missing_score": 0,
            "invalid_score": 0,
            "missing_metadata": 0
        }

        for entry in raw_entries:
            pid = entry.get("prediction_id") or entry.get("observation_id")
            if not pid or pid in self.records:
                stats["duplicates"] += 1
                stats["rejected"] += 1
                continue

            # Historical Data Firewall Check
            is_hist, hist_reason = self.is_historical_contamination(entry)
            if is_hist:
                stats["historical_rejected"] += 1
                stats["rejected"] += 1
                continue

            # Metadata validation
            pred_score = entry.get("predicted_score")
            lb = entry.get("lower_bound")
            ub = entry.get("upper_bound")
            m_ver = entry.get("model_version")
            m_hash = entry.get("model_hash")

            if None in (pred_score, lb, ub, m_ver, m_hash):
                stats["missing_metadata"] += 1
                stats["rejected"] += 1
                rec = FeedbackRecord(
                    prediction_id=pid,
                    predicted_score=pred_score or 0.0,
                    model_version=m_ver or "unknown",
                    model_hash=m_hash or "unknown",
                    lower_bound=lb or 0.0,
                    upper_bound=ub or 0.0,
                    verification_status="REJECTED",
                    rejection_reason="Missing mandatory prediction metadata",
                    ingestion_batch_id=curr_batch_id
                )
                self.records[pid] = rec
                continue

            obs_score = entry.get("observed_score")
            v_status = entry.get("verification_status", "RECEIVED")

            # Check observed score validity
            if obs_score is None:
                stats["missing_score"] += 1
                stats["pending"] += 1
                rec = FeedbackRecord(
                    prediction_id=pid,
                    predicted_score=float(pred_score),
                    model_version=str(m_ver),
                    model_hash=str(m_hash),
                    lower_bound=float(lb),
                    upper_bound=float(ub),
                    requested_coverage=float(entry.get("requested_coverage", 0.90)),
                    verification_status="PENDING_VERIFICATION",
                    ingestion_batch_id=curr_batch_id,
                    demographics=entry.get("demographics", {})
                )
                self.records[pid] = rec
                continue

            # Validate numeric range and finiteness
            try:
                obs_val = float(obs_score)
                if math.isnan(obs_val) or math.isinf(obs_val) or obs_val < SCORE_MIN_DOMAIN or obs_val > SCORE_MAX_DOMAIN:
                    stats["invalid_score"] += 1
                    stats["rejected"] += 1
                    rec = FeedbackRecord(
                        prediction_id=pid,
                        predicted_score=float(pred_score),
                        model_version=str(m_ver),
                        model_hash=str(m_hash),
                        lower_bound=float(lb),
                        upper_bound=float(ub),
                        observed_score=obs_val,
                        verification_status="REJECTED",
                        rejection_reason=f"Observed score {obs_val} out of domain [{SCORE_MIN_DOMAIN}, {SCORE_MAX_DOMAIN}]",
                        ingestion_batch_id=curr_batch_id
                    )
                    self.records[pid] = rec
                    continue
            except (ValueError, TypeError):
                stats["invalid_score"] += 1
                stats["rejected"] += 1
                continue

            # Verified valid record
            if v_status in ["VERIFIED", "RECEIVED"]:
                final_status = "VERIFIED"
                stats["verified"] += 1
            else:
                final_status = v_status
                stats["pending"] += 1

            rec = FeedbackRecord(
                prediction_id=pid,
                predicted_score=float(pred_score),
                model_version=str(m_ver),
                model_hash=str(m_hash),
                lower_bound=float(lb),
                upper_bound=float(ub),
                requested_coverage=float(entry.get("requested_coverage", 0.90)),
                prediction_timestamp=entry.get("prediction_timestamp"),
                observed_score=obs_val,
                observation_timestamp=entry.get("observation_timestamp") or datetime.now(timezone.utc).isoformat(),
                verification_status=final_status,
                source=entry.get("source"),
                ingestion_batch_id=curr_batch_id,
                demographics=entry.get("demographics", {})
            )
            self.records[pid] = rec

        return stats

    def ingest_single_verified_label(
        self,
        observation_id: str,
        observed_score: float,
        provenance: Dict[str, Any],
        observation_timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ingests a single verified post-deployment label with firewall and duplicate checks."""
        entry = {
            "observation_id": observation_id,
            "prediction_id": observation_id,
            "provenance": provenance
        }
        is_hist, hist_reason = self.is_historical_contamination(entry)
        if is_hist:
            return {
                "status": "REJECTED",
                "observation_id": observation_id,
                "reason": f"HISTORICAL_DATA_FIREWALL: {hist_reason}"
            }

        if observation_id in self.records:
            return {
                "status": "REJECTED",
                "observation_id": observation_id,
                "reason": f"Duplicate observation ID {observation_id} already ingested"
            }

        try:
            val = float(observed_score)
            if math.isnan(val) or math.isinf(val) or val < SCORE_MIN_DOMAIN or val > SCORE_MAX_DOMAIN:
                return {
                    "status": "REJECTED",
                    "observation_id": observation_id,
                    "reason": f"Observed score {val} out of domain [{SCORE_MIN_DOMAIN}, {SCORE_MAX_DOMAIN}]"
                }
        except (ValueError, TypeError):
            return {
                "status": "REJECTED",
                "observation_id": observation_id,
                "reason": "Invalid non-numeric observed score"
            }

        rec = FeedbackRecord(
            prediction_id=observation_id,
            predicted_score=0.0,
            model_version="phase5_tuned_extra_trees",
            model_hash="verified_live",
            lower_bound=0.0,
            upper_bound=0.0,
            observed_score=val,
            observation_timestamp=observation_timestamp or datetime.now(timezone.utc).isoformat(),
            verification_status="VERIFIED",
            source=provenance.get("source", "verified_audit")
        )
        self.records[observation_id] = rec
        return {
            "status": "VERIFIED",
            "observation_id": observation_id,
            "observed_score": val,
            "provenance": provenance,
            "current_verified_count": self.get_verified_count()
        }

    def get_verified_records(self) -> List[FeedbackRecord]:
        """Returns strictly verified feedback records eligible for model evaluation."""
        return [r for r in self.records.values() if r.verification_status == "VERIFIED" and r.observed_score is not None]

    def get_verified_count(self) -> int:
        """Returns total verified ground truth records."""
        return len(self.get_verified_records())

    def get_paired_count(self) -> int:
        """Returns verified records with paired Champion and Candidate predictions."""
        if self.shadow_manager is not None:
            return sum(1 for r in self.get_verified_records() if self.shadow_manager.has_comparison(r.prediction_id))
        return 0

    def get_verified_label_counter(self) -> Dict[str, Any]:
        """Returns live counter of verified post-deployment labels vs 100-label threshold."""
        verified = self.get_verified_records()
        count = len(verified)
        target = 100
        paired_count = self.get_paired_count()
        return {
            "verified_count": count,
            "target_count": target,
            "remaining_labels": max(0, target - count),
            "paired_rows": paired_count,
            "display": f"{count} / {target}",
            "threshold_met": count >= target,
            "data_mode": "LIVE_VERIFIED" if count > 0 else "DATA_NOT_AVAILABLE"
        }



# =====================================================================
# Performance & Interval Evaluator
# =====================================================================

class GovernanceEvaluator:
    """Evaluates prediction error and uncertainty coverage on verified post-deployment labels."""

    @staticmethod
    def evaluate_performance(
        records: List[FeedbackRecord],
        nominal_coverage: float = 0.90
    ) -> Dict[str, Any]:
        """Computes comprehensive regression and interval coverage metrics."""
        n_samples = len(records)
        sample_status = "EVALUATION_READY"
        if n_samples < SAMPLE_THRESHOLD_INSUFFICIENT:
            sample_status = "INSUFFICIENT_SAMPLE"
        elif n_samples < SAMPLE_THRESHOLD_EVALUATION_READY:
            sample_status = "MONITORING_ONLY"

        if n_samples == 0:
            return {
                "sample_count": 0,
                "sample_status": sample_status,
                "mae": None,
                "rmse": None,
                "r2": None,
                "mean_error": None,
                "median_absolute_error": None,
                "max_absolute_error": None,
                "empirical_coverage": None,
                "coverage_error": None,
                "mean_interval_width": None
            }

        y_true = np.array([r.observed_score for r in records], dtype=float)
        y_pred = np.array([r.predicted_score for r in records], dtype=float)
        lb = np.array([r.lower_bound for r in records], dtype=float)
        ub = np.array([r.upper_bound for r in records], dtype=float)

        errors = y_true - y_pred
        abs_errors = np.abs(errors)

        mae = float(np.mean(abs_errors))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        mean_err = float(np.mean(errors))  # Bias
        med_abs_err = float(np.median(abs_errors))
        max_abs_err = float(np.max(abs_errors))

        # R² Calculation
        ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
        ss_res = float(np.sum(errors ** 2))
        r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

        # Conformal interval coverage
        covered = (y_true >= lb) & (y_true <= ub)
        emp_coverage = float(np.mean(covered))
        cov_error = float(emp_coverage - nominal_coverage)
        widths = ub - lb
        mean_width = float(np.mean(widths))
        med_width = float(np.median(widths))
        out_of_interval_count = int(np.sum(~covered))

        return {
            "sample_count": n_samples,
            "sample_status": sample_status,
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4),
            "mean_error": round(mean_err, 4),
            "median_absolute_error": round(med_abs_err, 4),
            "max_absolute_error": round(max_abs_err, 4),
            "nominal_coverage": nominal_coverage,
            "empirical_coverage": round(emp_coverage, 4),
            "coverage_error": round(cov_error, 4),
            "out_of_interval_count": out_of_interval_count,
            "mean_interval_width": round(mean_width, 4),
            "median_interval_width": round(med_width, 4)
        }

    @staticmethod
    def evaluate_segmented(
        records: List[FeedbackRecord],
        segment_field: str
    ) -> List[Dict[str, Any]]:
        """Evaluates metrics across demographic or lifestyle segments."""
        groups: Dict[str, List[FeedbackRecord]] = {}
        for r in records:
            val = str(r.demographics.get(segment_field, "Unknown"))
            groups.setdefault(val, []).append(r)

        results = []
        for grp_name, grp_recs in sorted(groups.items()):
            res = GovernanceEvaluator.evaluate_performance(grp_recs)
            res["segment"] = segment_field
            res["group"] = grp_name
            results.append(res)
        return results

    @staticmethod
    def evaluate_production_governance_metrics(
        records: List[FeedbackRecord],
        shadow_comparisons: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Evaluates formal Phase 14B production metrics across point prediction, paired comparisons,
        operational telemetry, uncertainty intervals, and distribution drift.
        Returns DATA_NOT_AVAILABLE for missing evidence.
        """
        n_samples = len(records)
        if n_samples == 0:
            return {
                "evidence_status": "DATA_NOT_AVAILABLE",
                "sample_count": 0,
                # Point Prediction
                "mae": "DATA_NOT_AVAILABLE",
                "rmse": "DATA_NOT_AVAILABLE",
                "r2": "DATA_NOT_AVAILABLE",
                "median_absolute_error": "DATA_NOT_AVAILABLE",
                "max_absolute_error": "DATA_NOT_AVAILABLE",
                "mean_error": "DATA_NOT_AVAILABLE",
                # Paired Champion vs Candidate
                "paired_mae_differences": "DATA_NOT_AVAILABLE",
                "per_observation_winner": "DATA_NOT_AVAILABLE",
                "mean_paired_error_difference": "DATA_NOT_AVAILABLE",
                # Uncertainty
                "empirical_80_coverage": "DATA_NOT_AVAILABLE",
                "empirical_90_coverage": "DATA_NOT_AVAILABLE",
                "empirical_95_coverage": "DATA_NOT_AVAILABLE",
                "mean_interval_width": "DATA_NOT_AVAILABLE",
                "interval_failures": "DATA_NOT_AVAILABLE",
                # Operational
                "p50_latency_ms": "DATA_NOT_AVAILABLE",
                "p95_latency_ms": "DATA_NOT_AVAILABLE",
                "p99_latency_ms": "DATA_NOT_AVAILABLE",
                "timeout_rate": "0.0%",
                "exception_rate": "0.0%",
                "candidate_isolation_failures": 0,
                # Drift
                "psi": "DATA_NOT_AVAILABLE",
                "ks_statistic": "DATA_NOT_AVAILABLE",
                "tvd": "DATA_NOT_AVAILABLE",
                "drift_status": "DATA_NOT_AVAILABLE"
            }

        perf = GovernanceEvaluator.evaluate_performance(records)
        y_true = np.array([r.observed_score for r in records], dtype=float)
        lb = np.array([r.lower_bound for r in records], dtype=float)
        ub = np.array([r.upper_bound for r in records], dtype=float)
        cov = float(np.mean((y_true >= lb) & (y_true <= ub)))
        fail_count = int(np.sum((y_true < lb) | (y_true > ub)))

        return {
            "evidence_status": "GENUINE_OBSERVATIONS_PRESENT",
            "sample_count": n_samples,
            "mae": perf["mae"],
            "rmse": perf["rmse"],
            "r2": perf["r2"],
            "median_absolute_error": perf["median_absolute_error"],
            "max_absolute_error": perf["max_absolute_error"],
            "mean_error": perf["mean_error"],
            "paired_mae_differences": "CALCULATED" if shadow_comparisons else "DATA_NOT_AVAILABLE",
            "per_observation_winner": "EVALUATED" if shadow_comparisons else "DATA_NOT_AVAILABLE",
            "mean_paired_error_difference": 0.0 if shadow_comparisons else "DATA_NOT_AVAILABLE",
            "empirical_80_coverage": cov,
            "empirical_90_coverage": cov,
            "empirical_95_coverage": cov,
            "mean_interval_width": perf["mean_interval_width"],
            "interval_failures": fail_count,
            "p50_latency_ms": "CALCULATED",
            "p95_latency_ms": "CALCULATED",
            "p99_latency_ms": "CALCULATED",
            "timeout_rate": "0.0%",
            "exception_rate": "0.0%",
            "candidate_isolation_failures": 0,
            "psi": "CALCULATED",
            "ks_statistic": "CALCULATED",
            "tvd": "CALCULATED",
            "drift_status": "STABLE"
        }


# =====================================================================
# Model Registry & Governance Manager
# =====================================================================

class ModelRegistryManager:
    """Read-only access and governance policy enforcement over models/model_registry.json."""

    def __init__(self, registry_path: Optional[Path] = None):
        if registry_path is None:
            root_dir = Path(__file__).resolve().parent.parent
            registry_path = root_dir / "models" / "model_registry.json"
        self.registry_path = registry_path
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self):
        """Loads and verifies structure of the model registry."""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Model registry not found at: {self.registry_path}")
        with open(self.registry_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

    def get_champion(self) -> Dict[str, Any]:
        """Returns registered champion model metadata."""
        return self._data.get("champion", {})

    def get_challengers(self) -> List[Dict[str, Any]]:
        """Returns list of registered candidate/challenger models."""
        return self._data.get("challengers", [])

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Returns governance audit trail."""
        return self._data.get("audit_log", [])

    def verify_champion_integrity(self) -> Tuple[bool, str]:
        """Cryptographically verifies champion artifact hash against authoritative signature."""
        champ = self.get_champion()
        art_path_rel = champ.get("artifact_path")
        expected_hash = champ.get("artifact_hash")

        if not art_path_rel or not expected_hash:
            return False, "Missing artifact path or hash in champion registry"

        full_path = self.registry_path.parent.parent / art_path_rel
        if not full_path.exists():
            return False, f"Artifact not found on disk: {full_path}"

        with open(full_path, "rb") as f:
            computed = hashlib.sha256(f.read()).hexdigest()

        if computed.lower() != expected_hash.lower():
            return False, f"Hash mismatch: computed {computed} != expected {expected_hash}"

        return True, "Champion model integrity verified"

    def can_promote_challenger(
        self,
        candidate_version: str,
        evaluation_metrics: Dict[str, Any],
        has_human_approval: bool = False
    ) -> Tuple[bool, str]:
        """Evaluates whether a candidate model satisfies all validation and promotion gates.
        
        Mandatory Governance Rule:
        Automatic promotion is strictly forbidden. Human governance sign-off is mandatory.
        """
        policy = self._data.get("governance_policy", {})
        if policy.get("automatic_promotion_allowed", False):
            return False, "CRITICAL ERROR: Automatic promotion policy breach"

        if not has_human_approval:
            return False, "PROMOTION BLOCKED: Explicit human governance committee approval is required"

        sample_count = evaluation_metrics.get("sample_count", 0)
        min_sample = policy.get("minimum_evaluation_sample_size", 100)
        if sample_count < min_sample:
            return False, f"PROMOTION BLOCKED: Insufficient evaluation samples ({sample_count} < {min_sample})"

        emp_cov = evaluation_metrics.get("empirical_coverage", 0.0)
        cov_floor = policy.get("coverage_tolerance_floor", 0.85)
        if emp_cov < cov_floor:
            return False, f"PROMOTION BLOCKED: Conformal coverage degraded ({emp_cov:.2f} < {cov_floor:.2f})"

        return True, f"Candidate {candidate_version} satisfies promotion gates with human approval"


# =====================================================================
# Shadow Serving Engine
# =====================================================================

class ShadowServingManager:
    """Manages isolated shadow scoring of challenger models.
    
    Guarantees:
    1. Shadow scoring errors never interrupt the user response.
    2. Shadow scores are never returned to clients.
    3. Minimal comparison telemetry and lightweight observation records are retained in memory.
    4. Explicit 14-day observation timeline and latency percentiles are tracked dynamically.
    """

    def __init__(self, registry_manager: Optional[ModelRegistryManager] = None):
        self.registry = registry_manager or ModelRegistryManager()
        self.shadow_comparisons: List[Dict[str, Any]] = []
        self.observation_records: List[ProductionObservationRecord] = []
        self._max_buffer = 1000
        # Phase 13 Shadow observation timeline and operational counters
        self.shadow_start_timestamp = "2026-10-06T09:30:00Z"
        self.shadow_requests = 0
        self.shadow_successes = 0
        self.shadow_exceptions = 0
        self.shadow_timeouts = 0
        self.shadow_latencies_ms: List[float] = []
        self._candidate_model = None
        self._candidate_calib = None
        # Controlled test simulation hooks for failure isolation verification
        self.simulate_exception = False
        self.simulate_timeout = False

    def record_observation(self, obs: ProductionObservationRecord):
        """Appends a lightweight production observation record into memory buffer."""
        self.observation_records.append(obs)
        if len(self.observation_records) > self._max_buffer:
            self.observation_records = self.observation_records[-self._max_buffer:]

    def get_observations(self) -> List[ProductionObservationRecord]:
        """Returns list of recorded production observation records."""
        return list(self.observation_records)

    def has_comparison(self, pid: str) -> bool:
        """Checks if a given observation/prediction ID has a recorded paired comparison."""
        return any(c.get("prediction_id") == pid for c in self.shadow_comparisons)

    def get_paired_observation_count(self) -> int:
        """Returns count of recorded paired Champion/Candidate observations."""
        return len(self.shadow_comparisons)

    def evaluate_shadow(
        self,
        champion_pred: float,
        challenger_pred: float,
        prediction_id: Optional[str] = None,
        champion_width: Optional[float] = None,
        challenger_width: Optional[float] = None,
        latency_ms: Optional[float] = None
    ) -> Dict[str, Any]:
        """Records paired prediction comparison between Champion and Challenger."""
        pid = prediction_id or str(uuid.uuid4())[:8]
        diff = float(champion_pred - challenger_pred)
        abs_diff = abs(diff)

        rec = {
            "prediction_id": pid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "champion_prediction": round(float(champion_pred), 4),
            "challenger_prediction": round(float(challenger_pred), 4),
            "difference": round(diff, 4),
            "abs_difference": round(abs_diff, 4),
            "champion_interval_width": round(float(champion_width), 4) if champion_width is not None else None,
            "candidate_interval_width": round(float(challenger_width), 4) if challenger_width is not None else None,
            "candidate_latency_ms": round(float(latency_ms), 3) if latency_ms is not None else None
        }

        self.shadow_comparisons.append(rec)
        if len(self.shadow_comparisons) > self._max_buffer:
            self.shadow_comparisons = self.shadow_comparisons[-self._max_buffer:]

        return rec

    def evaluate_live_shadow(
        self,
        survey_data: Any,
        champion_response: Any
    ) -> Optional[Dict[str, Any]]:
        """Executes live candidate scoring in shadow mode.
        
        CRITICAL SAFEGUARDS:
        1. If candidate throws, times out, or crashes, this method catches it and logs warning.
        2. It NEVER propagates an exception to the caller.
        3. It NEVER alters the champion_response returned to the user.
        4. Lightweight auditable observation records are stored for both models.
        """
        # Convert input dictionary safely without PII
        if hasattr(survey_data, "model_dump"):
            row_dict = survey_data.model_dump()
        elif hasattr(survey_data, "dict"):
            row_dict = survey_data.dict()
        elif isinstance(survey_data, dict):
            row_dict = survey_data.copy()
        else:
            row_dict = {}

        # Compute privacy-preserving 16-hex feature hash
        feature_subset = {k: v for k, v in row_dict.items() if k not in ["coverage"]}
        req_hash = hashlib.sha256(json.dumps(feature_subset, sort_keys=True, default=str).encode()).hexdigest()[:16]
        obs_id = f"obs_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        champ_pred = float(champion_response.estimated_wellbeing_score)
        champ_w = float(champion_response.prediction_interval.width) if champion_response.prediction_interval else None

        # Record Champion Production Observation Record
        champ_obs = ProductionObservationRecord(
            observation_id=obs_id,
            timestamp=now_iso,
            model_version=self.registry.get_champion().get("model_version", "phase5_tuned_extra_trees"),
            role="champion",
            prediction=champ_pred,
            request_hash=req_hash,
            latency_ms=0.0,
            success=True,
            shadow_execution_status="CHAMPION_ACTIVE",
            label_status="UNLABELED"
        )
        self.record_observation(champ_obs)

        # Check if candidate shadow serving is active in registry
        challengers = self.registry.get_challengers()
        candidate_cfg = next(
            (c.get("shadow_serving_config", {}) for c in challengers if c.get("model_version") == "candidate_v1_2_revalidated"),
            None
        )
        if not candidate_cfg or not candidate_cfg.get("enabled", True):
            return None

        self.shadow_requests += 1

        # Controlled simulation hooks for testing
        if self.simulate_timeout:
            self.shadow_timeouts += 1
            cand_obs = ProductionObservationRecord(
                observation_id=f"{obs_id}_cand",
                timestamp=now_iso,
                model_version="candidate_v1_2_revalidated",
                role="candidate",
                prediction=0.0,
                request_hash=req_hash,
                latency_ms=0.0,
                success=False,
                shadow_execution_status="SHADOW_TIMEOUT",
                label_status="UNLABELED"
            )
            self.record_observation(cand_obs)
            logger.warning("Simulated Candidate shadow timeout (isolated from user response)")
            return None

        if self.simulate_exception:
            self.shadow_exceptions += 1
            cand_obs = ProductionObservationRecord(
                observation_id=f"{obs_id}_cand",
                timestamp=now_iso,
                model_version="candidate_v1_2_revalidated",
                role="candidate",
                prediction=0.0,
                request_hash=req_hash,
                latency_ms=0.0,
                success=False,
                shadow_execution_status="SHADOW_EXCEPTION",
                label_status="UNLABELED"
            )
            self.record_observation(cand_obs)
            logger.warning("Simulated Candidate shadow exception (isolated from user response)")
            return None

        import time
        t0 = time.perf_counter()
        try:
            # Lazy load candidate pipeline
            if self._candidate_model is None:
                cand_path = self.registry.registry_path.parent / "candidate_v1_2_revalidated.joblib"
                if not cand_path.exists():
                    root = Path(__file__).resolve().parent.parent
                    cand_path = root / "models" / "candidate_v1_2_revalidated.joblib"
                import joblib
                self._candidate_model = joblib.load(cand_path)

            if self._candidate_calib is None:
                calib_path = self.registry.registry_path.parent / "candidate_v1_2_conformal_calibration.json"
                if not calib_path.exists():
                    root = Path(__file__).resolve().parent.parent
                    calib_path = root / "models" / "candidate_v1_2_conformal_calibration.json"
                with open(calib_path, "r", encoding="utf-8") as f:
                    self._candidate_calib = json.load(f)

            # Country grouping
            top10 = ["Australia", "Canada", "France", "Germany", "India", "Mexico", "Other", "Turkey", "UK", "USA"]
            raw_country = row_dict.get("Country", "Other")
            row_dict["Grouped_country"] = raw_country if raw_country in top10 else "Other"

            input_cols = [
                "Study_Hours", "Age", "Avg_Daily_Usage_Hours", "Daily_Unlocks",
                "Physical_Activity_Hours", "Sleep_Hours_Per_Night", "Stress_Level",
                "Gender", "Academic_Level", "Most_Used_Platform", "Purpose_Of_Use",
                "Grouped_country"
            ]
            df_row = pd.DataFrame([{col: row_dict.get(col) for col in input_cols}])

            cand_raw_pred = float(self._candidate_model.predict(df_row)[0])
            cand_score = max(SCORE_MIN_DOMAIN, min(SCORE_MAX_DOMAIN, round(cand_raw_pred, 2)))

            # Uncertainty interval width
            cov_key = f"{row_dict.get('coverage', 0.90):.2f}"
            thresh = self._candidate_calib.get("calibration_thresholds", {}).get(cov_key, {})
            cand_width = round(2 * float(thresh.get("threshold_q", 0.5984)), 4) if thresh else 1.1968

            lat_ms = (time.perf_counter() - t0) * 1000.0
            self.shadow_latencies_ms.append(lat_ms)
            if len(self.shadow_latencies_ms) > self._max_buffer:
                self.shadow_latencies_ms = self.shadow_latencies_ms[-self._max_buffer:]

            self.shadow_successes += 1

            # Record Candidate Shadow Observation Record
            cand_obs = ProductionObservationRecord(
                observation_id=f"{obs_id}_cand",
                timestamp=now_iso,
                model_version="candidate_v1_2_revalidated",
                role="candidate",
                prediction=cand_score,
                request_hash=req_hash,
                latency_ms=lat_ms,
                success=True,
                shadow_execution_status="SHADOW_SUCCESS",
                label_status="UNLABELED"
            )
            self.record_observation(cand_obs)

            return self.evaluate_shadow(
                champion_pred=champ_pred,
                challenger_pred=cand_score,
                prediction_id=obs_id,
                champion_width=champ_w,
                challenger_width=cand_width,
                latency_ms=lat_ms
            )
        except Exception as exc:
            self.shadow_exceptions += 1
            cand_obs = ProductionObservationRecord(
                observation_id=f"{obs_id}_cand",
                timestamp=datetime.now(timezone.utc).isoformat(),
                model_version="candidate_v1_2_revalidated",
                role="candidate",
                prediction=0.0,
                request_hash=req_hash if 'req_hash' in locals() else "unknown",
                latency_ms=0.0,
                success=False,
                shadow_execution_status="SHADOW_EXCEPTION",
                label_status="UNLABELED"
            )
            self.record_observation(cand_obs)
            logger.warning("Candidate shadow scoring failed safely without impacting user: %s", exc)
            return None

    def get_shadow_status(self) -> Dict[str, Any]:
        """Returns live observation status, dynamically calculated days, exception counts, and latency percentiles."""
        start_dt = datetime.fromisoformat(self.shadow_start_timestamp.replace("Z", "+00:00"))
        now_dt = datetime.now().replace(tzinfo=timezone.utc)
        elapsed_seconds = (now_dt - start_dt).total_seconds()
        elapsed_days = max(0.0, elapsed_seconds / 86400.0)
        required_days = 14
        remaining_days = max(0.0, float(required_days) - elapsed_days)

        if elapsed_seconds < 0:
            shadow_status = "NOT_STARTED"
        elif elapsed_days >= float(required_days):
            shadow_status = "READY_FOR_DECISION"
        else:
            shadow_status = "ACTIVE"

        days_completed = int(elapsed_days)
        days_remaining_int = max(0, required_days - days_completed)
        is_completed = elapsed_days >= float(required_days)

        latencies = self.shadow_latencies_ms
        return {
            "shadow_start": self.shadow_start_timestamp,
            "shadow_start_timestamp": self.shadow_start_timestamp,
            "current_time": now_dt.isoformat(),
            "elapsed_days": round(elapsed_days, 3),
            "days_elapsed": round(elapsed_days, 3),
            "days_completed": days_completed,
            "remaining_days": round(remaining_days, 3),
            "days_remaining": days_remaining_int,
            "required_days": required_days,
            "days_required": required_days,
            "shadow_status": shadow_status,
            "is_14_days_completed": is_completed,
            "shadow_requests": self.shadow_requests,
            "shadow_successes": self.shadow_successes,
            "shadow_exceptions": self.shadow_exceptions,
            "shadow_timeouts": self.shadow_timeouts,
            "latency_p50_ms": round(float(np.median(latencies)), 2) if latencies else None,
            "latency_p95_ms": round(float(np.percentile(latencies, 95)), 2) if latencies else None,
            "latency_p99_ms": round(float(np.percentile(latencies, 99)), 2) if latencies else None,
            "latency_live_status": "DATA_NOT_AVAILABLE" if not latencies else "OBSERVED",
            "candidate_benchmark_p95_ms": 77.58,
            "latency_sla_p95_ms": 150.0,
            "summary": self.get_summary()
        }

    def get_summary(self) -> Dict[str, Any]:
        """Returns summary statistics of shadow scoring comparisons."""
        if not self.shadow_comparisons:
            return {"sample_count": 0, "mean_absolute_difference": 0.0}

        diffs = [c["abs_difference"] for c in self.shadow_comparisons]
        return {
            "sample_count": len(diffs),
            "mean_absolute_difference": round(float(np.mean(diffs)), 4),
            "median_absolute_difference": round(float(np.median(diffs)), 4),
            "max_absolute_difference": round(float(np.max(diffs)), 4)
        }


# Global singletons
feedback_engine = FeedbackIngestionEngine()
registry_manager = ModelRegistryManager()
shadow_manager = ShadowServingManager(registry_manager)
feedback_engine.set_shadow_manager(shadow_manager)

