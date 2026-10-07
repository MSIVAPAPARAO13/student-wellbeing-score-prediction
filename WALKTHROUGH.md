# Student Wellbeing Score Prediction — Technical Project Walkthrough

**Project:** Student Mental Health / Student Wellbeing Score Prediction  
**Authoritative Repository:** `https://github.com/MSIVAPAPARAO13/student-wellbeing-score-prediction` (`main` branch)  
**Status:** **FROZEN / PRODUCTION & RESUME READY**  

---

## 1. Project Goal & Problem Formulation

### Problem Statement
Student wellbeing is heavily influenced by daily lifestyle factors—including sleep duration, study load, exercise, screen time, and perceived stress. However, practical machine learning systems for wellbeing analytics frequently fail due to three core challenges:
1. **Uncalibrated Point Estimates:** Naked point predictions provide no indication of uncertainty, making it impossible to distinguish between confident and high-variance estimates.
2. **Black-Box Opacity:** Complex non-linear models fail to explain which specific student habits drove an estimate.
3. **Data Leakage & Train-Test Overlap:** Naive preprocessing pipelines often fit transformations across combined data splits, producing artificially optimistic benchmarks.

### Target Variable
The system models a continuous **Student Wellbeing Score** on a bounded scale from $1.0$ to $10.0$ ($\mu \approx 6.22$, $\sigma \approx 1.26$), where higher values correspond to greater self-reported lifestyle balance and lower daily strain.

### Non-Clinical Scope
> **Strict Non-Clinical Scope:**  
> This system is an educational analytics tool for personal lifestyle awareness. It is **not** a diagnostic device, psychiatric assessment, or clinical triage system. Conformal predictive intervals represent mathematical residual bounds, not clinical confidence.

---

## 2. Dataset & Quality Auditing

- **Dataset Source:** Survey of student digital routines, academic schedules, and lifestyle indicators.
- **Initial Size:** 5,000 raw survey records.
- **Cleaning & Deduplication:** Identified and permanently purged 2 exact duplicate rows during Phase 2, establishing an authoritative baseline of **4,998 unique student records**.
- **Features (12 Total Survey Inputs):**
  - **Numerical (6):** `Age`, `Study_Hours`, `Avg_Daily_Usage_Hours`, `Daily_Unlocks`, `Physical_Activity_Hours`, `Sleep_Hours_Per_Night`.
  - **Categorical (5):** `Gender`, `Academic_Level`, `Country` (top 10 preserved; non-top-10 mapped to `'Other'`), `Most_Used_Platform`, `Purpose_Of_Use`.
  - **Ordinal (1):** `Stress_Level` (`Low` < `Medium` < `High` < `Very High`).
- **Target Variable:** `Mental_Health_Score` (served contextually as `estimated_wellbeing_score`).

---

## 3. Leakage-Free Preprocessing & Feature Engineering

To guarantee zero data leakage between training and evaluation partitions:
1. **Partitioning:** An 80/20 train/holdout split was executed before fitting any transformer ($3,998$ training samples / $1,000$ holdout samples).
2. **Pipeline Encapsulation:** All transformers are encapsulated within a scikit-learn `ColumnTransformer`:
   - `Study_Hours`: Log-transformed ($\ln(1 + x)$) to handle right-skew, followed by `StandardScaler`.
   - Continuous numerical features: `StandardScaler` fitted strictly on the training partition.
   - `Stress_Level`: Ordinal encoding (`OrdinalEncoder(categories=[['Low', 'Medium', 'High', 'Very High']])`).
   - Categorical inputs: `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` applied to country, gender, academic level, platform, and purpose.
3. **Multicollinearity Diagnosis:** Variance Inflation Factor (VIF) analysis verified all preprocessed features exhibited $\text{VIF} < 5.0$, confirming no destructive multicollinearity.
4. **Output Dimension:** The 12 survey inputs expand into an encoded 38-dimensional numerical feature space.

---

## 4. Model Selection & Multi-Model Benchmarking

Eight regression algorithms across diverse model families were systematically benchmarked on the 3,998-record training partition using 5-fold cross-validation:

