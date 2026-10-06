# MODEL CARD — PHASE 5 TUNED EXTRA TREES REGRESSOR

**Model Name:** Student Wellbeing Score Predictor (Phase 5 Champion)  
**Model Version:** `phase5_tuned_extra_trees` (v1.0.0)  
**Artifact Path:** `models/phase5_tuned_extra_trees.joblib`  
**Cryptographic Hash (SHA-256):** `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8`  
**Associated Conformal Artifact:** `models/phase7_1_conformal_calibration.json` (`22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b`)  
**Release Date:** October 5, 2026  
**License:** Educational & Research Use Only  
**Responsible AI Scope:** Strictly Non-Clinical Survey Wellbeing Scoring  

---

## 1. Model Overview & Purpose

### Intended Use:
- Predict a continuous statistical **Wellbeing Score** (domain $[1.0, 10.0]$) for university and college students based on self-reported social media usage, academic workload, and lifestyle habits.
- Provide calibrated uncertainty intervals at $80\%$, $90\%$, and $95\%$ nominal coverage using finite-sample cross-conformal prediction.
- Provide local, on-demand feature attributions using TreeSHAP to understand self-reported lifestyle influences.

### Out-of-Scope & Prohibited Uses:
- **NOT a Diagnostic Tool:** Must NEVER be used for clinical psychiatric diagnosis, depression detection, anxiety screening, or medical classification.
- **NOT a Crisis Response System:** Must NEVER be used to triage suicidal ideation, self-harm risks, or urgent psychiatric emergencies.
- **NOT an Automated Decision System:** Must NEVER be used for automated university admissions, academic sanctions, or healthcare eligibility determinations.
- **NOT a Causal Inference Engine:** Feature coefficients and SHAP values indicate observational statistical association, NOT causal lifestyle interventions.

---

## 2. Training Data & Preprocessing

### Dataset Summary:
- **Source:** Survey on Student Social Media and Mental Health Impact (`Student Social Media And Mental Health Impact.csv`).
- **Raw Volume:** 5,000 records; deduplicated to 4,998 unique records in Phase 2.
- **Partitioning:**
  - **Training Reference Subset:** 3,998 records (used for feature engineering, hyperparameter tuning, and cross-conformal calibration).
  - **Quarantined Evaluation Holdout:** 1,000 records ($20.01\%$), strictly quarantined and isolated from training, tuning, and CI/CD container packaging.
- **Leakage Prevention:**
  - Preprocessing pipeline fits `ColumnTransformer` strictly on training folds.
  - Zero target encoding leakage; country grouping threshold ($N \ge 100$) computed inside pipeline.

### Input Feature Schema (12 Dimensions):
| Feature Name | Type | Domain / Values | Description |
| :--- | :---: | :---: | :--- |
| `Study_Hours` | Continuous | $[0.5, 8.3]$ hours/day | Daily study time |
| `Age` | Integer | $[18, 24]$ years | Student age |
| `Avg_Daily_Usage_Hours` | Continuous | $[1.1, 8.8]$ hours/day | Daily screen/social media time |
| `Daily_Unlocks` | Integer | $[62, 273]$ unlocks/day | Frequency of phone unlocking |
| `Physical_Activity_Hours` | Continuous | $[-0.4, 4.1]$ hours/day | Daily exercise/activity |
| `Sleep_Hours_Per_Night` | Continuous | $[3.6, 9.9]$ hours/night | Nightly sleep duration |
| `Stress_Level` | Ordinal | `Low`, `Medium`, `High`, `Very High` | Self-reported perceived stress |
| `Gender` | Categorical | `Male`, `Female` | Self-identified gender |
| `Academic_Level` | Categorical | `High School`, `Undergraduate`, `Graduate` | Current enrollment status |
| `Most_Used_Platform` | Categorical | 12 social platforms (Instagram, TikTok, etc.) | Primary social network |
| `Purpose_Of_Use` | Categorical | `Entertainment`, `Education`, `Networking`, `News` | Primary usage intention |
| `Country` / `Grouped_country` | Categorical | Top 10 countries + `Other` | Geographical location |

### Target Definition:
- **`Mental_Health_Score`:** Continuous survey-derived wellbeing index ranging from $1.0$ (lowest wellbeing) to $10.0$ (highest wellbeing).

