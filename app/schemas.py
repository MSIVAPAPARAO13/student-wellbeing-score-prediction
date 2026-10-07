from typing import Literal, Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
import math

RESPONSIBLE_AI_DISCLAIMER = (
    "This is a survey-based wellbeing score estimate and predictive uncertainty interval, "
    "not a clinical assessment or medical diagnosis."
)

class StudentSurveyRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "Age": 20,
                "Gender": "Female",
                "Academic_Level": "Undergraduate",
                "Country": "India",
                "Avg_Daily_Usage_Hours": 4.5,
                "Most_Used_Platform": "Instagram",
                "Daily_Unlocks": 120,
                "Sleep_Hours_Per_Night": 7.5,
                "Study_Hours": 3.5,
                "Physical_Activity_Hours": 1.5,
                "Stress_Level": "Medium",
                "Purpose_Of_Use": "Education",
                "coverage": 0.90
            }
        }
    )

    Age: int = Field(
        ...,
        alias="age",
        ge=10,
        le=100,
        description="Student age in years (10 to 100)"
    )
    Gender: Literal["Male", "Female", "Other", "Non-binary"] = Field(
        ...,
        alias="gender",
        description="Gender of the student"
    )
    Academic_Level: Literal["High School", "Undergraduate", "Graduate"] = Field(
        ...,
        alias="academic_level",
        description="Current academic enrollment level"
    )
    Country: str = Field(
        ...,
        alias="country",
        min_length=1,
        max_length=100,
        description="Country of residence"
    )
    Avg_Daily_Usage_Hours: float = Field(
        ...,
        alias="avg_daily_usage_hours",
        ge=0.0,
        le=24.0,
        description="Average daily social media usage in hours (0.0 to 24.0)"
    )
    Most_Used_Platform: Literal[
        "Facebook", "Instagram", "KakaoTalk", "LINE", "LinkedIn",
        "Snapchat", "TikTok", "Twitter", "VKontakte", "WeChat", "WhatsApp", "YouTube"
    ] = Field(
        ...,
        alias="most_used_platform",
        description="Most frequently used social media platform"
    )
    Daily_Unlocks: int = Field(
        ...,
        alias="daily_unlocks",
        ge=0,
        le=1000,
        description="Number of smartphone unlocks per day (0 to 1000)"
    )
    Sleep_Hours_Per_Night: float = Field(
        ...,
        alias="sleep_hours_per_night",
        ge=0.0,
        le=24.0,
        description="Average hours of sleep per night (0.0 to 24.0)"
    )
    Study_Hours: float = Field(
        ...,
        alias="study_hours",
        ge=0.0,
        le=24.0,
        description="Average daily study hours (0.0 to 24.0)"
    )
    Physical_Activity_Hours: float = Field(
        ...,
        alias="physical_activity_hours",
        ge=0.0,
        le=24.0,
        description="Average daily physical activity in hours (0.0 to 24.0)"
    )
    Stress_Level: Literal["Low", "Medium", "High", "Very High"] = Field(
        ...,
        alias="stress_level",
        description="Perceived stress level (Low, Medium, High, or Very High)"
    )
    Purpose_Of_Use: Literal["Education", "Entertainment", "Networking", "News"] = Field(
        ...,
        alias="purpose_of_use",
        description="Primary purpose of social media usage"
    )
    coverage: Optional[float] = Field(
        default=0.90,
        description="Nominal prediction interval coverage level (0.80, 0.90, or 0.95)"
    )

    @field_validator("Avg_Daily_Usage_Hours", "Sleep_Hours_Per_Night", "Study_Hours", "Physical_Activity_Hours", mode="after")
    @classmethod
    def check_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Numeric values must be finite numbers (not NaN or Inf)")
        return v

    @field_validator("Country", mode="after")
    @classmethod
    def clean_country(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Country cannot be an empty or whitespace-only string")
        return cleaned

    @field_validator("coverage", mode="after")
    @classmethod
    def validate_coverage(cls, v: Optional[float]) -> float:
        if v is None:
            return 0.90
        # Allow close floating point matching for 0.80, 0.90, 0.95
        allowed = [0.80, 0.90, 0.95]
        for a in allowed:
            if abs(v - a) < 1e-4:
                return a
        raise ValueError("Unsupported coverage level. Allowed values are 0.80, 0.90, or 0.95")


class PredictionInterval(BaseModel):
    nominal_coverage: float = Field(..., description="Nominal coverage target (e.g. 0.90)")
    lower: float = Field(..., description="Calibrated lower bound of prediction interval")
    upper: float = Field(..., description="Calibrated upper bound of prediction interval")
    width: float = Field(..., description="Total width of the prediction interval")


class PredictionResponse(BaseModel):
    estimated_wellbeing_score: float = Field(..., description="Model point estimate of wellbeing score")
    prediction_interval: PredictionInterval = Field(..., description="Calibrated conformal prediction interval")
    model_version: str = Field(..., description="Production model identifier")
    uncertainty_method: str = Field(..., description="Uncertainty quantification calibration method")
    disclaimer: str = Field(default=RESPONSIBLE_AI_DISCLAIMER, description="Responsible AI non-clinical notice")
    predicted_mental_health_score: Optional[float] = Field(
        None,
        description="Legacy field for backward compatibility with existing frontends"
    )


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status ('ok' or 'unhealthy')")
    model_loaded: bool = Field(..., description="Flag indicating point model is loaded")
    uncertainty_loaded: bool = Field(..., description="Flag indicating conformal calibration is loaded")
    model_version: str = Field(..., description="Model artifact identifier")
    uncertainty_method: str = Field(..., description="Uncertainty quantification method")
    model_hash_verified: bool = Field(..., description="True if model SHA-256 hash matches authoritative hash")


class FeatureContribution(BaseModel):
    feature: str = Field(..., description="Original survey feature name")
    value: Any = Field(..., description="Student input value")
    shap_value: float = Field(..., description="Net signed contribution to estimated score")
    direction: Literal["positive", "negative", "neutral"] = Field(..., description="Direction of contribution")
    interpretation: str = Field(..., description="Responsible non-clinical interpretation")


class ExplanationResponse(BaseModel):
    estimated_wellbeing_score: float = Field(..., description="Model point estimate of wellbeing score")
    base_value: float = Field(..., description="Expected baseline score across training population")
    feature_contributions: List[FeatureContribution] = Field(..., description="SHAP contributions for all 12 survey features")
    positive_contributors: List[FeatureContribution] = Field(..., description="Top features associated with higher scores")
    negative_contributors: List[FeatureContribution] = Field(..., description="Top features associated with lower scores")
    model_version: str = Field(..., description="Production model identifier")
    disclaimer: str = Field(default=RESPONSIBLE_AI_DISCLAIMER, description="Responsible AI non-clinical notice")


class ErrorResponse(BaseModel):
    error: str
    detail: Any
    timestamp: str


class FeedbackProvenance(BaseModel):
    source: str = Field(..., description="Provenance source of verified ground-truth label")
    auditor_id: Optional[str] = Field(None, description="Auditor or institutional identifier")
    verification_method: Optional[str] = Field("manual_audit", description="Ground truth collection method")


class VerifiedFeedbackSubmission(BaseModel):
    observation_id: str = Field(..., description="Target production observation ID")
    observed_score: float = Field(..., ge=1.0, le=10.0, description="Verified post-deployment score in [1.0, 10.0]")
    provenance: FeedbackProvenance = Field(..., description="Auditable provenance details")
    observation_timestamp: Optional[str] = Field(None, description="ISO timestamp of observation")
    is_historical: Optional[bool] = Field(False, description="Historical data flag (strictly forbidden if true)")

