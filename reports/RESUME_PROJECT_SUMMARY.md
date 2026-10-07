# Resume Project Summary: Student Wellbeing Score Prediction

**Project Name:** Student Wellbeing Score Prediction  
**Repository:** `https://github.com/MSIVAPAPARAO13/student-wellbeing-score-prediction`  
**Authoritative Language & Stack:** Python 3.13, scikit-learn, FastAPI, TreeSHAP, MAPIE / Conformal Prediction, Pydantic v2, HTML5/CSS3/Vanilla JS  

---

## 1. Problem Statement
Students navigate heavy academic workloads alongside high daily screen time and digital distractions. While digital habits, sleep deprivation, and stress correlate with diminished wellbeing, typical ML prototypes deliver uncalibrated point estimates, black-box predictions, and suffer from train-test data leakage. This project builds a reliable, interpretable, and uncertainty-aware prediction platform for personal wellbeing score estimation.

---

## 2. Technical Approach
- **Data Deduplication & Preprocessing:** Cleaned 5,000 raw survey records, eliminating exact duplicates to reach 4,998 unique records. Designed an isolated `ColumnTransformer` (log-transforms, standard scalers, ordinal encoding, one-hot encoding) fitted strictly on training data to ensure zero leakage.
- **Multicollinearity Screening:** Verified that all 38 transformed features exhibited a Variance Inflation Factor (VIF) below 5.0.
- **Multi-Model Benchmarking:** Systematically evaluated 8 regressors across linear, regularized, bagged, and boosting families using 5-fold cross-validation.
- **Explainability & Uncertainty:** Integrated TreeSHAP for bidirectional feature attributions and 5-fold cross-conformal calibration for distribution-free prediction intervals.
- **Microservice & Client:** Served via asynchronous FastAPI endpoints with input validation schemas and an interactive client interface.

---

## 3. Machine Learning Model
- **Selected Architecture:** `ExtraTreesRegressor(n_estimators=500, max_features='sqrt', random_state=42)`.
- **Selection Rationale:** Superior variance reduction on tabular survey splits through randomized split thresholds, outperforming standard Random Forest and gradient boosters.
- **Status:** Serialized and frozen at `models/phase5_tuned_extra_trees.joblib` with cryptographic SHA-256 fingerprint verification (`a012e7a1...`).

---

## 4. Verified Results (Holdout Evaluation)
*Evaluated on an independent, quarantined 1,000-sample holdout test partition:*
- **Coefficient of Determination ($R^2$):** **0.9275**
- **Root Mean Squared Error (RMSE):** **0.3596**
- **Mean Absolute Error (MAE):** **0.2490**
- **5-Fold Cross-Validation $R^2$:** **0.9110 ± 0.0094**

*(Note: Live production metrics are classified as `DATA_NOT_AVAILABLE` pending real-world label accumulation during shadow observation).*

---

## 5. Explainability (TreeSHAP)
- Leverages decision-tree graph structure to compute exact Shapley values in polynomial time ($O(T \cdot L \cdot D^2)$).
- Aggregation engine maps 38 encoded feature dimensions back to the **12 intuitive survey inputs**.
- Compares individual inferences against the dataset expected score ($\mathbb{E}[Y] \approx 6.22$), returning ranked positive and negative lifestyle drivers.

---

## 6. Uncertainty Estimation (Conformal Prediction)
- Employs **5-fold cross-conformal (OOF) residual calibration** across 3,998 calibration residuals.
- **Coverage Tiers & Empirical Holdout Performance:**
  - **80% Nominal Target:** Mean Width = 0.8312, Empirical Coverage = **84.60%**
  - **90% Nominal Target:** Mean Width = 1.1884, Empirical Coverage = **92.70%**
  - **95% Nominal Target:** Mean Width = 1.5804, Empirical Coverage = **95.80%**
- Computes non-parametric prediction intervals in $< 1\ \mu\text{s}$ without assuming Gaussian error distributions.

---

## 7. API Architecture
- **Framework:** FastAPI with asynchronous endpoints and Pydantic v2 schemas.
- **Endpoints:**
  - `GET /health`: Health probe verifying model load status, conformal engine, and SHA-256 integrity.
  - `POST /predict`: Generates point estimate and calibrated prediction interval.
  - `POST /explain`: Computes TreeSHAP base value and top lifestyle contributors.
  - `GET /docs`: OpenAPI Swagger UI documentation.
  - `GET /governance/shadow/status`: Dynamic shadow observation telemetry.

---

## 8. User Interface
- Lightweight, accessible, model-driven web client (`index.html`, `style.css`, `script.js`).
- Structured input form, score display gauge, interval visualization bar, and on-demand SHAP explanations.
- Persistent non-clinical disclaimer communicating that estimates are statistical approximations.

---

## 9. Automated Testing
- **Pytest Suite:** **147 unit and integration tests passing** (`pytest -q`).
- **Production Smoke Tests:** **6 / 6 checks passing** against live server (`/health`, `/predict`, local-serving equivalence, `/explain`, `/docs`, `/governance/shadow/status`).
- **Integrity Testing:** Automated SHA-256 cryptographic verification of all model and calibration artifacts.

---

## 10. Engineering Highlights
- **Zero Data Leakage:** Preprocessing transformations fitted strictly on training data within an encapsulated scikit-learn pipeline.
- **Model Registry & Isolated Shadow Evaluation:** Challenger models evaluate in defensive shadow execution without affecting user responses.
- **Defensive Safeguards:** Automatic model retraining and automatic promotion are strictly disabled by policy; human governance approval is mandatory.
- **Privacy-Preserving Telemetry:** Telemetry and drift monitoring (PSI, KS, TVD) operate in memory with zero storage of student PII.

---

## 11. Current Limitations
- Estimates are conditioned on self-reported survey inputs subject to recall bias.
- System provides statistical estimation, not psychiatric diagnosis or clinical risk triage.
- Real-world production accuracy awaits post-deployment label collection.

---

## 12. Resume-Ready Descriptions

### Option A: Standard Bullet Points (for Resume Experience / Projects)
- **Student Wellbeing Score Prediction Platform | Python, scikit-learn, FastAPI, SHAP, Conformal Prediction**
  - Engineered an end-to-end ML regression system on 4,998 survey records, tuning an Extra Trees ensemble that achieved holdout $R^2 = 0.9275$, $\text{RMSE} = 0.3596$, and $\text{MAE} = 0.2490$.
  - Implemented 5-fold cross-conformal residual calibration, delivering distribution-free prediction intervals with guaranteed 90% empirical coverage ($92.70\%$ observed) in $< 1\ \mu\text{s}$.
  - Built real-time TreeSHAP explainability engine mapping 38 encoded feature dimensions back to 12 intuitive lifestyle inputs, identifying bidirectional positive and negative score drivers.
  - Deployed an asynchronous FastAPI microservice with Pydantic v2 schema validation, in-memory Prometheus telemetry, automated smoke tests, and an interactive web frontend.
  - Designed an isolated shadow validation framework with strict anti-retraining governance, cryptographic SHA-256 artifact verification, and a 147-test automated test suite.

### Option B: Concise Single-Paragraph Summary (for Portfolio / LinkedIn)
> *"Built an end-to-end student wellbeing score prediction system using leakage-free preprocessing and a tuned Extra Trees model ($R^2 \approx 0.9275$), with TreeSHAP explainability, conformal prediction intervals ($92.70\%$ empirical coverage at $90\%$ confidence), and an asynchronous FastAPI serving layer with 147 automated tests."*
