# Student Wellbeing Score Prediction — Project Walkthrough

---

## 1. Project Goal

### Problem Statement
Modern students navigate demanding academic schedules alongside ubiquitous digital connectivity and social media usage. While extreme screen time, disrupted sleep, and high stress correlate with diminished subjective wellbeing, off-the-shelf machine learning solutions often suffer from three major shortcomings:
1. **Uncalibrated Predictions:** Point predictions lack rigorous confidence bounds, leaving decision-makers blind to prediction uncertainty.
2. **Black-Box Opacity:** Complex models fail to articulate which specific student habits drove an estimate.
3. **Flawed Governance & Leakage:** Prototypes often suffer from silent train-test contamination, automatic model deployment regressions, or clinical scope creep.

### Target Variable
The system estimates a continuous **Student Wellbeing Score** on a bounded scale from $1.0$ to $10.0$ (mean $\approx 6.22$, standard deviation $\approx 1.26$), where higher values correspond to greater self-reported lifestyle balance and lower perceived daily strain.

### Non-Clinical Scope
> [!IMPORTANT]
> **Strict Non-Clinical Scope:**  
> This application is an educational and behavioral lifestyle analytics platform. It **does not** diagnose depression, anxiety, psychiatric illnesses, or clinical conditions. It does not output medical risk categories, and its predictive intervals represent mathematical conformal residual bounds—never clinical diagnostic confidence.

---

## 2. Dataset

- **Source:** Survey of student digital routines, academic schedules, and lifestyle indicators.
- **Initial Volume:** 5,000 raw survey responses.
- **Cleaning & Deduplication:** Identified and permanently purged 2 exact duplicate rows in Phase 2, establishing an authoritative clean baseline of **4,998 unique student records**.
- **Features (12 Total Survey Inputs):**
  - **Numerical (6):** `Age`, `Study_Hours`, `Avg_Daily_Usage_Hours`, `Daily_Unlocks`, `Physical_Activity_Hours`, `Sleep_Hours_Per_Night`.
  - **Categorical (5):** `Gender`, `Academic_Level`, `Country` (top 10 preserved: Australia, Canada, France, Germany, India, Mexico, Other, Turkey, UK, USA; non-top-10 mapped to 'Other'), `Most_Used_Platform`, `Purpose_Of_Use`.
  - **Ordinal (1):** `Stress_Level` (`Low` < `Medium` < `High` < `Very High`).
- **Target:** `Mental_Health_Score` (renamed contextually in serving as `estimated_wellbeing_score`).

---

## 3. ML Lifecycle (Phase-by-Phase)

| Phase | Title | Core Contribution & Key Metric |
| :--- | :--- | :--- |
| **Phase 1** | Problem Formulation & EDA | Distribution analysis, target characterization ($N=5,000$, $\mu=6.22$). |
| **Phase 2** | Cleaning & Leakage-Free Partitioning | Removed 2 duplicates ($N=4,998$); executed isolated 80/20 train/holdout split ($3,998$ train / $1,000$ holdout). |
| **Phase 3** | Feature Engineering & Multicollinearity | Log-transform on skewed study hours, VIF analysis ($<5.0$), preprocessing pipeline freezing. |
| **Phase 4** | Multi-Model Benchmarking | Evaluated 8 algorithms (Linear, ElasticNet, RF, GBDT, XGBoost, LightGBM, CatBoost, Extra Trees). Extra Trees achieved lowest CV RMSE. |
| **Phase 5** | Hyperparameter Optimization & Champion Freezing | Optuna-tuned `ExtraTreesRegressor` (500 trees) frozen as production Champion ($R^2 = 0.9275$, $\text{RMSE} = 0.3596$). |
| **Phase 6** | TreeSHAP Explainability Engine | Precalculated TreeExplainer mapping 38 preprocessed pipeline dimensions back to 12 original survey inputs. |
| **Phase 7 / 7.1** | Distribution-Free Conformal Uncertainty | 5-Fold Cross-Conformal / Out-Of-Fold Residual Calibration yielding valid empirical coverage ($92.70\%$ coverage at $90\%$ nominal target; $q_{90} = 0.5942$, mean width $1.1884$). |
| **Phase 8** | Enterprise FastAPI Productionization | Production async endpoints (`/predict`, `/explain`, `/health`, `/metrics`), Pydantic v2 schemas, in-memory Prometheus observability. |
| **Phase 9** | Cloud Deployment & Containerization | Multi-stage Docker containerization, GHCR package publishing, automated cloud hosting configuration. |
| **Phase 10** | Continuous Production Monitoring | Automated drift monitoring without PII storage: Population Stability Index (PSI), Kolmogorov-Smirnov (KS), Total Variation Distance (TVD). |
| **Phase 11** | Model Governance & Shadow Serving | Central Model Registry (`models/model_registry.json`), lifecycle states, isolated shadow serving, anti-auto-retraining policies. |
| **Phase 12** | Controlled Model Improvement | Trained Candidate v1.2 (`RandomForestRegressor`) on new records; generated initial validation metrics. |
| **Phase 12.1** | Evaluation Integrity Audit | **Discovered 79.9% holdout overlap** between Phase 12 holdout and historical Phase 5 training data; blocked flawed candidate promotion. |
| **Phase 12.2** | Clean Head-to-Head Evaluation | Symmetrically evaluated Champion vs. Candidate on the clean, unseen 201-row dataset. Demonstrated Candidate is statistically non-superior. |
| **Phase 12.3** | Candidate Validation Gate | Formally blocked Candidate promotion; approved Candidate exclusively for non-interfering shadow observation. |
| **Phase 13** | Real-World Shadow Observation | **ACTIVE / IN PROGRESS:** 14-day shadow window and 100 verified production label requirements enforced. Promotion BLOCKED. |
| **Phase 13A** | Model-Driven UI Integrity Hardening | Removed hardcoded sample inputs and static score categories. Guaranteed frontend is 100% driven by live API responses. |