| Model | Family | CV $R^2$ | CV RMSE | CV MAE | Analysis |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Extra Trees** | Randomized Ensembles | **0.9110 ± 0.0094** | **0.3986** | **0.3105** | **Top Performer: Best variance reduction on tabular splits** |
| Random Forest | Bagged Ensembles | 0.8648 ± 0.0078 | 0.4902 | 0.3802 | Strong baseline, but higher variance than Extra Trees |
| XGBoost | Gradient Boosting | 0.8629 ± 0.0084 | 0.4952 | 0.3854 | Competitive boosting model |
| HistGradientBoosting | Gradient Boosting | 0.8542 ± 0.0091 | 0.4902 | 0.3727 | Fast histogram boosting |
| LightGBM | Gradient Boosting | 0.8392 ± 0.0060 | 0.5060 | 0.3883 | Fastest training, but slight under-fitting |
| CatBoost | Gradient Boosting | 0.8347 ± 0.0049 | 0.5131 | 0.3945 | Under-fitted with default depth |
| ElasticNet / Ridge | Regularized Linear | 0.4357 ± 0.0120 | 0.9501 | 0.7485 | Incapable of capturing non-linear interactions |
| Linear Regression | Ordinary Least Squares| 0.4356 ± 0.0121 | 0.9502 | 0.7486 | Severe underfitting |

**Why Extra Trees Won:**  
By drawing random split thresholds for candidate features rather than optimizing each split, `ExtraTreesRegressor` achieves superior variance reduction on tabular data compared to standard Random Forest and default gradient boosters.

---

## 5. Hyperparameter Tuning & Frozen Champion

- **Tuning Strategy:** Exhaustive grid search over estimators, tree depth, and feature subset sizes.
- **Selected Architecture:** `ExtraTreesRegressor(n_estimators=500, max_features='sqrt', random_state=42)`.
- **Holdout Evaluation (Independent 1,000 Records):**
  - **$R^2 = 0.9275$**
  - **$\text{RMSE} = 0.3596$**
  - **$\text{MAE} = 0.2490$**
- **Champion Freezing:** The resulting model pipeline was serialized to `models/phase5_tuned_extra_trees.joblib` and locked with an authoritative SHA-256 fingerprint:
  `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8`

---

## 6. Interpretability with TreeSHAP

To explain individual predictions in real time:
- **TreeExplainer Integration:** Leverages the decision-tree structure of the 500-tree ensemble to compute exact Shapley values in polynomial time ($O(T \cdot L \cdot D^2)$) rather than sampling exponentially.
- **Feature Aggregation:** An attribution engine (`app/explanation_service.py`) automatically maps the 38 encoded column Shapley values back to the **12 intuitive survey inputs**.
- **Dynamic Expected Value:** Benchmarks individual inferences against the dataset expected score ($\mathbb{E}[Y] \approx 6.22$).
- **Bidirectional Insight:** Distinguishes positive drivers (e.g. adequate sleep, regular physical activity) from negative drivers (e.g. high stress, excessive screen unlocks).

---

## 7. Distribution-Free Uncertainty (Conformal Prediction)

Standard regression models output single numbers without reliability bounds. This system implements **5-fold cross-conformal (OOF) residual calibration**:

$$\hat{C}(x) = [\hat{y} - q_{1-\alpha}, \; \hat{y} + q_{1-\alpha}]$$

Using 3,998 out-of-fold calibration residuals:
- **80% Nominal Target:** $q_{80} = 0.4156 \implies \text{Mean Width} = 0.8312$, Empirical Coverage: **$84.60\%$**
- **90% Nominal Target:** $q_{90} = 0.5942 \implies \text{Mean Width} = 1.1884$, Empirical Coverage: **$92.70\%$**
- **95% Nominal Target:** $q_{95} = 0.7902 \implies \text{Mean Width} = 1.5804$, Empirical Coverage: **$95.80\%$**

Conformal intervals provide distribution-free, finite-sample coverage guarantees without assuming Gaussian residuals, executing in $< 1\ \mu\text{s}$.

---

## 8. FastAPI Serving & Architecture

The production serving layer is implemented as an asynchronous FastAPI microservice (`app/main.py`):

