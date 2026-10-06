import os
from pathlib import Path
from typing import List

# Detect root directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME: str = "Student Mental Health / Wellbeing Prediction Service"
    API_VERSION: str = "v1"
    API_ENV: str = os.getenv("API_ENV", "production")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Model configuration
    MODEL_PATH: Path = Path(os.getenv("MODEL_PATH", str(BASE_DIR / "models" / "phase5_tuned_extra_trees.joblib")))
    METADATA_PATH: Path = Path(os.getenv("METADATA_PATH", str(BASE_DIR / "models" / "phase5_metadata.json")))
    CONFORMAL_PATH: Path = Path(os.getenv("CONFORMAL_PATH", str(BASE_DIR / "models" / "phase7_1_conformal_calibration.json")))
    REGISTRY_PATH: Path = Path(os.getenv("REGISTRY_PATH", str(BASE_DIR / "models" / "model_registry.json")))
    
    # Authoritative SHA-256 hash from Phase 7.1
    MODEL_EXPECTED_HASH: str = os.getenv(
        "MODEL_EXPECTED_HASH",
        "a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8"
    )
    
    # Default allowed origins
    DEFAULT_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5173",
        "null"
    ]
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        raw = os.getenv("ALLOWED_ORIGINS")
        if not raw:
            return self.DEFAULT_ORIGINS
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        return origins if origins else self.DEFAULT_ORIGINS

settings = Settings()