---

## 4. Current Production Architecture

```
               [ User Web Browser (Vanilla HTML/CSS/JS) ]
                                    │
                                    │ HTTP POST /predict, POST /explain, GET /health
                                    ▼
                          [ FastAPI Application ]
                          (app/main.py, lifespan)
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
[ ModelService ]          [ ExplanationService ]      [ Governance & Monitoring ]
• Verifies SHA-256        • TreeExplainer             • Prometheus Telemetry
• Champion Pipeline       • 38 Transformed Features   • Feature Drift (PSI/KS)
• Conformal Calibration     mapped to 12 inputs       • Isolated Shadow Runner
  (Phase 7.1 OOF)         • Dynamic base value E[Y]   • Registry Gatekeeper
         │                          │                          │
         ▼                          ▼                          ▼
  Point Prediction           Signed Feature            Challenger Shadow Run
 + Conformal Interval         Attributions             (Zero user interference)
         │                          │                          │
         └──────────────────────────┼──────────────────────────┘
                                    ▼
                [ JSON Response to User Interface / Client ]
```

---

## 5. How Prediction Works

1. **User Submission:** The user submits values for all 12 survey fields.
2. **Input Validation:** Pydantic v2 schemas enforce data types, numerical boundaries (e.g., $Age \in [10, 100]$, hours $\in [0, 24]$), and categorical membership.
3. **Data Preprocessing:**
   - Country is cleaned and grouped (top 10 preserved; others mapped to `"Other"`).
   - Numerical inputs are standardized via `StandardScaler`.
   - `Study_Hours` is log-transformed ($\ln(1 + x)$).
   - Categorical inputs are one-hot encoded (`OneHotEncoder`).
   - `Stress_Level` is ordinally encoded.
4. **Ensemble Point Prediction:** The preprocessed 38-feature vector traverses all 500 trees in the frozen `ExtraTreesRegressor`.
5. **Calibrated Conformal Interval:**
   - The selected nominal coverage level (e.g., 90%) retrieves the calibrated quantile threshold $q_{90} = 0.5942$ from `models/phase7_1_conformal_calibration.json`.
   - Bounds are constructed as $[\hat{y} - q_{90}, \hat{y} + q_{90}]$.
   - Fixed width $= 2 \times q_{90} = 1.1884$.

---

## 6. How Explainability Works

- **TreeSHAP Implementation:** Uses `shap.TreeExplainer` initialized directly on the production Extra Trees ensemble.
- **Dynamic Expected Value ($E[Y]$):** The population base value is derived directly at startup from `TreeExplainer.expected_value` ($\approx 6.22$).
- **Attribution Aggregation:** The 38 encoded column SHAP contributions are aggregated back to the 12 intuitive survey features.
- **Directional Categorization:**
  - Positive contributors ($\text{SHAP} > +0.005$): habits associated with higher wellbeing scores.
  - Negative contributors ($\text{SHAP} < -0.005$): habits associated with lower wellbeing scores.
  - Neutral contributors ($|\text{SHAP}| \le 0.005$): minimal estimated impact.

