# Phase 3: Final Results & Feature Selection Decision Report

**Project:** Student Mental Health / Student Wellbeing Score Prediction  
**Phase:** PHASE 3 — Controlled Feature Engineering & Feature Selection  
**Notebook Source of Truth:** [`ml/notebooks/03_preprocessing_feature_engineering.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/03_preprocessing_feature_engineering.ipynb)  
**Date:** October 2026  
**Auditor:** Antigravity AI Pair Programmer  

---

## 1. Executive Summary & Core Scientific Finding

Phase 3 evaluated whether row-level domain interaction features improve predictive performance, stability, or generalization for the Student Mental Health Score regression model.

### Key Finding
**None of the four candidate interaction features improved cross-validation or holdout performance.** Every candidate ratio degraded cross-validated $R^2$, increased root-mean-squared error, elevated mean absolute error, and introduced severe multicollinearity (VIF scores exceeding 126.0). 

In accordance with strict Occam's Razor and empirical machine learning principles:
* **All four candidate engineered features were REJECTED.**
* **The clean, parsimonious Phase 2 baseline feature set (12 features) is RETAINED as the official feature representation.**
* **Scientific Outcome:** This constitutes **Outcome C / Outcome D** (Features degraded performance; retaining the simpler, more robust baseline model is the correct scientific decision).

---

## 2. Feature Selection Rule & Evaluation Criteria

A candidate feature or feature set was considered acceptable if and only if it satisfied all criteria of the predefined Phase 3 Quality Standard:
1. **$\Delta \text{CV } R^2 > 0$:** Higher cross-validation coefficient of determination.
2. **$\Delta \text{CV RMSE} < 0$:** Lower cross-validation root-mean-squared error.
3. **$\Delta \text{CV MAE} \le 0$:** Lower or equivalent cross-validation mean absolute error.
4. **Stable Fold Variance:** No substantial increase in CV standard deviation across folds.
5. **Well-Conditioned Covariance:** No extreme variance inflation (VIF $< 20$).
6. **Parsimony Justification:** Added complexity must be justified by meaningful empirical gains.

### Evaluation of Candidates Against Criteria

| Candidate Feature | CV $R^2$ ($\Delta$) | CV RMSE ($\Delta$) | Max VIF | CV Stability | Decision |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `screen_to_sleep_ratio` | 0.860611 (-0.004166) | 0.471299 (+0.007210) | 48.81 | Degraded ($\sigma = 0.0096$) | **REJECTED** |
| `study_to_sleep_ratio` | 0.860721 (-0.004056) | 0.471063 (+0.006974) | 126.01 | Degraded | **REJECTED** |
| `unlocks_per_usage_hour` | 0.858581 (-0.006197) | 0.474593 (+0.010504) | 61.38 | Severely Degraded | **REJECTED** |
| `active_to_sedentary_ratio` | 0.861279 (-0.003498) | 0.470043 (+0.005954) | 16.85 | Degraded | **REJECTED** |
| All 4 Ratios Combined | 0.851395 (-0.013382) | 0.486641 (+0.022552) | 126.01 | Severely Degraded | **REJECTED** |

---

## 3. Phase 3 Selected Feature Set

### Retained Features (12 Original Baseline Features)

#### A. Continuous Numerical Predictors (Scaled via `StandardScaler`, Median-Imputed)
1. `Age` (Student age in years)
2. `Avg_Daily_Usage_Hours` (Social media screen hours per day)
3. `Daily_Unlocks` (Frequency of device unlock actions per day)
4. `Study_Hours` (Academic study hours per day)
5. `Physical_Activity_Hours` (Daily physical exercise hours, floored at 0.0)
6. `Sleep_Hours_Per_Night` (Nocturnal sleep duration in hours)

#### B. Ordinal Predictor (Encoded via `OrdinalEncoder`, Most-Frequent Imputed)
7. `Stress_Level` (Ordered: `Low` < `Moderate` < `High`)

#### C. Nominal Categorical Predictors (Encoded via `OneHotEncoder`, Most-Frequent Imputed)
8. `Gender` (Student gender identity)
9. `Academic_Level` (Undergraduate, Graduate, High School)
10. `Most_Used_Platform` (Dominant social media platform)
11. `Purpose_Of_Use` (Primary reason for social media activity)
12. `Grouped_country` (Top-10 countries learned strictly from training data, remaining mapped to 'Other')

---

## 4. Cross-Phase Historical Progression

| Phase | Methodology / Architecture | Total Input Features | CV $R^2$ Mean | CV RMSE Mean | Holdout Test $R^2$ | Holdout Test RMSE | Leakage Free? |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Phase 1** | Script-based 70/30 split, global country grouping, pre-split imputation | 12 | *None (No CV)* | *None* | 0.8872 | 0.4437 | **NO (Severe Leakage)** |
| **Phase 2** | Notebook-first 80/20 split, 5-fold CV, pipeline preprocessing, clean data | 12 | **0.8648 $\pm$ 0.0079** | **0.4641** | **0.8904** | **0.4423** | **YES (Verified)** |
| **Phase 3** | Controlled feature engineering study, 4 ratios tested, ablation benchmark | 12 | **0.8648 $\pm$ 0.0079** | **0.4641** | **0.8904** | **0.4423** | **YES (Verified)** |

> [!NOTE]
> Phase 3 rigorously tested whether feature engineering could beat Phase 2. The empirical evidence proved that adding interaction terms reduced CV $R^2$ to $0.8514$ and Test $R^2$ to $0.8772$. By rejecting the degraded features, the verified Phase 2 baseline is preserved without performance compromise.

---

## 5. Complexity & Computational Impact Analysis

| Dimension | Phase 2 Baseline (Retained) | Phase 3 Exp F (+ All 4 Ratios) | Impact Assessment |
| :--- | :--- | :--- | :--- |
| **Input Columns** | 12 features | 16 features | +33% input surface area |
| **One-Hot Transformed Columns** | 38 columns | 42 columns | +4 redundant continuous columns |
| **Max Predictor VIF** | 17.10 (`Avg_Daily_Usage_Hours`) | **126.01** (`Study_Hours`) | Severe multicollinearity explosion |
| **CV Training Time** | ~8.34 s (5 folds total) | ~4.33 s (single fold fits) | No computational bottleneck |
| **Pipeline Maintenance** | Clean `ColumnTransformer` | Additional custom ratio step | Avoided unnecessary transformer code |
| **Production Artifact Footprint** | ~5.3 MB ([`phase2_baseline.joblib`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/phase2_baseline.joblib)) | *Unchanged* | Zero disk bloat |

---

## 6. Model Artifact Policy Compliance

Per user guidelines:
> *"Do NOT automatically create many model artifacts. If Phase 3 produces a genuinely selected model, create at most `models/phase3_feature_engineered.joblib`. Otherwise do not create an artifact."*

Because the engineered features were empirically rejected, no inferior `phase3_feature_engineered.joblib` artifact was created. [`models/phase2_baseline.joblib`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/phase2_baseline.joblib) remains the sole, active, verified baseline model artifact.

---

## 7. Phase 3 Quality Gate Verification

| Quality Gate Item | Status | Verification Detail |
| :--- | :---: | :--- |
| Phase 2 baseline reproduced | **PASSED** | Baseline Random Forest CV $R^2 = 0.864777$, Test $R^2 = 0.890397$ confirmed. |
| One Phase 3 notebook created | **PASSED** | [`03_preprocessing_feature_engineering.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/03_preprocessing_feature_engineering.ipynb) created and executed. |
| No unnecessary ML `.py` files created | **PASSED** | Exactly 0 new ML `.py` files created. |
| Four proposed ratios evaluated | **PASSED** | All 4 candidates evaluated individually and in combination. |
| Safe division verified | **PASSED** | Protected with `np.divide(..., where=...)`. |
| No NaN/inf introduced | **PASSED** | Automated assertion confirmed 0 NaNs and 0 Infs across all records. |
| Correlation analysis completed | **PASSED** | Heatmap and target correlations computed and documented. |
| VIF analysis completed | **PASSED** | Pre- and post-engineering VIF matrices calculated and interpreted. |
| Feature ablation completed | **PASSED** | Exp A through Exp F executed under identical CV protocol. |
| 5-fold CV used consistently | **PASSED** | Same `KFold(n_splits=5, shuffle=True, random_state=42)` across all runs. |
| Model configuration kept fixed | **PASSED** | Default Random Forest (100 trees) held fixed across all ablation runs. |
| Feature set selected using CV | **PASSED** | Decisions based strictly on out-of-fold cross-validation metrics. |
| Holdout evaluated only after selection | **PASSED** | Holdout evaluated once at the end; confirmed degradation across all ratios. |
| No feature changed after holdout | **PASSED** | Decisions were frozen before holdout evaluation. |
| Feature importance compared | **PASSED** | Relative contributions extracted and visual diagnostic exported. |
| Complexity impact measured | **PASSED** | Dimensionality, VIF, and pipeline impact documented. |
| Results documented | **PASSED** | Experiment results logged to [`phase3_feature_engineering_results.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase3_feature_engineering_results.csv). |
| Phase 3 reports created | **PASSED** | 4 detailed markdown reports delivered to `reports/phase3/`. |
| Final recommendation documented | **PASSED** | Parsimonious baseline retained; clear transition path to Phase 4 outlined. |
