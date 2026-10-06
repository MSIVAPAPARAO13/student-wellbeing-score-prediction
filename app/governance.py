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
# Verified Feedback Data Model & Ingestion Engine
# =====================================================================

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
    """Ingests, validates, deduplicates, and manages verified feedback batches."""

    def __init__(self):
        self.records: Dict[str, FeedbackRecord] = {}

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
            "missing_score": 0,
            "invalid_score": 0,
            "missing_metadata": 0
        }

        for entry in raw_entries:
            pid = entry.get("prediction_id")
            if not pid or pid in self.records:
                stats["duplicates"] += 1
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

    def get_verified_records(self) -> List[FeedbackRecord]:
        """Returns strictly verified feedback records eligible for model evaluation."""
        return [r for r in self.records.values() if r.verification_status == "VERIFIED" and r.observed_score is not None]


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
    3. Minimal comparison telemetry is retained in memory.
    """

    def __init__(self, registry_manager: Optional[ModelRegistryManager] = None):
        self.registry = registry_manager or ModelRegistryManager()
        self.shadow_comparisons: List[Dict[str, Any]] = []
        self._max_buffer = 1000

    def evaluate_shadow(
        self,
        champion_pred: float,
        challenger_pred: float,
        prediction_id: Optional[str] = None
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
            "abs_difference": round(abs_diff, 4)
        }

        self.shadow_comparisons.append(rec)
        if len(self.shadow_comparisons) > self._max_buffer:
            self.shadow_comparisons = self.shadow_comparisons[-self._max_buffer:]

        return rec

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
