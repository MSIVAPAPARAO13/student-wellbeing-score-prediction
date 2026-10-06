# Phase 1: Comprehensive Project Audit Report

**Project Name:** Student Mental Health / Student Wellbeing Score Prediction  
**Repository Corpus:** tanishq-latent/Mental-Health-Score  
**Audit Date:** October 2026  
**Auditor:** Antigravity AI Pair Programmer  

---

## 1. Executive Summary

This audit represents a complete, forensic inspection of the **Student Mental Health Score Prediction** repository. The system is designed to predict a continuous student mental health score (scale: 0.0 to 10.0) based on demographic attributes, digital device usage patterns, academic variables, and lifestyle factors.

The project currently consists of:
1. An exploratory and training Jupyter Notebook (`ML_Project.ipynb`) which processes a 5,000-record CSV dataset and saves a Scikit-Learn `Pipeline`.
2. A serialized Scikit-learn Pipeline artifact (`Mental_Health_Model.pkl`, ~25.7 MB) containing a `ColumnTransformer` and a `RandomForestRegressor`.
3. A lightweight FastAPI application (`main.py`) providing a `/predict` REST endpoint.
4. A static vanilla frontend (`index.html`, `style.css`, `script.js`) presenting an editorial dark-themed UI with an interactive SVG gauge.
5. An architectural presentation document (`ML Project.html`).

While the baseline achieves strong predictive correlation on the single holdout test set (Test $R^2 \approx 0.878$, MAE $\approx 0.347$), our audit revealed severe technical debt, subtle data leakage in category grouping, severe model overfitting (Train $R^2 \approx 0.981$), an unversioned deployment script pointing to a dormant remote server, and git tracking of large binary model files.

---

## 2. Complete Repository Inventory

| File / Path | Purpose | Technology | Used By | Input | Output | Status | Problems Identified | Recommended Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `Student Social Media And Mental Health Impact.csv` | Primary training dataset | CSV tabular data | `ML_Project.ipynb` | Raw survey records | 5,000 records × 13 fields | **KEEP** | Contains 2 duplicate rows and 10 negative physical activity values | Clean via reproducible pipeline; keep raw file intact |
| `ML_Project.ipynb` | Data exploration, cleaning, training & tuning | Jupyter Notebook, Python 3, Scikit-learn | Data Scientist / Developer | Raw CSV dataset | `Mental_Health_Model.pkl` | **KEEP** | Leakage in country grouping; severe RF overfitting; mismatch between markdown docs and code | Retain as reference; migrate production pipeline to modular Python scripts |
| `Mental_Health_Model.pkl` | Serialized model pipeline artifact | Joblib / Pickle (Python 3.12/3.13, Scikit-Learn 1.9.0/1.6.1) | `main.py` | DataFrame of student features | Vector of continuous scores | **KEEP (TEMPORARY)** | 25.7 MB binary tracked directly in Git repository; default unpruned RF saved instead of tuned model | Re-train cleanly in V2, move to dedicated artifacts storage / Git LFS or release asset |
| `main.py` | REST API backend service | FastAPI, Uvicorn, Pydantic v2 | Frontend / Client consumers | JSON request payload | JSON prediction response | **MODIFY** | Root `/` returns a set instead of JSON dict; no `/health` endpoint; wildcard CORS; eager top-level model load | Refactor into modular FastAPI architecture (`backend/app/`) with versioned endpoints |
| `requirements.txt` | Python dependency declarations | Plain text | Pip / Virtualenv | N/A | Environment state | **MODIFY** | Unpinned versions; no separation between production and development tooling | Split into `backend/requirements.txt` and `backend/requirements-dev.txt` with pinned versions |
| `index.html` | Client-facing web user interface | HTML5, Semantic markup | End users / Web browsers | User form entries | Rendered score & UI gauge | **KEEP** | Hardcoded scripts; single-page monolithic HTML | Maintain as V1 fallback; migrate to React + Bootstrap in Phase 9 |
| `style.css` | Styling and visual design system | Vanilla CSS3, Custom Properties | `index.html` | N/A | Rendered layout & typography | **KEEP** | Fixed media queries; coupled directly to vanilla HTML classes | Retain for V1 static view; port tokens into V2 design system |
| `script.js` | Frontend interaction and API client | Vanilla ES6 JavaScript | `index.html` | DOM events, user inputs | API HTTP requests, DOM updates | **MODIFY** | Hardcoded Render backend URL that times out on local execution; lack of configuration | Add dynamic host resolution; transition to modern React state management |
| `ML Project.html` | Architectural blueprint and presentation guide | HTML5, SVG diagrams, CSS | Documentation / Onboarding | N/A | Rendered blueprint | **KEEP** | Static standalone file; not connected to codebase | Move to documentation / references folder |
| `README.md` | Repository documentation | Markdown (UTF-16LE) | Developers / GitHub | N/A | Rendered docs | **MODIFY** | Encoded in UTF-16LE; contains only 1 line (`# Mansik-Santulan-Score`) | Rewrite completely with proper UTF-8 encoding and architecture details |
| `.vscode/settings.json` | VS Code workspace configuration | JSON | Visual Studio Code | N/A | IDE environment settings | **KEEP** | Uses system Python interpreter manager | Keep for developer consistency |
| `__pycache__/` | Compiled Python bytecode | Python bytecode (`.pyc`) | Python runtime | `.py` source files | `.pyc` files | **REMOVE FROM GIT** | Tracked in Git history (`main.cpython-310.pyc`, etc.) | Add `.gitignore` and untrack from Git |
| `venv/` | Python virtual environment | Virtualenv | Python execution | N/A | Installed libraries | **KEEP (LOCAL ONLY)** | Windows Application Control policy blocks C-extension DLLs (`_cd_fast.pyd`) within Music folder | Use system Python or configured virtual environment in allowed directory |