---

## 7. How Governance Works

1. **Cryptographic Verification:** Every model load verifies SHA-256 hashes against immutable release records.
2. **No Automatic Retraining:** Retraining triggers require human governance authorization to avoid data poisoning or degradation.
3. **No Automatic Promotion:** Promotion requires meeting sample size thresholds ($\ge 100$ verified production labels), passing conformal coverage floors ($\ge 85\%$), completing a 14-day shadow window, and securing explicit human approval.
4. **Failure Isolation:** Candidate challenger models evaluate shadow traffic asynchronously. If the challenger errors or times out, the user's prediction response from the Champion is unaffected.

---

## 8. Phase 13 Status

- **Status:** **ACTIVE / IN PROGRESS** (Phase 14 has **NOT** been started).
- **Champion:** `phase5_tuned_extra_trees` (Active in Production).
- **Candidate:** `candidate_v1_2_revalidated` (Shadow / Validating only).
- **Shadow Duration Requirement:** 14 consecutive calendar days.
- **Verified Label Requirement:** 100 verified post-deployment labels.
- **Current Observation Metrics:**
  - Shadow days completed: **0 / 14**
  - Verified production labels: **0 / 100**
  - Promotion status: **STRICTLY BLOCKED**

---

## 9. Phase 13A — Model-Driven UI Hardening

Phase 13A hardened the web interface into a strictly model-driven client:
1. **Removed Benchmark Loader:** Eliminated all hardcoded demo sample buttons and pre-filled survey records.
2. **Removed Client Categorization:** Deleted all arbitrary score classification rules (`Low`, `Moderate`, `High`, `Balanced Baseline`, etc.). The UI displays only the continuous point score and conformal interval.
3. **Dynamic Model Metadata:** Model version, uncertainty methodology, and disclaimers are populated dynamically from `/health` and `/predict`.
4. **Dynamic TreeSHAP Attribution:** Renders real feature names, values, SHAP impact values, and baseline values from `/explain`.
5. **No Fallback Predictions:** API validation rejections ($422$) or server errors clear previous results and present genuine error notices.

---

## 10. How to Run Locally

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Modern web browser

### Execution Steps
```bash
# 1. Clone repository
git clone https://github.com/MSIVAPAPARAO13/student-wellbeing-score-prediction.git
cd student-wellbeing-score-prediction

# 2. Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch FastAPI application
python main.py
```

