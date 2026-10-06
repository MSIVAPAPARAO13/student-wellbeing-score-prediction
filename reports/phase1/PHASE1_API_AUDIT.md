# Phase 1: FastAPI Backend Service Audit

**Service Name:** Student Mental Health Prediction API  
**Framework:** FastAPI (0.142.2) on Uvicorn (0.54.0)  
**Entry Point:** `main.py`  
**Audit Date:** October 2026  
**Verification Method:** Empirical HTTP testing via `fastapi.testclient.TestClient` and live daemon execution  

---

## 1. API Architecture & Routing Summary

The current backend is a single-file application (`main.py`) containing 74 lines of code.

### Endpoints Verified:

| Method | Route | Purpose | Status Code | Response Type | Verified Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Welcome banner | `200 OK` | `application/json` | Returns `["Welcome to Sheryians AI School Guys"]`. (BUG: code returns a Python `set`, serialized as a JSON array). |
| `GET` | `/health` | Liveness probe | `404 Not Found` | `application/json` | Missing. Returns `{"detail":"Not Found"}`. |
| `POST` | `/predict` | Single student inference | `200 OK` / `422` | `application/json` | Consumes `StudentData`, predicts score, returns `{"predicted_mental_health_score": 6.19}`. |
| `GET` | `/docs` | OpenAPI Swagger UI | `200 OK` | `text/html` | Interactive Swagger documentation active and operational. |
| `GET` | `/openapi.json`| OpenAPI Schema | `200 OK` | `application/json` | Valid OpenAPI 3.1.0 schema generated automatically. |

---

## 2. Request & Response Schemas

### 2.1 Request Schema: `StudentData` (Pydantic V2)
```python
class StudentData(BaseModel):
    age                     : int = Field(..., ge=10, le=100)
    gender                  : Literal['Male', 'Female']
    country                 : str
    academic_level          : Literal['Undergraduate', 'Graduate', 'High School']
    most_used_platform      : Literal['Facebook', 'LinkedIn', 'Instagram', 'Snapchat','Twitter','YouTube', 'TikTok', 'LINE', 'KakaoTalk', 'VKontakte', 'WhatsApp','WeChat']
    purpose_of_use          : Literal['Networking', 'Education', 'Entertainment', 'News']
    avg_daily_usage_hours   : float = Field(..., ge=0, le=24)
    daily_unlocks           : int   = Field(..., ge=0)
    study_hours             : float = Field(..., ge=0, le=24)
    physical_activity_hours : float = Field(..., ge=0, le=24)
    sleep_hours_per_night   : float = Field(..., ge=0, le=24)
    stress_level            : Literal['Medium', 'Low', 'Very High', 'High']
```

### 2.2 Response Schema: `PredictionResponse`
```python
class PredictionResponse(BaseModel):
    predicted_mental_health_score: float
```

---

## 3. Schema & Validation Deficiencies

1. **Unbounded Unlocks (`daily_unlocks`):**
   - Defined as `Field(..., ge=0)` without an upper bound (`le` is missing).
   - An adversary can submit `daily_unlocks: 50000000`, causing numerical overflow or distorted outlier predictions.
2. **Age Domain Mismatch:**
   - Schema allows `age` from 10 to 100.
   - The training dataset strictly contains young adult students aged **18 to 24**.
   - Submitting an age of 85 causes the model to extrapolate far beyond its training support without warning.
3. **Unvalidated Country Strings:**
   - `country: str` accepts arbitrary text, emoji, or injection strings (e.g. `"<script>"`).
   - While sanitized by the top-10 check into `"Other"`, input validation should restrict string length (e.g., `max_length=60`).
4. **Hardcoded Category Lookup:**
   - Line 9 hardcodes: `top_countries = ['Other','India','USA','Canada','Australia','UK','Germany','Mexico','Turkey','France']`.
   - This tight-couples backend code to training artifacts. If the model pipeline changes categories, the API silently becomes inconsistent.

---

## 4. Model Loading & Inference Execution

### 4.1 Eager Top-Level Loading
* **Implementation:** `model = joblib.load('Mental_Health_Model.pkl')` at module level (Line 8).
* **Risks:**
  - If the pickle file is corrupt, missing, or throws a version incompatibility error, the entire Uvicorn worker crashes on startup.
  - Does not support async lifespan management (`@asynccontextmanager`), warmups, or clean resource deallocation.

### 4.2 Dataframe Construction Overhead
* For every incoming request, a new Pandas `DataFrame` is instantiated on the fly:
  ```python
  input_row = pd.DataFrame([{...}])
  prediction = model.predict(input_row)[0]
  ```
* While acceptable for low-concurrency demonstrations, constructing a single-row Pandas DataFrame per request introduces ~5–10ms of unnecessary overhead compared to pre-structured NumPy vectors or dictionary records.

---

## 5. Security & Configuration Audit

1. **Permissive CORS Configuration:**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```
   - Allows all origins, methods, and headers.
   - Suitable only for local prototyping; production deployments must restrict allowed origins via environment variables.
2. **Absence of Rate Limiting:**
   - No rate limiting (e.g. `slowapi` or Redis token bucket) exists.
   - The API is vulnerable to Denial of Service (DoS) via concurrent heavy Random Forest inference requests.
3. **No Request Size Bounds:**
   - Uvicorn accepts arbitrary payload sizes, leaving memory vulnerable to oversized requests.

---

## 6. Recommended V2 API Architecture

```text
backend/app/
├── api/
│   └── v1/
│       ├── endpoints/
│       │   ├── health.py        # GET /api/v1/health (Checks model loaded, uptime)
│       │   ├── predict.py       # POST /api/v1/predict (Single & batch prediction)
│       │   └── explain.py       # POST /api/v1/explain (SHAP waterfall feature contributions)
│       └── router.py
├── core/
│   ├── config.py                # Pydantic BaseSettings (.env loading, CORS)
│   └── logging.py               # Structured JSON logging
├── schemas/
│   ├── student.py               # Robust validation with domain bounds
│   └── prediction.py            # Score + prediction intervals + risk tier
├── services/
│   └── model_service.py         # Async lifespan manager, model warmups, SHAP explainer
└── main.py                      # Clean application factory
```
