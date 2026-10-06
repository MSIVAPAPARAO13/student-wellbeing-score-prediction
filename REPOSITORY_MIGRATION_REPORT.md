# REPOSITORY MIGRATION REPORT

**Date:** October 6, 2026  
**Project:** Student Mental Health / Student Wellbeing Score Prediction  
**Status:** **COMPLETE**

---

## 1. Migration Specification & Verification Summary

| Metric / Parameter | Value / Finding | Audit Status |
| :--- | :--- | :---: |
| **Repository** | `MSIVAPAPARAO13/student-wellbeing-score-prediction` | **VERIFIED** |
| **Migration Status** | **COMPLETE** | **VERIFIED** |
| **Old Remote** | `https://github.com/tanishq-latent/Mental-Health-Score.git` | **REPLACED** |
| **New Remote** | `https://github.com/MSIVAPAPARAO13/student-wellbeing-score-prediction.git` | **ACTIVE** |
| **Target Branch** | `main` | **TRACKING** |
| **Total Files Migrated** | **164 tracked project files** | **VERIFIED** |
| **Important Directories Migrated** | `app/`, `models/`, `ml/`, `reports/`, `tests/`, `requirements/`, `.github/` | **VERIFIED** |
| **Champion Model Hash** | `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8` | **VERIFIED (Bit-for-Bit)** |
| **Candidate Model Hash** | `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc` | **VERIFIED (Bit-for-Bit, Git LFS)** |
| **Conformal Calibration Hash (P7.1)** | `22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b` | **VERIFIED** |
| **Candidate Calibration Hash (P12)** | `b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af` | **VERIFIED** |
| **Secrets & Credentials Audit** | **PASS** (Zero `.env`, tokens, passwords, or service-accounts found) | **VERIFIED** |
| **Automated Tests** | **50 passed, 0 failed, 0 skipped** (`pytest -q` in 17.82s) | **VERIFIED** |
| **Application Health & Readiness** | `GET /health` -> HTTP 200 `{'status': 'ok', 'model_hash_verified': true}` | **VERIFIED** |
| **Inference & Conformal Serving** | `POST /predict` -> HTTP 200, Score: 6.67, Width: 1.1884 | **VERIFIED** |
| **API Documentation** | `GET /docs` -> HTTP 200, `GET /redoc` -> HTTP 200 | **VERIFIED** |
| **Phase Preserved Through** | **12.1** (Evaluation Integrity & Cryptographic Lineage Audit) | **PRESERVED** |
| **Next Planned Phase** | **12.2 — Clean Champion vs Candidate Evaluation** | **IDENTIFIED** |
| **Production Champion** | `phase5_tuned_extra_trees` (`models/phase5_tuned_extra_trees.joblib`) | **ACTIVE** |
| **Champion Modified** | **NO** (Strictly frozen, zero retraining) | **VERIFIED** |
| **Candidate Promoted** | **NO** (Retained as `CHALLENGER / VALIDATING` only) | **VERIFIED** |

---

## 2. Directory Structure of the Migrated Repository

```
student-wellbeing-score-prediction/
├── .github/
│   └── workflows/
│       ├── ci.yml                          # Continuous Integration & Hash Guardrails
│       └── docker-publish.yml              # CD Container Deployment to GHCR
├── app/
│   ├── configuration.py                   # Pydantic v2 Settings
│   ├── explanation_service.py             # TreeSHAP Explainer Service
│   ├── governance.py                      # Registry & Shadow Challenger Engine
│   ├── main.py                            # FastAPI Microservice & Middleware
│   ├── model_service.py                   # Frozen Champion & Conformal Inference
│   ├── monitoring.py                      # Drift Engine (PSI, KS, TVD) & Prometheus
│   └── schemas.py                         # Request/Response Validation Schemas
├── ml/
│   ├── data/                              # Raw survey data (4,998 unique rows)
│   ├── evaluation/                        # Evaluation charts & diagnostics (Phases 3–12)
│   ├── experiments/                       # Experiment metrics, benchmark CSVs, drift references
│   └── notebooks/                         # Preserved lifecycle notebooks (01 through 12.1)
├── models/
│   ├── candidate_v1_2_conformal_calibration.json
│   ├── candidate_v1_2_metadata.json
│   ├── candidate_v1_2_revalidated.joblib  # 128.72 MB Candidate (Tracked via Git LFS)
│   ├── model_registry.json                # Central Model Registry & Shadow Logs
│   ├── phase2_baseline.joblib             # Historical baseline pipeline
│   ├── phase4_candidate.joblib            # Historical candidate pipeline
│   ├── phase5_metadata.json               # Champion metadata
│   ├── phase5_tuned_extra_trees.joblib    # Frozen Production Champion (52.40 MB)
│   └── phase7_1_conformal_calibration.json# 5-fold OOF conformal calibration thresholds
├── reports/                               # Full engineering reports across Phases 1–12.1
├── tests/
│   ├── test_api.py                        # API contract & validation tests (14 tests)
│   ├── test_audit_12_1.py                 # Lineage, hash, & schema regression tests (11 tests)
│   ├── test_governance.py                 # Registry & shadow isolation tests (7 tests)
│   ├── test_monitoring.py                 # PSI/KS/TVD drift tests (11 tests)
│   ├── test_revalidation.py               # Candidate validation tests (6 tests)
│   └── test_smoke_production.py           # Production smoke tests (1 test)
├── .dockerignore
├── .gitattributes                         # Git LFS tracking configuration
├── .gitignore                             # Secret & cache exclusion patterns
├── Dockerfile                             # Production container definition
├── index.html                             # Web frontend interface
├── LICENSE                                # MIT License
├── main.py                                # Entry point delegating to app.main:app
├── pytest.ini                             # Pytest root configuration
├── README.md                              # Portfolio-grade README
├── render.yaml                            # Cloud deployment configuration
├── requirements.txt                       # Production dependency manifest
├── script.js                              # Client logic with SHAP & Interval UI
└── style.css                              # Design system styling
```

