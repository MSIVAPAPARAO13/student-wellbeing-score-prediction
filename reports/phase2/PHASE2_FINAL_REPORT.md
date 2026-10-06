# Phase 2: Final Executive & Technical Summary Report

**Project:** Student Mental Health / Student Wellbeing Score Prediction  
**Phase:** PHASE 2 — Data Quality, Leakage-Free Pipeline & Reproducible ML Baseline  
**Notebook Source of Truth:** [`ml/notebooks/02_data_quality_eda.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/02_data_quality_eda.ipynb)  
**Date:** October 2026  
**Auditor:** Antigravity AI Pair Programmer  

---

## 1. Direct Answers to the 12 Core Audit Questions

### 1. What changed?
* The ML workflow shifted to a strict **Notebook-First architecture**.
* The raw dataset was quarantined and preserved in `ml/data/raw/`.
* The partition ratio changed from 70/30 (3,500/1,500) to **80/20 (3,998/1,000)**.
* Category grouping, scalers, imputers, and encoders were refactored to fit **strictly on training data**.
* A formal **5-Fold Cross-Validation protocol** was implemented on the training partition for model selection.
* An end-to-end, top-to-bottom executable notebook [`02_data_quality_eda.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/02_data_quality_eda.ipynb) was authored, executed, and saved with complete outputs.

### 2. What data-quality problems were fixed?
* **Exact Duplicate Records:** Detected and removed 2 exact duplicate rows (Indices 2405 and 2463), reducing the modeling dataset from 5,000 to **4,998 clean records**.
* **Negative Durations:** Identified 10 records with negative exercise hours in `Physical_Activity_Hours` (values: -0.1 to -0.4). Applied an explicit floor clipping rule (`clip(lower=0.0)`), eliminating negative hours while preserving student responses.
* **Defensive Imputation Safeguards:** Replaced omitted imputers with unified `SimpleImputer` instances inside the `ColumnTransformer`.

### 3. Was data leakage removed?
* **YES, 100% ELIMINATED.** All statistical thresholds, frequency counts, standard scalers, and encoder vocabularies are derived strictly from the 3,998 training records. The 1,000-record test set was completely quarantined until the final evaluation.

### 4. How was country grouping changed?
* In Phase 1, top-10 countries were determined across all 5,000 records before splitting.
* In Phase 2, top-10 countries were determined **strictly on `train_df['Country']`**:
  `['Other', 'India', 'USA', 'Canada', 'Australia', 'UK', 'Germany', 'Mexico', 'France', 'Turkey']`.
  (France and Turkey tied for #9 and #10 at 74 rows each; Spain was dropped to #11 at 73 rows).
* The learned mapping was frozen and projected onto `test_df`, mapping non-top-10 countries into `"Other"`.

### 5. What split strategy is now used?
* **80% Training (3,998 records) / 20% Holdout Test (1,000 records)** using `random_state=42`.
* Performed prior to any data-dependent feature engineering or transformation.

### 6. What CV methodology is used?
* **5-Fold Cross-Validation (`KFold(n_splits=5, shuffle=True, random_state=42)`)** applied strictly to the 3,998 training records.
* Out-of-fold metrics ($R^2$, MAE, RMSE) and standard deviations ($\pm \sigma$) are computed for all candidate models.

### 7. Which baseline models were evaluated?
1. **Dummy Regressor (Mean Baseline):** Non-learning statistical reference ($y = \bar{y}$).
2. **Linear Regression (OLS):** Ordinary Least Squares baseline.
3. **Ridge Regression ($\alpha=1.0$):** $L_2$ regularized linear model.
4. **Random Forest (Default):** Untuned ensemble (100 trees, unpruned).
5. **Random Forest (Regularized):** Pruned ensemble (100 trees, `max_depth=12`, `min_samples_split=5`, `min_samples_leaf=2`).

### 8. What are the CV results?
* **Dummy (Mean):** $CV\ R^2 = -0.0012 \pm 0.0016$, $CV\ MAE = 1.0508$, $CV\ RMSE = 1.2631$
* **Linear Regression:** $CV\ R^2 = 0.7206 \pm 0.0064$, $CV\ MAE = 0.5257$, $CV\ RMSE = 0.6673$
* **Ridge ($\alpha=1.0$):** $CV\ R^2 = 0.7206 \pm 0.0063$, $CV\ MAE = 0.5257$, $CV\ RMSE = 0.6672$
* **Random Forest (Default):** **$CV\ R^2 = 0.8648 \pm 0.0079$**, **$CV\ MAE = 0.3430$**, **$CV\ RMSE = 0.4641$**
* **Random Forest (Regularized):** $CV\ R^2 = 0.8411 \pm 0.0104$, $CV\ MAE = 0.3810$, $CV\ RMSE = 0.5030$

### 9. What are the final holdout test results?
* **Linear Regression:** Test $R^2 = 0.7428$, Test MAE = $0.5339$, Test RMSE = $0.6776$
* **Ridge ($\alpha=1.0$):** Test $R^2 = 0.7428$, Test MAE = $0.5338$, Test RMSE = $0.6776$
* **Random Forest (Default):** **Test $R^2 = 0.8904$**, **Test MAE = $0.3265$**, **Test RMSE = $0.4423$**
* **Random Forest (Regularized):** Test $R^2 = 0.8641$, Test MAE = $0.3746$, Test RMSE = $0.4926$

### 10. Did overfitting improve?
* In the **Default Random Forest**, acute overfitting remains present due to unconstrained leaf splits (Train $R^2 = 0.9828$ vs Test $R^2 = 0.8904$, gap = **9.24%**; Train-CV gap = **11.80%**).
* In the **Regularized Random Forest**, overfitting was substantially reduced:
  - Train $R^2$ dropped from 0.9828 to 0.9312.
  - Train-Test gap dropped from 9.24% to **6.71%** (a 2.53% improvement).
  - Train-CV gap dropped from 11.80% to **9.00%** (a 2.80% improvement).
  - This establishes the clear path for gradient boosted models (LightGBM/XGBoost) and Bayesian tuning in later phases.

### 11. What remains unresolved?
* **High Cardinality Bucket Size:** 64.88% of training data still resides in the `"Other"` country category.
* **Absence of Engineered Interaction Terms:** Domain interaction ratios (screen/sleep, study/sleep) have not yet been evaluated.
* **Large Model Artifact Size:** Default Random Forest requires ~29.2 MB of serialized memory.
* **Lack of Local Explainability:** SHAP feature attributions are not yet integrated into the serving pipeline.

### 12. What should Phase 3 investigate?
* **Domain Feature Engineering:** Formulate and validate behavior ratios:
  - `screen_to_sleep_ratio`
  - `study_to_sleep_ratio`
  - `unlocks_per_usage_hour`
  - `active_to_sedentary_ratio`
* Check for multicollinearity using Variance Inflation Factor (VIF).
* Benchmark whether engineered features measurably improve CV $R^2$ and reduce RMSE beyond the 0.8648 baseline.

---

## 2. Strict Notebook-First Governance Compliance

* **New ML Python Files Created:** **`0`**
* **All ML experimentation, data cleaning, splitting, leakage verification, cross-validation, and baseline evaluation are contained strictly within:**
  [`ml/notebooks/02_data_quality_eda.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/02_data_quality_eda.ipynb).
* **Execution Status:** Successfully executed top-to-bottom from a clean Python 3.13 kernel. All outputs, metrics, and plots are preserved in the notebook JSON.
