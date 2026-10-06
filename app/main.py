import time
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response, status, HTTPException
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.configuration import settings
from app.schemas import (
    StudentSurveyRequest,
    PredictionResponse,
    ExplanationResponse,
    HealthResponse,
    ErrorResponse
)
from app.model_service import model_service
from app.explanation_service import explanation_service
from app.monitoring import metrics_collector
from app.governance import registry_manager, shadow_manager

# Configure production logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler: loads model and explainer once at application startup."""
    logger.info("Initializing application startup...")
    try:
        # Load and verify model & conformal calibration
        model_service.verify_and_load()
        logger.info("Model service successfully initialized and verified.")
        
        # Initialize SHAP explainer
        explanation_service.initialize()
        logger.info("Explanation service successfully initialized.")
    except Exception as exc:
        logger.critical(f"FATAL: Application startup failed: {exc}", exc_info=True)
        raise exc

    yield  # Application is serving requests

    logger.info("Application shutdown initiated. Releasing resources...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=(
        "Production REST API for continuous survey-based wellbeing score prediction, "
        "calibrated 80/90/95% prediction intervals (5-fold OOF cross-conformal), "
        "and TreeSHAP feature attribution.\n\n"
        "**Responsible AI Notice:** Predictions represent statistical wellbeing scores "
        "estimated from survey habits and do not constitute clinical assessment, diagnosis, "
        "or treatment recommendations."
    ),
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Latency and request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    # Record privacy-safe operational metrics
    metrics_collector.record_request(request.url.path, response.status_code, duration_ms)
    
    # Safe logging: log method, endpoint, status, and duration without sensitive body data
    logger.info(
        f"{request.method} {request.url.path} "
        f"Status: {response.status_code} - Latency: {duration_ms:.2f}ms"
    )
    return response

# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    metrics_collector.record_validation_failure()
    errors = []
    for err in exc.errors():
        field_loc = err.get("loc", [])
        field_name = str(field_loc[-1]) if field_loc else "unknown"
        errors.append({
            "field": field_name,
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type", "value_error")
        })
    logger.warning(f"Validation failure on {request.url.path}: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": errors,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.warning(f"Value error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Invalid Input",
            "detail": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred while processing the request.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@app.get(
    "/",
    summary="Root Endpoint",
    description="Welcome message and API service metadata."
)
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
        "metrics": "/metrics",
        "governance": "/governance/champion",
        "ui": "/ui"
    }

@app.get("/ui", include_in_schema=False)
def serve_ui():
    index_path = settings.MODEL_PATH.parent.parent / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend index.html not found")

@app.get("/style.css", include_in_schema=False)
def serve_css():
    css_path = settings.MODEL_PATH.parent.parent / "style.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS not found")

@app.get("/script.js", include_in_schema=False)
def serve_js():
    js_path = settings.MODEL_PATH.parent.parent / "script.js"
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JS not found")

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health and Readiness Check",
    description="Returns operational readiness of the model pipeline and conformal uncertainty calibrator."
)
def health():
    if not model_service.is_loaded or not model_service.uncertainty_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model or uncertainty engine is not loaded"
        )
    return HealthResponse(
        status="ok",
        model_loaded=model_service.is_loaded,
        uncertainty_loaded=model_service.uncertainty_loaded,
        model_version="phase5_tuned_extra_trees",
        uncertainty_method="5-fold OOF conformal",
        model_hash_verified=True
    )

@app.get(
    "/metrics",
    summary="Operational Observability & Metrics",
    description=(
        "Exposes Prometheus-formatted operational counters and histograms (or JSON summary "
        "when requested). Strictly aggregates telemetry without student PII or raw survey payloads."
    )
)
def metrics(format: str = "prometheus"):
    if format.lower() == "json":
        return metrics_collector.get_summary_statistics()
    return PlainTextResponse(metrics_collector.export_prometheus(), media_type="text/plain; version=0.0.4")

@app.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict Wellbeing Score & Calibrated Interval",
    description=(
        "Synchronously predicts estimated student wellbeing score and computes calibrated "
        "conformal prediction intervals centered on the frozen Phase 5 Extra Trees model."
    )
)
def predict(data: StudentSurveyRequest):
    resp = model_service.predict(data)
    width = resp.prediction_interval.width if resp.prediction_interval else None
    metrics_collector.record_prediction(resp.estimated_wellbeing_score, width)
    return resp

@app.post(
    "/explain",
    response_model=ExplanationResponse,
    summary="Compute TreeSHAP Explanations",
    description=(
        "Computes TreeSHAP feature contributions aggregated back to the 12 original survey features. "
        "Latency is approximately ~1.4s due to exact tree traversal across 500 trees."
    )
)
def explain(data: StudentSurveyRequest):
    metrics_collector.record_explanation()
    return explanation_service.explain(data)

@app.get(
    "/governance/champion",
    summary="Champion Model Governance Metadata",
    description="Returns verified metadata, cryptographic SHA-256 hash, and calibration information for the production champion model."
)
def get_governance_champion():
    valid, msg = registry_manager.verify_champion_integrity()
    champ = registry_manager.get_champion()
    return {
        "champion": champ,
        "integrity_verified": valid,
        "integrity_message": msg,
        "governance_status": "LOCKED_IN_PRODUCTION"
    }

@app.get(
    "/governance/registry",
    summary="Model Registry Overview",
    description="Returns registered challenger models, lifecycle states, and immutable governance audit trail."
)
def get_governance_registry():
    return {
        "registry_version": "1.0.0",
        "champion_version": registry_manager.get_champion().get("model_version"),
        "challengers": registry_manager.get_challengers(),
        "audit_log": registry_manager.get_audit_log(),
        "governance_policy": {
            "automatic_retraining": "STRICTLY_FORBIDDEN",
            "automatic_promotion": "STRICTLY_FORBIDDEN",
            "promotion_requires_human_approval": True
        }
    }

@app.get(
    "/governance/shadow",
    summary="Shadow Serving Statistics",
    description="Returns aggregate paired difference statistics between Champion and Candidate models without exposing raw inputs."
)
def get_governance_shadow():
    return shadow_manager.get_summary()