---

## 3. Cryptographic Artifact Integrity Verification

Both models and calibration artifacts were verified bit-for-bit using SHA-256 before staging, after committing, and post-push:

```
Artifact: models/phase5_tuned_extra_trees.joblib (54,945,902 bytes)
Expected SHA-256: a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8
Observed SHA-256: a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8
Status: EXACT MATCH

Artifact: models/candidate_v1_2_revalidated.joblib (134,970,570 bytes / 128.72 MB)
Expected SHA-256: aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc
Observed SHA-256: aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc
Status: EXACT MATCH (Uploaded via Git Large File Storage - Git LFS)

Artifact: models/phase7_1_conformal_calibration.json (2,048 bytes)
Expected SHA-256: 22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b
Observed SHA-256: 22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b
Status: EXACT MATCH

Artifact: models/candidate_v1_2_conformal_calibration.json (1,108 bytes)
Expected SHA-256: b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af
Observed SHA-256: b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af
Status: EXACT MATCH
```

---

## 4. Preservation of the Phase 12.1 Contamination Finding

The evaluation integrity findings established in Phase 12.1 are preserved verbatim:
- **Phase 5 Partition:** Train = 3,998 rows, Holdout = 1,000 rows (`random_state=42`).
- **Phase 12 Partition:** Dev = 3,998 rows, Holdout = 1,000 rows (`random_state=1242`).
- **Phase 5 Train $\cap$ Phase 12 Holdout:** **799 rows (79.90%)** -> **CONTAMINATED FOR CHAMPION**.
- **Phase 5 Holdout $\cap$ Phase 12 Holdout:** **201 rows (20.10%)** -> **CLEAN COMMON UNSEEN SUBSET**.
- **Phase 12 Dev $\cap$ Phase 12 Holdout:** **0 rows (0.00%)** -> **CLEAN FOR CANDIDATE**.
- Champion evaluation on the full Phase 12 holdout produced near-perfect memorization ($\text{RMSE} = 0.0064$ on the 799 train rows) and is officially ruled invalid.
- Candidate v1.2 holdout evaluation ($\text{RMSE} = 0.357865, R^2 = 0.922289$) is valid as an out-of-sample candidate estimate, but cannot be directly compared against the Champion on the full holdout.
- **The Champion was NOT modified, Candidate was NOT promoted.**
- **Phase 12.2** is identified as the next planned phase to conduct a strictly symmetric, leakage-free evaluation exclusively on the 201 clean rows.

---

## 5. Security & Secrets Audit Result

- **Audit Result:** **`PASS`**
- No `.env`, `.env.*`, API keys, private certificates (`.pem`, `.key`), cloud tokens, or personal access tokens were present or staged.
- `.gitignore` rigorously blocks virtual environments (`venv/`, `.venv/`), temporary compilation artifacts (`__pycache__/`), test caches (`.pytest_cache/`), scratch scripts (`scratch/`), and model weights not intended for version control.
- Git tracking for legacy `__pycache__/*.pyc` files from early commits was purged.

---

## 6. Test Suite & Health Verification

Execution of `pytest -q`:
```
..................................................                       [100%]
50 passed, 9 warnings in 17.82s
```
- `tests/test_api.py`: 14 passed
- `tests/test_audit_12_1.py`: 11 passed
- `tests/test_governance.py`: 7 passed
- `tests/test_monitoring.py`: 11 passed
- `tests/test_revalidation.py`: 6 passed
- `tests/test_smoke_production.py`: 1 passed

Application Startup & Endpoints (`app.main:app`):
- `GET /health` -> `200 OK` (Model loaded, uncertainty loaded, SHA-256 verified)
- `POST /predict` -> `200 OK` (Estimated Wellbeing Score: 6.67, 90% Prediction Interval: [6.07, 7.26], Width: 1.1884)
- `POST /explain` -> `200 OK` (TreeSHAP feature attributions mapped across 38 features to 12 survey inputs)
- `GET /docs` -> `200 OK` (Swagger OpenAPI schema)
- `GET /redoc` -> `200 OK` (ReDoc schema)

---

## 7. Migration Completion Sign-Off

The repository has been successfully transitioned to its authoritative home:
**`https://github.com/MSIVAPAPARAO13/student-wellbeing-score-prediction`**
All project history, models, tests, deployment workflows, notebooks, and audit findings through Phase 12.1 are fully committed and active on `main`.