---

## 3. End-to-End System Data Flow

```text
[Raw Dataset: CSV]
       │
       ▼
[Data Cleaning: drop_duplicates, clip(lower=0)]
       │
       ▼
[Feature Engineering: group_countries (Top 10 + 'Other')]  <-- *POTENTIAL LEAKAGE (Computed on Full Data)*
       │
       ▼
[Train / Test Split: 70% Train (3,500) / 30% Test (1,500), random_state=42]
       │
       ▼
[ColumnTransformer Preprocessing]
  ├── Skewed ('Study_Hours') ──> log1p ──> StandardScaler
  ├── Plain Numeric (5 features) ──> StandardScaler
  ├── Ordinal ('Stress_Level') ──> OrdinalEncoder(['Low', 'Medium', 'High', 'Very High'])
  └── Nominal (5 features) ──> OneHotEncoder(handle_unknown='ignore')
       │
       ▼
[Model Training: RandomForestRegressor(random_state=42, n_estimators=100)]
       │
       ▼
[Model Evaluation: Single Test Set (Test R²=0.878, Train R²=0.981)]
       │
       ▼
[Serialization: joblib.dump(rf_pipeline, 'Mental_Health_Model.pkl')]
       │
       ▼
[FastAPI Backend: main.py]
  ├── Top-level eager load of Mental_Health_Model.pkl
  ├── Pydantic validation via StudentData schema
  └── POST /predict -> Pipeline.predict(input_row) -> PredictionResponse
       │
       ▲  HTTP POST (JSON)
       │
[Frontend Interface: index.html + script.js]
  ├── User inputs form fields
  ├── Client-side validation in script.js
  └── Renders SVG Gauge, Numerical Score, and Health Band
```

---

## 4. Current vs Target Architecture

### Current Structure (Flat / Monolithic)
```text
Mental-Health-Score/
├── .vscode/
├── ML Project.html
├── ML_Project.ipynb
├── Mental_Health_Model.pkl
├── README.md
├── Student Social Media And Mental Health Impact.csv
├── __pycache__/
├── index.html
├── main.py
├── requirements.txt
├── script.js
├── style.css
└── venv/
```

### Problems with Current Structure
1. **Root Directory Clutter:** ML training notebooks, serialized large model binaries, API code, static web assets, and raw data all share the root directory.
2. **No Clear Separation of Concerns:** ML code, backend services, and frontend presentation are mingled together, preventing independent containerization or CI testing.
3. **Git Hygiene Issues:** The 25.7 MB pickle file and `__pycache__` binaries are checked into Git version control. No `.gitignore` file exists.
4. **Lack of Automated Testing:** Zero automated unit or integration tests exist in the repository.

### Target Architecture (V2 Clean Modular Structure)
```text
Explainable-Student-Wellbeing-Prediction/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── health.py
│   │   │       │   ├── predict.py
│   │   │       │   └── explain.py
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── logging.py
│   │   ├── schemas/
│   │   │   ├── prediction.py
│   │   │   └── explanation.py
│   │   ├── services/
│   │   │   └── model_service.py
│   │   └── main.py
│   ├── tests/
│   │   ├── test_api.py
│   │   └── test_validation.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AssessmentForm.jsx
│   │   │   ├── GaugeReadout.jsx
│   │   │   ├── ExplanationChart.jsx
│   │   │   └── DisclaimerModal.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── index.jsx
│   ├── package.json
│   └── package-lock.json
│
├── ml/
│   ├── data/
│   │   ├── raw/
│   │   └── processed/
│   ├── notebooks/
│   │   └── 01_exploratory_data_analysis.ipynb
│   ├── src/
│   │   ├── data_pipeline.py
│   │   ├── features.py
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   └── explain.py
│   └── tests/
│       └── test_pipeline.py
│
├── models/
│   └── baseline_rf.joblib
│
├── reports/
│   ├── phase1/
│   └── figures/
│
├── .gitignore
├── README.md
└── docker-compose.yml
```

---

## 5. Security & Technical Debt Audit

1. **CORS Wildcard Policy:** In `main.py`, `allow_origins=["*"]` permits cross-origin requests from any origin without authentication or CSRF tokens. Acceptable for local dev, dangerous in production.
2. **Missing Input Bounds:** In `main.py`, `daily_unlocks` accepts any integer $\ge 0$ without an upper bound (`le` is missing). A user can submit $10^9$ unlocks, skewing model predictions.
3. **Hardcoded URLs:** In `script.js`, the remote backend URL `https://mansik-santulan-score.onrender.com` was hardcoded, causing local executions to fail upon Render service sleep.
4. **Git Hygiene:** No `.gitignore` file exists. Compiled CPython bytecode files and 25MB binary model weights are tracked in Git history.
5. **No Health Check Endpoint:** The API lacks a `/health` or `/ready` endpoint, preventing container orchestration (Kubernetes / Docker Compose) from performing liveness probes.
6. **Discrepancy Between Docs and Implementation:** The notebook documentation claims an 80/20 train/test split and SimpleImputer on all pipelines, whereas the actual code implements a 70/30 split and zero imputers.