```
                   [ User Web Client / Frontend ]
                                │
                                │ HTTP POST /predict, POST /explain, GET /health
                                ▼
                      [ FastAPI Application ]
                      (app/main.py, lifespan)
                                │
     ┌──────────────────────────┼──────────────────────────┐
     ▼                          ▼                          ▼
[ ModelService ]       [ ExplanationService ]      [ Governance & Telemetry ]
• Verifies SHA-256     • TreeExplainer Engine      • Prometheus Telemetry
• Champion Pipeline    • 38 Transformed Features   • Drift Engine (PSI/KS)
• Conformal Quantiles    mapped to 12 inputs       • Isolated Shadow Runner
     │                          │                          │
     ▼                          ▼                          ▼
Point Prediction       Signed Feature              Candidate Shadow Scoring
+ Prediction Interval   Attributions               (Zero client interference)
     │                          │                          │
     └──────────────────────────┼──────────────────────────┘
                                ▼
                   [ JSON Response to Client ]
```

### Key Endpoints:
- `GET /health`: Health probe verifying model loading, conformal calibration, and SHA-256 fingerprint.
- `POST /predict`: Computes estimated score and calibrated prediction interval.
- `POST /explain`: Computes SHAP base value and top positive/negative feature contributions.
- `GET /docs`: Interactive OpenAPI Swagger UI documentation.
- `GET /governance/shadow/status`: Shadow observation telemetry and readiness state.

---

## 9. Web User Interface

The application includes an interactive client (`index.html`, `style.css`, `script.js`):
1. **Personal & Lifestyle Inputs:** Organized into clean fieldsets with client-side validation.
2. **Model-Driven Score Display:** Renders the estimated wellbeing score directly from the API response.
3. **Calibrated Interval Bar:** Visualizes the dynamic uncertainty bounds (e.g. $[6.07, 7.26]$ at 90% confidence).
4. **On-Demand SHAP Explanations:** Allows the user to click "Explain Prediction" to view individual positive and negative lifestyle drivers.
5. **Responsible AI Notice:** Persistent disclaimer communicating statistical estimation boundaries.

---

## 10. Automated Testing & Verification

The test suite covers full regression, data validation, conformal coverage, and shadow governance:

- **Pytest Suite (`pytest -q`):** **147 tests passed, 0 failures**.
- **Live Production Smoke Checks (`tests/test_smoke_production.py`):** **6 / 6 passed**:
  1. `GET /health` [PASSED]
  2. `POST /predict` [PASSED]
  3. Local Pipeline vs Serving Equivalence [PASSED]
  4. `POST /explain` [PASSED]
  5. `GET /docs` [PASSED]
  6. `GET /governance/shadow/status` [PASSED]

---

## 11. Current Governance State & Real-World Validation

To prevent unverified model changes, the repository enforces strict governance:

- **Production Champion:** `models/phase5_tuned_extra_trees.joblib` (**ACTIVE PRODUCTION**)
- **Candidate Challenger:** `models/candidate_v1_2_revalidated.joblib` (**SHADOW / VALIDATING**)
- **Shadow Isolation:** Candidate scoring runs out-of-band; exceptions or timeouts have strictly zero impact on user responses.
- **Historical Data Firewall:** 4,998 offline records are quarantined from production evaluation.
- **Real-World Evidence Status:**
  - Shadow observation: $\approx 1.12$ days of 14 required ($13$ calendar days remaining).
  - Verified post-deployment labels: $0 / 100$.
  - Paired observations: $0$.
  - Production metrics: `DATA_NOT_AVAILABLE` (truthfully reported without fabrication).
- **Promotion Status:** **STRICTLY BLOCKED** (Decision: **OPTION C — INSUFFICIENT EVIDENCE**).
- **Human Approval:** **REQUIRED (PENDING)**.
- **Automatic Retraining & Promotion:** **DISABLED**.

---

## 12. 60-Second Interview Summary

> *"I developed an end-to-end Student Wellbeing Score Prediction system designed to demonstrate production-quality ML engineering: leakage-free preprocessing, uncertainty quantification, explainability, and rigorous governance.  
> 
> We benchmarked eight regressors on 4,998 student records and tuned an Extra Trees ensemble achieving an offline holdout $R^2$ of $0.9275$. Instead of outputting uncalibrated point estimates, we implemented 5-fold cross-conformal residual calibration to provide distribution-free prediction intervals with a guaranteed 90% coverage rate, paired with TreeSHAP for local feature attribution.  
> 
> On the serving side, the model is deployed via FastAPI with sub-120ms latency and an interactive web interface. To protect serving reliability, challenger models are evaluated in isolated shadow mode with zero user interference, requiring 14 days of live observation and 100 verified post-deployment labels before human sign-off can unlock promotion."*
