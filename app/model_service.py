import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import joblib

from app.configuration import settings
from app.schemas import StudentSurveyRequest, PredictionResponse, PredictionInterval

logger = logging.getLogger("uvicorn.error")

TOP10_COUNTRIES = [
    "Australia", "Canada", "France", "Germany", "India",
    "Mexico", "Other", "Turkey", "UK", "USA"
]

FEATURE_COLUMNS = [
    "Study_Hours", "Age", "Avg_Daily_Usage_Hours", "Daily_Unlocks",
    "Physical_Activity_Hours", "Sleep_Hours_Per_Night", "Stress_Level",
    "Gender", "Academic_Level", "Most_Used_Platform", "Purpose_Of_Use",
    "Grouped_country"
]

class ModelService:
    def __init__(self):
        self.model = None
        self.metadata: Dict[str, Any] = {}
        self.registry_champion: Dict[str, Any] = {}
        self.conformal_data: Dict[str, Any] = {}
        self._model_hash: str = ""
        self._calibration_hash: str = ""
        self._model_hash_verified: bool = False
        self._is_loaded: bool = False
        self._uncertainty_loaded: bool = False

    def verify_and_load(self):
        """Loads model once and verifies SHA-256 hash against authoritative Phase 7.1 hash."""
        model_path = settings.MODEL_PATH
        if not model_path.exists():
            raise FileNotFoundError(f"Model artifact not found at: {model_path}")

        # Compute and verify model SHA-256 hash
        with open(model_path, "rb") as f:
            file_bytes = f.read()
        self._model_hash = hashlib.sha256(file_bytes).hexdigest()

        if self._model_hash.lower() != settings.MODEL_EXPECTED_HASH.lower():
            err_msg = (
                f"Model integrity verification FAILED! "
                f"Computed hash: {self._model_hash}, "
                f"Expected hash: {settings.MODEL_EXPECTED_HASH}"
            )
            logger.critical(err_msg)
            raise RuntimeError(err_msg)

        self._model_hash_verified = True
        logger.info(f"Model integrity verified successfully: SHA-256 {self._model_hash}")

        # Load pipeline
        self.model = joblib.load(model_path)
        self._is_loaded = True

        # Load Champion metadata if present
        if settings.METADATA_PATH.exists():
            with open(settings.METADATA_PATH, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

        # Load authoritative Champion registry metadata if present
        if settings.REGISTRY_PATH.exists():
            try:
                with open(settings.REGISTRY_PATH, "r", encoding="utf-8") as f:
                    reg_data = json.load(f)
                    self.registry_champion = reg_data.get("champion", {})
            except Exception as exc:
                logger.warning(f"Could not load model registry metadata: {exc}")

        # Load conformal calibration artifact
        conformal_path = settings.CONFORMAL_PATH
        if not conformal_path.exists():
            raise FileNotFoundError(f"Conformal calibration artifact not found at: {conformal_path}")

        with open(conformal_path, "rb") as f:
            conformal_bytes = f.read()
        self._calibration_hash = hashlib.sha256(conformal_bytes).hexdigest()
        self.conformal_data = json.loads(conformal_bytes.decode("utf-8"))

        # Verify source hash in calibration metadata matches loaded model hash
        calib_source_hash = self.conformal_data.get("source_model_hash", "")
        if calib_source_hash and calib_source_hash.lower() != self._model_hash.lower():
            err_msg = (
                f"Conformal calibration metadata hash mismatch! "
                f"Calibration refers to {calib_source_hash}, but loaded model is {self._model_hash}"
            )
            logger.critical(err_msg)
            raise RuntimeError(err_msg)

        self._uncertainty_loaded = True
        logger.info("Phase 7.1 Conformal calibration artifact loaded and verified successfully.")

    @property
    def is_loaded(self) -> bool:
        """Returns True if the point prediction pipeline is verified and loaded."""
        return self._is_loaded and self.model is not None

    @property
    def model_loaded(self) -> bool:
        """Alias for is_loaded."""
        return self.is_loaded

    @property
    def uncertainty_loaded(self) -> bool:
        """Returns True if the conformal calibration engine is verified and loaded."""
        return self._uncertainty_loaded and bool(self.conformal_data)

    @property
    def model_hash(self) -> str:
        """Cryptographic SHA-256 hash of the loaded model artifact."""
        return self._model_hash

    @property
    def model_hash_verified(self) -> bool:
        """True if the loaded model hash exactly matches the expected champion hash."""
        return self._model_hash_verified

    @property
    def calibration_hash(self) -> str:
        """Cryptographic SHA-256 hash of the conformal calibration artifact."""
        return self._calibration_hash

    @property
    def model_version(self) -> str:
        """Authoritative model version derived from the model registry champion record."""
        if self.registry_champion.get("model_version"):
            return str(self.registry_champion["model_version"])
        if self.metadata.get("model_version"):
            return str(self.metadata["model_version"])
        return "phase5_tuned_extra_trees"

    @property
    def model_family(self) -> str:
        """Authoritative model family derived from conformal metadata or registry."""
        if self.conformal_data.get("model_family"):
            return str(self.conformal_data["model_family"])
        if self.registry_champion.get("model_family"):
            return str(self.registry_champion["model_family"])
        if self.metadata.get("model_name"):
            return str(self.metadata["model_name"])
        return "ExtraTreesRegressor"

    @property
    def uncertainty_method(self) -> str:
        """Authoritative uncertainty quantification method string from the calibration artifact."""
        return self.conformal_data.get(
            "method",
            "5-Fold Cross-Conformal / Out-Of-Fold Residual Calibration"
        )

    @property
    def calibration_artifact(self) -> str:
        """File name of the active conformal calibration artifact."""
        return settings.CONFORMAL_PATH.name

    def format_input_dataframe(self, req: StudentSurveyRequest) -> pd.DataFrame:
        """Constructs pandas DataFrame conforming to the exact pipeline schema.
        
        Country Grouping Policy:
        The pipeline preprocessor expects 'Grouped_country' as one of the TOP10_COUNTRIES:
        ['Australia', 'Canada', 'France', 'Germany', 'India', 'Mexico', 'Other', 'Turkey', 'UK', 'USA'].
        If an input matches one of these top 10 categories exactly (e.g. 'USA'), it is retained.
        Any other country string (e.g. 'United States', 'Brazil', etc.) is grouped into 'Other'.
        """
        country_clean = req.Country.strip()
        grouped_country = country_clean if country_clean in TOP10_COUNTRIES else "Other"

        data_row = {
            "Study_Hours": float(req.Study_Hours),
            "Age": int(req.Age),
            "Avg_Daily_Usage_Hours": float(req.Avg_Daily_Usage_Hours),
            "Daily_Unlocks": int(req.Daily_Unlocks),
            "Physical_Activity_Hours": float(req.Physical_Activity_Hours),
            "Sleep_Hours_Per_Night": float(req.Sleep_Hours_Per_Night),
            "Stress_Level": str(req.Stress_Level),
            "Gender": str(req.Gender),
            "Academic_Level": str(req.Academic_Level),
            "Most_Used_Platform": str(req.Most_Used_Platform),
            "Purpose_Of_Use": str(req.Purpose_Of_Use),
            "Grouped_country": grouped_country
        }
        return pd.DataFrame([data_row], columns=FEATURE_COLUMNS)

    def predict(self, req: StudentSurveyRequest) -> PredictionResponse:
        """Executes point prediction and calibrated conformal interval construction."""
        if not self.is_loaded or self.model is None:
            raise RuntimeError("ModelService is not loaded. Cannot execute predict.")

        df_input = self.format_input_dataframe(req)

        # Execute point prediction from frozen pipeline
        raw_pred = float(self.model.predict(df_input)[0])
        score_point = round(raw_pred, 4)

        # Select conformal calibration threshold
        coverage_val = req.coverage if req.coverage is not None else 0.90
        coverage_key = f"{coverage_val:.2f}"
        threshold_info = self.conformal_data.get("calibration_thresholds", {}).get(coverage_key)

        if not threshold_info:
            raise ValueError(f"No calibrated threshold found for coverage level: {coverage_val}")

        threshold_q = float(threshold_info["threshold_q"])
        lower = round(score_point - threshold_q, 4)
        upper = round(score_point + threshold_q, 4)
        width = round(upper - lower, 4)

        # Mathematical assertions
        assert lower <= score_point <= upper, "Invalid prediction interval bounds ordering!"
        assert lower < upper, "Degenerate prediction interval width!"

        return PredictionResponse(
            estimated_wellbeing_score=round(score_point, 2),
            prediction_interval=PredictionInterval(
                nominal_coverage=coverage_val,
                lower=round(lower, 2),
                upper=round(upper, 2),
                width=round(width, 4)
            ),
            model_version=self.model_version,
            uncertainty_method=self.uncertainty_method,
            predicted_mental_health_score=round(score_point, 2)
        )

# Global singleton
model_service = ModelService()