### Access URLs
- **Web UI:** [http://127.0.0.1:8000/ui](http://127.0.0.1:8000/ui)
- **API Documentation (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Service Health:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Shadow Status:** [http://127.0.0.1:8000/governance/shadow/status](http://127.0.0.1:8000/governance/shadow/status)
- **Prometheus Metrics:** [http://127.0.0.1:8000/metrics](http://127.0.0.1:8000/metrics)

---

## 11. Live Demonstration Walkthrough

Follow these steps during an interview or live system demonstration:

1. **Step 1: Open the UI:** Navigate to [http://127.0.0.1:8000/ui](http://127.0.0.1:8000/ui). Observe the connection pill confirming connection and model status from `GET /health`.
2. **Step 2: Enter Profile 1 (Balanced Habits):**
   - Age: 20, Gender: Female, Level: Undergraduate, Country: USA
   - Screen Time: 2.0 hrs, Platform: LinkedIn, Unlocks: 45
   - Study: 6.0 hrs, Physical Activity: 3.0 hrs, Sleep: 8.5 hrs, Stress: Low, Purpose: Education
3. **Step 3: Click "Estimate Wellbeing Score":**
   - The UI sends `POST /predict`.
   - Observe the returned continuous score (e.g., ~8.0 / 10).
   - Observe the 90% prediction interval and dynamic metadata fields.
4. **Step 4: Click "Explain this prediction":**
   - The UI sends `POST /explain`.
   - Observe TreeSHAP attributions: Sleep and physical activity appear as top positive contributors.
5. **Step 5: Change Inputs to Profile 2 (High Screen Time & Strain):**
   - Screen Time: 10.0 hrs, Unlocks: 250, Sleep: 4.0 hrs, Physical Activity: 0.0 hrs, Stress: Very High
6. **Step 6: Click "Estimate Wellbeing Score" Again:**
   - Observe the new predicted score drop significantly (e.g., ~5.0 / 10).
7. **Step 7: Re-run Explanation:**
   - TreeSHAP immediately recalculates: Screen time, unlocks, and stress shift into the top negative contributors.
8. **Step 8: Check Governance & Observability:**
   - Open [http://127.0.0.1:8000/governance/shadow/status](http://127.0.0.1:8000/governance/shadow/status) to verify that shadow evaluations were recorded in the background with zero impact on user latency.

---

## 12. API Walkthrough

### Example Request (`POST /predict`)
```json
{
  "Age": 21,
  "Gender": "Female",
  "Academic_Level": "Undergraduate",
  "Country": "India",
  "Avg_Daily_Usage_Hours": 4.5,
  "Most_Used_Platform": "Instagram",
  "Daily_Unlocks": 140,
  "Sleep_Hours_Per_Night": 7.0,
  "Study_Hours": 3.0,
  "Physical_Activity_Hours": 1.5,
  "Stress_Level": "Medium",
  "Purpose_Of_Use": "Education",
  "coverage": 0.90
}
```

### Example Response Structure
*(Note: Actual values are generated at request time by the loaded Champion Extra Trees model and conformal calibration engine)*
```json
{
  "estimated_wellbeing_score": 6.67,
  "prediction_interval": {
    "nominal_coverage": 0.9,
    "lower": 6.07,
    "upper": 7.26,
    "width": 1.1884
  },
  "model_version": "phase5_tuned_extra_trees",
  "uncertainty_method": "5-Fold Cross-Conformal / Out-Of-Fold Residual Calibration",
  "disclaimer": "This is a survey-based wellbeing score estimate and predictive uncertainty interval, not a clinical assessment or medical diagnosis."
}
```

---

## 13. Automated Testing

Run the test suite:
```bash
pytest -q
```

### Current Test Suite Status
- **104 passed, 0 failed, 10 warnings in ~53s**
- **Test Categories:**
  - `test_api.py` (14 tests): Routing, schema validation, 422 error handlers, conformal intervals.
  - `test_audit_12_1.py` (11 tests): Partition cryptographic hashes, holdout contamination rates, schema invariance.
  - `test_phase12_2_clean_evaluation.py` (14 tests): Symmetric evaluation on the 201 unseen holdout.
  - `test_phase12_3_validation_gate.py` (14 tests): Artifact hashes, calibration linkage, shadow readiness.
  - `test_phase13_real_world_validation.py` (15 tests): Shadow isolation, unverified label rejection, promotion blocks.
  - `test_phase13a_ui_integrity.py` (11 tests): Model-driven UI integrity, metadata consistency, country grouping, multi-profile divergence.
  - `test_governance.py` (11 tests): Model registry, shadow engine, anti-auto-retraining policies.
  - `test_monitoring.py` (11 tests): PSI, KS, TVD statistical drift calculation.
  - `test_revalidation.py` (5 tests): Candidate v1.2 behavior, interval monotonicity.
  - `test_smoke_production.py` (1 test): Live server probe and artifact-derived width validation.

---

## 14. Responsible AI & Ethical Guardrails

1. **Non-Diagnostic Nature:** The output is an empirical lifestyle score, not a medical or psychological diagnosis.
2. **No Causal Inferences:** Attributions reflect mathematical associations within the trained model, not proven causal drivers.
3. **Uncertainty Communication:** Conformal intervals clearly bound the model's prediction variance under finite-sample guarantees.
4. **Data Privacy:** Telemetry and monitoring are strictly in-memory and aggregate; no student PII or raw survey responses are retained.

---

## 15. Current Project Status

- **Champion Model:** `models/phase5_tuned_extra_trees.joblib` (**ACTIVE PRODUCTION**)
  - SHA-256: `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8`
- **Candidate Model:** `models/candidate_v1_2_revalidated.joblib` (**SHADOW / VALIDATING**)
  - SHA-256: `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc`
- **Phase 13:** **ACTIVE / IN PROGRESS** (0 / 14 shadow days, 0 / 100 verified labels)
- **Phase 14:** **NOT STARTED**
- **Candidate Promotion:** **STRICTLY BLOCKED**

---

## 16. 60-Second Interview Explanation

> *"I engineered an end-to-end Student Wellbeing Score Prediction system that goes beyond standard model training to address real-world ML engineering challenges: uncertainty quantification, explainability, and rigorous governance.  
> 
> We benchmarked eight regressors on 4,998 unique student records and selected an Extra Trees ensemble achieving an $R^2$ of $0.9275$. Instead of delivering naked point estimates, we implemented 5-fold cross-conformal residual calibration to provide distribution-free prediction intervals with a guaranteed 90% coverage rate, paired with TreeSHAP for feature attribution.  
> 
> Crucially, when evaluating an upgraded candidate model in Phase 12, our Phase 12.1 audit caught a 79.9% holdout data overlap that would have caused an invalid promotion. We enforced strict governance: the candidate was isolated into shadow serving, requiring a 14-day observation window and 100 verified post-deployment labels before human sign-off. In Phase 13A, we hardened the UI so that every score, interval, and SHAP attribution is 100% dynamically driven by our FastAPI service."*

---

## 17. Interview Deep-Dive Questions & Answers

### 1. Why Extra Trees over Random Forest or Gradient Boosting?
In our Phase 4 multi-model benchmarking across 8 algorithms, Extra Trees Regressor demonstrated superior generalization ($R^2 = 0.9275$, $\text{RMSE} = 0.3596$) compared to standard Random Forest ($R^2 = 0.9168$) and XGBoost ($R^2 = 0.9082$). By drawing random thresholds for each candidate feature rather than searching for the strictly optimal split, Extra Trees introduces additional variance reduction that proved effective on our 12-dimensional tabular feature space.

### 2. Why Conformal Prediction instead of standard standard-deviation confidence intervals?
Standard Gaussian confidence intervals ($\hat{y} \pm 1.96 \hat{\sigma}$) assume normal residual distributions and asymptotic guarantees that often fail on finite tabular datasets. Conformal prediction is distribution-free: it leverages out-of-fold calibration residuals to compute non-parametric empirical quantiles ($q_{90} = 0.5942$), mathematically guaranteeing finite-sample coverage ($\ge 90\%$) without assuming normality.

### 3. Why TreeSHAP instead of KernelSHAP or Permutation Importance?
KernelSHAP is model-agnostic but computationally prohibitive for live production requests ($O(M \cdot 2^{|F|})$ sampling). TreeSHAP leverages the internal decision tree graph structure of Extra Trees to compute exact Shapley values in polynomial time ($O(T \cdot L \cdot D^2)$), enabling local attributions in ~1.5s for 500 trees.

### 4. How did you prevent data leakage during preprocessing?
All feature transformers—including `StandardScaler` parameters ($\mu, \sigma$) and `OneHotEncoder` categories—were fitted strictly on training partitions within an encapsulated scikit-learn `Pipeline`. Transformed artifacts were never fitted on combined data.

### 5. Why was the initial Phase 12 Candidate vs. Champion comparison invalid?
In Phase 12, a 1,000-row holdout dataset was used to evaluate Candidate v1.2 against the Champion. Our Phase 12.1 evaluation integrity audit checked the record lineage and discovered that 799 of those 1,000 records (79.9%) were present in the historical Phase 5 training set used to fit the Champion. Evaluating the Champion on data it had trained on constituted train-test leakage.

### 6. How did you fix evaluation integrity in Phase 12.2?
We programmatically computed cryptographic row hashes across the entire dataset to isolate the exact 201 records that were provably unseen by *both* the Champion (trained on 3,998 Phase 5 rows) and the Candidate (developed on 4,797 rows). Symmetrically evaluating both models on this clean 201-row holdout revealed that Candidate v1.2 showed no statistically significant superiority, rightfully blocking promotion.

### 7. Why shadow the candidate rather than running an immediate A/B test?
In educational and wellbeing settings, returning unvalidated challenger predictions directly to users risks exposing them to degraded predictions. Shadow serving routes production traffic to the Candidate asynchronously in memory: user responses receive predictions solely from the proven Champion, while challenger telemetry and latency percentiles are tracked safely.

### 8. Why is automatic model retraining disabled?
Automated self-retraining loops on unverified post-deployment feedback create severe risks of model drift, feedback poisoning, and representation collapse. Governance rules mandate that incoming feedback must be verified, held to sample-size floors, and reviewed by human stakeholders before any retraining pipeline can be triggered.

### 9. What happens if Candidate v1.2 fails shadow validation?
The Model Registry manager immediately marks Candidate v1.2 as `REJECTED`. The Champion continues serving 100% of production traffic without disruption. A post-mortem report is compiled documenting why the challenger failed, preserving full audit history.

### 10. What occurs when a Champion model is eventually replaced?
When a candidate completes all shadow days, verified label quotas, and human sign-off, the registry initiates an atomic champion transition: the current Champion is archived with status `RETIRED`, the approved challenger becomes `CHAMPION`, and its cryptographic hash and conformal calibration artifact become the new runtime baseline.
