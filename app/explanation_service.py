import logging
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
import shap

from app.model_service import model_service
from app.schemas import (
    StudentSurveyRequest,
    ExplanationResponse,
    FeatureContribution,
    RESPONSIBLE_AI_DISCLAIMER
)

logger = logging.getLogger("uvicorn.error")

SURVEY_FEATURES = [
    "Age", "Gender", "Academic_Level", "Country", "Avg_Daily_Usage_Hours",
    "Most_Used_Platform", "Daily_Unlocks", "Sleep_Hours_Per_Night",
    "Study_Hours", "Physical_Activity_Hours", "Stress_Level", "Purpose_Of_Use"
]

class ExplanationService:
    def __init__(self):
        self.explainer = None
        self.transformed_feature_names: List[str] = []
        self.feature_mapping: Dict[str, str] = {}
        self.base_value: Optional[float] = None
        self.is_initialized: bool = False

    def initialize(self):
        """Initializes TreeExplainer on ExtraTreesRegressor and caches feature mapping."""
        if not model_service.is_loaded or model_service.model is None:
            raise RuntimeError("ModelService must be loaded before initializing ExplanationService.")

        pipeline = model_service.model
        preprocessor = pipeline.named_steps["preprocessor"]
        extra_trees_model = pipeline.named_steps["model"]

        # Derive transformed feature names
        names = []
        for name, trans, cols in preprocessor.transformers_:
            if name == "skewed":
                names.extend([f"skewed__{c}" for c in cols])
            elif name == "numeric":
                names.extend([f"numeric__{c}" for c in cols])
            elif name == "ordinal":
                names.extend([f"ordinal__{c}" for c in cols])
            elif name == "nominal":
                ohe = trans.named_steps["encoder"]
                ohe_cols = ohe.get_feature_names_out(cols)
                names.extend([f"nominal__{c}" for c in ohe_cols])

        self.transformed_feature_names = names

        # Build mapping: transformed feature -> original survey feature
        mapping = {}
        for col in self.transformed_feature_names:
            matched = False
            for orig in SURVEY_FEATURES:
                if orig in col:
                    mapping[col] = orig
                    matched = True
                    break
            if not matched and "Grouped_country" in col:
                mapping[col] = "Country"

        self.feature_mapping = mapping
        logger.info(f"ExplanationService mapped {len(self.feature_mapping)} transformed features to original features.")

        # Initialize TreeExplainer
        logger.info("Initializing TreeExplainer on ExtraTreesRegressor (500 trees)...")
        self.explainer = shap.TreeExplainer(extra_trees_model)
        self.base_value = float(np.ravel(self.explainer.expected_value)[0])
        self.is_initialized = True
        logger.info(f"TreeExplainer initialized successfully. Expected base value = {self.base_value:.4f}")

    def explain(self, req: StudentSurveyRequest) -> ExplanationResponse:
        """Computes TreeSHAP values for single request and aggregates to original 12 features."""
        if not self.is_initialized or self.explainer is None:
            raise RuntimeError("ExplanationService is not initialized.")

        pipeline = model_service.model
        preprocessor = pipeline.named_steps["preprocessor"]
        extra_trees_model = pipeline.named_steps["model"]

        df_input = model_service.format_input_dataframe(req)
        X_trans = preprocessor.transform(df_input)
        X_trans_df = pd.DataFrame(X_trans, columns=self.transformed_feature_names)

        # Compute SHAP explanation
        shap_res = self.explainer(X_trans_df)
        shap_vals = shap_res.values[0]  # Array of 38 numbers
        base_val = float(np.ravel(shap_res.base_values)[0])
        pred_val = float(extra_trees_model.predict(X_trans)[0])

        # Aggregate SHAP contributions back to original 12 survey dimensions
        aggregated: Dict[str, float] = {f: 0.0 for f in SURVEY_FEATURES}
        for col_name, val in zip(self.transformed_feature_names, shap_vals):
            orig_feature = self.feature_mapping.get(col_name, "Other")
            if orig_feature in aggregated:
                aggregated[orig_feature] += float(val)

        # Extract request values dictionary
        req_dict = {
            "Age": req.Age,
            "Gender": req.Gender,
            "Academic_Level": req.Academic_Level,
            "Country": req.Country,
            "Avg_Daily_Usage_Hours": req.Avg_Daily_Usage_Hours,
            "Most_Used_Platform": req.Most_Used_Platform,
            "Daily_Unlocks": req.Daily_Unlocks,
            "Sleep_Hours_Per_Night": req.Sleep_Hours_Per_Night,
            "Study_Hours": req.Study_Hours,
            "Physical_Activity_Hours": req.Physical_Activity_Hours,
            "Stress_Level": req.Stress_Level,
            "Purpose_Of_Use": req.Purpose_Of_Use
        }

        # Build feature contribution objects with safe language
        contributions: List[FeatureContribution] = []
        for feat in SURVEY_FEATURES:
            net_shap = round(aggregated[feat], 4)
            if net_shap > 0.005:
                direction = "positive"
                interp = "Associated with a higher model-predicted wellbeing score."
            elif net_shap < -0.005:
                direction = "negative"
                interp = "Associated with a lower model-predicted wellbeing score."
            else:
                direction = "neutral"
                interp = "Minimal estimated impact on predicted wellbeing score."

            contributions.append(FeatureContribution(
                feature=feat,
                value=req_dict[feat],
                shap_value=net_shap,
                direction=direction,
                interpretation=interp
            ))

        # Sort positive and negative contributors
        positive_contributors = sorted(
            [c for c in contributions if c.direction == "positive"],
            key=lambda x: x.shap_value,
            reverse=True
        )
        negative_contributors = sorted(
            [c for c in contributions if c.direction == "negative"],
            key=lambda x: x.shap_value
        )

        return ExplanationResponse(
            estimated_wellbeing_score=round(pred_val, 2),
            base_value=round(base_val, 2),
            feature_contributions=contributions,
            positive_contributors=positive_contributors,
            negative_contributors=negative_contributors,
            model_version=model_service.model_version,
            disclaimer=RESPONSIBLE_AI_DISCLAIMER
        )

# Global singleton
explanation_service = ExplanationService()
