# Phase 1: V2 Comprehensive Implementation Roadmap

**Project Vision:** Explainable, Production-Grade Student Wellbeing Analytics System  
**Architecture:** Python FastAPI Backend + React/Bootstrap Frontend + Scikit-learn/Gradient Boosting ML Pipeline  
**Priority Tiers:**  
* **P0:** Critical (Prerequisites, Leakage Prevention, Git Hygiene, Core Functionality)  
* **P1:** High Value (Model Benchmarking, SHAP Explainability, Production API & Frontend)  
* **P2:** Medium Value (Uncertainty Quantification, Testing Suite, Containerization)  
* **P3:** Advanced / Operational (Monitoring, CI/CD, Drift Tracking)  

---

## 1. Roadmap Matrix Across Lifecycle Phases

| Phase | Focus Area | Deliverables | Priority |
| :--- | :--- | :--- | :--- |
| **Phase 2** | Leakage Prevention & Data Pipeline | Modular ingestion script; strict 80/20 partition; leakage-free country transformer | **P0** |
| **Phase 3** | Feature Engineering & Ratios | Habit interaction terms (screen/sleep, unlocks/hour, study/sleep ratios); correlation filtering | **P1** |
| **Phase 4** | Model Benchmarking & Multi-Algorithm Selection | Benchmark ElasticNet, LightGBM, XGBoost, CatBoost, Regularized RF; 5-fold CV comparison | **P1** |
| **Phase 5** | Hyperparameter Optimization | Optuna Bayesian optimization on candidate models; minimize CV RMSE while bounding train-test gap | **P1** |
| **Phase 6** | Model Explainability (SHAP) | SHAP TreeExplainer integration; compute global summary and local student waterfall values | **P1** |
| **Phase 7** | Uncertainty Quantification | Conformal prediction (MAPIE) for calibrated 90% prediction intervals | **P2** |
| **Phase 8** | Production Backend Refactoring | Modular FastAPI (`backend/app/`); `/health`, `/predict`, `/explain`; Pydantic V2 domain bounds | **P0** |
| **Phase 9** | Modern Frontend (React + Bootstrap) | Responsive React SPA; Bootstrap 5; interactive SVG gauge; SHAP waterfall chart; what-if sliders | **P1** |
| **Phase 10**| Automated Testing & Quality Assurance | Pytest test suite for ML pipeline, API validation schemas, and end-to-end integration | **P2** |
| **Phase 11**| Containerization & Deployment | Multi-stage Dockerfile, docker-compose orchestration, environment variables | **P2** |
| **Phase 12**| Monitoring, MLOps & Responsible AI | Drift detection hooks, ethical non-diagnostic safeguards, documentation | **P3** |

---

## 2. Detailed Improvement Specifications

### 2.1 Machine Learning & Data Science

#### [ML-01] Leakage-Free Country Transformer & Cleaning Pipeline
* **Problem:** Top-10 frequent country categories were calculated globally across the 5,000-record dataset before the train/test split.
* **Current Implementation:** Cell 41–43 in `ML_Project.ipynb`.
* **Why it Matters:** Violates statistical independence; test set frequencies leak into the feature definition.
* **Recommended Solution:** Implement a custom Scikit-learn transformer `FrequentCategoryGrouper(top_n=10, default='Other')` fitted strictly on `X_train`.
* **Files Affected:** `ml/src/features.py`, `ml/src/data_pipeline.py`.
* **Expected Benefit:** 100% statistically clean, reproducible pipeline.
* **Risk:** Negligible.
* **Priority:** **P0** | **Phase 2**

#### [ML-02] Cross-Validation Protocol & Strict Holdout Test Partition
* **Problem:** Models were evaluated and selected based on a single 30% test set split.
* **Current Implementation:** `test_size=0.30, random_state=42`.
* **Why it Matters:** Single-split evaluation is noisy and causes overfitting to that particular split.
* **Recommended Solution:** Fix an 80/20 split. Evaluate all candidate models strictly via 5-Fold Cross-Validation on the 80% training set. Evaluate the winning model once against the untouched 20% holdout test set.
* **Files Affected:** `ml/src/train.py`, `ml/src/evaluate.py`.
* **Expected Benefit:** Reliable generalization metric with known variance ($\pm \sigma$).
* **Risk:** Low.
* **Priority:** **P0** | **Phase 2**

#### [ML-03] Domain-Specific Feature Engineering
* **Problem:** Only a single feature (`Grouped_country`) was engineered.
* **Recommended Solution:** Test meaningful behavioural ratios:
  1. `screen_to_sleep_ratio = Avg_Daily_Usage_Hours / (Sleep_Hours_Per_Night + 0.1)`
  2. `study_to_sleep_ratio = Study_Hours / (Sleep_Hours_Per_Night + 0.1)`
  3. `unlocks_per_usage_hour = Daily_Unlocks / (Avg_Daily_Usage_Hours + 0.1)`
  4. `active_vs_sedentary = Physical_Activity_Hours / (Avg_Daily_Usage_Hours + 0.1)`
* **Files Affected:** `ml/src/features.py`.
* **Expected Benefit:** Enhanced signal capture for linear and gradient boosted models.
* **Risk:** Must check for multicollinearity using Variance Inflation Factor (VIF).
* **Priority:** **P1** | **Phase 3**

