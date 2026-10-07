# Final Project Audit: Student Wellbeing Score Prediction

**Project:** Student Mental Health / Student Wellbeing Score Prediction  
**Repository:** `https://github.com/MSIVAPAPARAO13/student-wellbeing-score-prediction` (`main` branch)  
**Audit Date:** October 7, 2026  
**Final Project State:** **FROZEN / PRODUCTION & RESUME READY**  

---

## 1. Executive Summary

This audit confirms that the **Student Wellbeing Score Prediction** repository has completed all core machine learning, explainability, uncertainty quantification, API productionization, testing, and governance milestones. The project is fully frozen, reproducible, and ready for portfolio presentation.

---

## 2. Final System Architecture

```
[ Web Browser Client ]
        │
        │ HTTP /predict, /explain, /health
        ▼
[ FastAPI Application (app/main.py) ]
 ├── Input Validation (Pydantic v2 schemas)
 ├── Preprocessing Pipeline (ColumnTransformer: log1p, StandardScaler, Ordinal, OneHot)
 ├── Inference Service (models/phase5_tuned_extra_trees.joblib)
 ├── Uncertainty Engine (models/phase7_1_conformal_calibration.json)
 ├── Explainer Service (TreeSHAP Engine: 38 dimensions -> 12 inputs)
 └── Governance & Monitoring (In-memory telemetry, drift engine, shadow runner)
```

---

## 3. Final Model Specifications

- **Production Champion:** `models/phase5_tuned_extra_trees.joblib`
- **Model Family:** `ExtraTreesRegressor(n_estimators=500, max_features='sqrt', random_state=42)`
- **Input Features:** 12 survey inputs transformed into 38 numerical pipeline features
- **Target:** Continuous wellbeing score bounded in $[1.0, 10.0]$
- **Operational Status:** Serving 100% of live traffic via `/predict`

---

## 4. Verified Offline Metrics (Holdout Evaluation)

Evaluated on an independent, quarantined 1,000-sample holdout test partition:

| Metric | Offline Value | Benchmark Standard |
| :--- | :---: | :---: |
| **Coefficient of Determination ($R^2$)** | **0.9275** | $> 0.8500$ |
| **Root Mean Squared Error (RMSE)** | **0.3596** | $< 0.4500$ |
| **Mean Absolute Error (MAE)** | **0.2490** | $< 0.3500$ |
| **5-Fold Cross-Validation $R^2$** | **0.9110 ± 0.0094** | Top performer across 8 models |

*(Real-world production ground truth metrics are truthfully reported as `DATA_NOT_AVAILABLE` pending post-deployment label collection).*

---

## 5. Explainability & Uncertainty Status

- **TreeSHAP Engine:** In-memory `TreeExplainer` computing exact Shapley values. Aggregates 38 encoded column attributions back to the 12 survey inputs and benchmarks against base value $\mathbb{E}[Y] \approx 6.22$.
- **Conformal Uncertainty:** 5-fold cross-conformal (OOF) residual calibration with verified empirical coverage:
  - 80% Tier: Width = $0.8312$, Empirical Coverage = **$84.60\%$**
  - 90% Tier: Width = $1.1884$, Empirical Coverage = **$92.70\%$**
  - 95% Tier: Width = $1.5804$, Empirical Coverage = **$95.80\%$**

---

## 6. API & User Interface Status

- **API Layer:** Fast, asynchronous FastAPI microservice with automated OpenAPI Swagger UI documentation at `/docs`.
- **Latency Performance:** Benchmark $P_{95} < 120\text{ ms}$ (compliant with authoritative SLA $P_{95} < 150\text{ ms}$).
- **Web Interface:** Vanilla HTML5/CSS3/JavaScript client (`index.html`, `style.css`, `script.js`). Fully model-driven with client-side form validation, dynamic score gauge, interval bar visualization, on-demand SHAP factor cards, and non-clinical disclaimer.

---

## 7. Automated Testing Status

- **Pytest Suite (`pytest -q`):** **147 tests passed, 0 failures, 10 warnings** in 72s.
- **Production Smoke Test Suite (`tests/test_smoke_production.py`):** **6 / 6 passed**:
  1. `GET /health` [PASSED]
  2. `POST /predict` [PASSED]
  3. Local Pipeline vs Serving Equivalence [PASSED]
  4. `POST /explain` [PASSED]
  5. `GET /docs` [PASSED]
  6. `GET /governance/shadow/status` [PASSED]

---

## 8. Cryptographic Model Hash Verification

All production model and conformal calibration artifacts were verified bit-for-bit against their authoritative SHA-256 signatures:

| Artifact | File Path | Authoritative SHA-256 | Verification |
| :--- | :--- | :--- | :---: |
| **Production Champion** | `models/phase5_tuned_extra_trees.joblib` | `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8` | **MATCH (INVARIANT)** |
| **Candidate Challenger** | `models/candidate_v1_2_revalidated.joblib` | `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc` | **MATCH (INVARIANT)** |
| **Champion Conformal Calib** | `models/phase7_1_conformal_calibration.json` | `22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b` | **MATCH (INVARIANT)** |
| **Candidate Conformal Calib** | `models/candidate_v1_2_conformal_calibration.json` | `b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af` | **MATCH (INVARIANT)** |

---

## 9. Current Governance State

```
======================================================================
GOVERNANCE STATE: CONTROLLED SHADOW OBSERVATION / WAIT STATE
======================================================================
Champion Model:       phase5_tuned_extra_trees (ACTIVE PRODUCTION)
Candidate Challenger: candidate_v1_2_revalidated (SHADOW / VALIDATING)
Shadow Observation:   ~1.12 / 14 days elapsed (13 calendar days remaining)
Verified Labels:      0 / 100 post-deployment labels collected
Paired Observations:  0 paired rows
Promotion Status:     STRICTLY BLOCKED
Decision:             OPTION C — INSUFFICIENT EVIDENCE
Automatic Retraining: DISABLED
Automatic Promotion:  DISABLED
Human Approval:       REQUIRED (PENDING)
Models Modified:      NONE (0 weights, parameters, or artifacts changed)
Models Retrained:     NONE (Retraining strictly disabled)
======================================================================
```

---

## 10. Known Limitations & Responsible AI

1. **Survey-Conditioned Estimates:** Predictions are conditioned strictly on self-reported inputs subject to recall bias.
2. **Statistical Analytics Only:** Estimates provide educational and lifestyle awareness; they are not psychiatric or medical diagnoses.
3. **No Automatic Self-Retraining:** Retraining loops on post-deployment feedback are disabled to protect against data poisoning and feedback collapse.

---

## 11. Resume-Ready Project Pitch

> *"Built an end-to-end student wellbeing score prediction system using leakage-free preprocessing and a tuned Extra Trees model ($R^2 \approx 0.9275$), with TreeSHAP explainability, conformal prediction intervals ($92.70\%$ empirical coverage at $90\%$ confidence), and an asynchronous FastAPI serving layer with 147 automated tests."*