---

## 3. Model Architecture & Hyperparameters

- **Estimator Family:** `sklearn.ensemble.ExtraTreesRegressor` within an end-to-end `sklearn.pipeline.Pipeline`.
- **Ensemble Hyperparameters:**
  - `n_estimators`: 500
  - `max_depth`: `None` (full depth tree expansion)
  - `min_samples_split`: 2
  - `min_samples_leaf`: 1
  - `max_features`: `"sqrt"` ($\approx \sqrt{38} \approx 6$ candidate features per split)
  - `random_state`: 42
  - `n_jobs`: -1

---

## 4. Quantitative Performance Metrics

### Validated Holdout Accuracy ($N=1,000$ Untouched Records):
- **Coefficient of Determination ($R^2$):** $\mathbf{0.927548}$
- **Root Mean Squared Error ($\text{RMSE}$):** $\mathbf{0.359641}$
- **Mean Absolute Error ($\text{MAE}$):** $\mathbf{0.249022}$
- **5-Fold Cross-Validation $R^2$:** $0.911006 \pm 0.003525$
- **Train-CV Generalization Gap:** $0.088983$ (indicating high stability without destructive overfitting)

### Uncertainty Quantification (Phase 7.1 Cross-Conformal):
- **Methodology:** 5-Fold Cross-Conformal / Out-Of-Fold Residual Calibration (finite-sample exact exchangeability).
- **Nominal 90% Target:** Empirical holdout coverage = $\mathbf{92.70\%}$ (Conservative margin: $+2.70\%$).
- **90% Mean Interval Width:** $\mathbf{1.1884\text{ units}}$ ($q_{90} = 0.5942$).
- **Multi-Tier Calibration Quantiles:**
  - $80\%$ Tier: $q_{80} = 0.4156$ | Mean Width: $0.8312$ | Empirical Coverage: $84.60\%$
  - $90\%$ Tier: $q_{90} = 0.5942$ | Mean Width: $1.1884$ | Empirical Coverage: $92.70\%$
  - $95\%$ Tier: $q_{95} = 0.7902$ | Mean Width: $1.5804$ | Empirical Coverage: $95.80\%$

---

## 5. Explainability & Interpretability

- **SHAP Method:** TreeSHAP (`shap.TreeExplainer`) executed directly across all 500 decision trees.
- **Aggregation Layer:** Internally maps 38 one-hot transformed dummy columns back to the 12 human-interpretable survey questions.
- **Global Feature Importance Hierarchy:**
  1. `Sleep_Hours_Per_Night` (Strong positive driver: mean $|SHAP| \approx 0.62$)
  2. `Stress_Level` (Strong negative driver: High/Very High reduces wellbeing by $\sim 0.54$)
  3. `Avg_Daily_Usage_Hours` (Negative driver above 5 hours: mean $|SHAP| \approx 0.41$)
  4. `Daily_Unlocks` (Negative driver: mean $|SHAP| \approx 0.28$)
  5. `Study_Hours` (Moderate positive driver: mean $|SHAP| \approx 0.22$)
  6. `Physical_Activity_Hours` (Positive driver: mean $|SHAP| \approx 0.18$)

---

## 6. Known Limitations & Caveats

1. **Self-Report Bias:** Survey responses are subject to recall bias and social desirability effects.
2. **Marginal vs. Conditional Coverage:** Conformal intervals guarantee exact marginal coverage over the survey distribution; individual sub-demographics may experience localized variance.
3. **Inference Latency Trade-Off:** While `/predict` executes synchronously in $\sim 118\text{ ms}$, full TreeSHAP `/explain` requires $\sim 1.65\text{ s}$ due to exhaustive tree traversal.

---

## 7. Model Governance & Production Lifecycle

- **Governance State:** `APPROVED_FOR_PRODUCTION` (Active Champion).
- **Automatic Retraining:** **Strictly Forbidden.**
- **Automatic Promotion:** **Strictly Forbidden.**
- **Integrity Enforcement:** Validated on every container startup and during `GET /health` requests via SHA-256 matching.
- **Monitoring Framework:** Continuous Population Stability Index (PSI), Kolmogorov-Smirnov (KS), and Total Variation Distance (TVD) auditing.