#### [ML-04] Multi-Algorithm Benchmarking
* **Problem:** Baseline only compared unconstrained Random Forest to Linear Regression.
* **Recommended Solution:** Benchmark Ridge, ElasticNet, LightGBM, XGBoost, CatBoost, and Regularized Random Forest.
* **Files Affected:** `ml/src/train.py`, `ml/experiments/`.
* **Expected Benefit:** Faster inference, smaller model artifacts ($< 5\text{MB}$ vs 25.7MB), and reduced overfitting gap ($< 5\%$).
* **Risk:** Low.
* **Priority:** **P1** | **Phase 4**

#### [ML-05] SHAP Model Explainability
* **Problem:** The model operates as a complete black box to students and researchers.
* **Recommended Solution:** Integrate `shap.TreeExplainer` into the inference service to return the top positive and negative contributing habits for any predicted student score.
* **Files Affected:** `backend/app/services/model_service.py`, `backend/app/api/v1/endpoints/explain.py`.
* **Expected Benefit:** Transform opaque predictions into actionable, interpretable wellness guidance.
* **Risk:** SHAP latency must be kept under 50ms per request.
* **Priority:** **P1** | **Phase 6**

#### [ML-06] Conformal Prediction Intervals (Uncertainty Quantification)
* **Problem:** Predictions are single point scores (e.g. 6.25) which convey false precision.
* **Recommended Solution:** Calibrate conformal prediction intervals (e.g. 90% confidence interval: $[5.65, 6.85]$) using MAPIE or split-conformal quantile regression.
* **Files Affected:** `ml/src/uncertainty.py`, `backend/app/schemas/prediction.py`.
* **Expected Benefit:** Communicates uncertainty responsibly, crucial for student wellbeing contexts.
* **Risk:** Low.
* **Priority:** **P2** | **Phase 7**

---

### 2.2 Backend & API Architecture

#### [API-01] Modular FastAPI Refactoring
* **Problem:** The entire backend is a flat 74-line script (`main.py`) with no module structure.
* **Recommended Solution:** Restructure into `backend/app/` with clean separation:
  - `core/`: settings and logging
  - `api/v1/`: versioned endpoints
  - `schemas/`: Pydantic V2 models
  - `services/`: model loading and prediction logic
* **Files Affected:** `backend/app/main.py`, `backend/app/core/config.py`.
* **Expected Benefit:** Production maintainability, testability, and clean dependency injection.
* **Priority:** **P0** | **Phase 8**

#### [API-02] Health & Liveness Probes
* **Problem:** `GET /health` returns 404 Not Found.
* **Recommended Solution:** Implement `GET /api/v1/health` returning service status, model version, and loaded artifact metadata.
* **Files Affected:** `backend/app/api/v1/endpoints/health.py`.
* **Expected Benefit:** Enables Docker and Kubernetes health checking.
* **Priority:** **P0** | **Phase 8**

#### [API-03] Strict Domain Bounds in Pydantic Schemas
* **Problem:** `daily_unlocks` is unbounded; `age` allows 10–100 despite training data being 18–24.
* **Recommended Solution:** Constrain `daily_unlocks: int = Field(..., ge=0, le=1000)` and add soft warning / bounded validation on `age`.
* **Files Affected:** `backend/app/schemas/student.py`.
* **Expected Benefit:** Rejection of malicious or out-of-distribution inputs.
* **Priority:** **P0** | **Phase 8**

---

### 2.3 Frontend & User Experience

#### [FE-01] Migration to React + Bootstrap
* **Problem:** Vanilla HTML/CSS/JS frontend is difficult to maintain and lacks modern component-based state management.
* **Recommended Solution:** Build a modern Single Page Application (SPA) using React 18+ and Bootstrap 5 with custom CSS variables (no Tailwind).
* **Components:**
  1. `AssessmentForm`: Validated inputs with clean slider/stepper controls.
  2. `WellbeingGauge`: Animated SVG speedometer indicating score (0–10) and risk tier.
  3. `ShapWaterfallChart`: Interactive horizontal bar chart visualizing habit contributions.
  4. `WhatIfSimulator`: Interactive sliders allowing students to simulate habit adjustments (e.g. +1 hr sleep).
* **Files Affected:** `frontend/src/`.
* **Expected Benefit:** Professional, responsive, accessible user experience.
* **Priority:** **P1** | **Phase 9**

---

### 2.4 Repository & DevOps Hygiene

#### [DEV-01] Git Cleanliness & .gitignore Setup
* **Problem:** No `.gitignore` file exists. The 25.7MB pickle artifact and `__pycache__` directories are committed to Git.
* **Recommended Solution:** Create standard `.gitignore`, untrack cached bytecode, and establish clean model storage.
* **Files Affected:** `.gitignore`.
* **Expected Benefit:** Prevents repository bloat and clean Git logs.
* **Priority:** **P0** | **Phase 1 / Phase 2**

#### [DEV-02] Dependency Pinning
* **Problem:** Root `requirements.txt` has unpinned package names.
* **Recommended Solution:** Create `backend/requirements.txt` with exact version pins and `backend/requirements-dev.txt` for development tools.
* **Priority:** **P0** | **Phase 1 / Phase 2**
