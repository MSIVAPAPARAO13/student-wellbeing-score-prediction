# Phase 3: Controlled Feature Ablation Results Report

**Project:** Student Mental Health / Student Wellbeing Score Prediction  
**Phase:** PHASE 3 — Controlled Feature Engineering & Feature Selection  
**Notebook Source of Truth:** [`ml/notebooks/03_preprocessing_feature_engineering.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/03_preprocessing_feature_engineering.ipynb)  
**Experiment Log:** [`ml/experiments/phase3_feature_engineering_results.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase3_feature_engineering_results.csv)  
**Date:** October 2026  
**Auditor:** Antigravity AI Pair Programmer  

---

## 1. Experimental Protocol & Controlled Design

To isolate the true empirical value of the candidate engineered features, the experimental configuration was held strictly constant:
* **Partition:** 3,998 training records / 1,000 holdout records (`random_state=42`, 80/20 split).
* **Validation Strategy:** Identical 5-Fold Cross-Validation (`KFold(n_splits=5, shuffle=True, random_state=42)`) applied strictly to the 3,998 training records.
* **Primary Estimator:** Phase 2 Verified Baseline Random Forest (`RandomForestRegressor(n_estimators=100, random_state=42)`).
* **Preprocessing Pipeline:** Identical leakage-free pipeline (StandardScaler on numericals, OrdinalEncoder on `Stress_Level`, OneHotEncoder on nominals with `handle_unknown='ignore'`).
* **Feature Selection Authority:** Decisions were governed **strictly by 5-fold CV on the training partition**. The holdout test set was not inspected or used to guide selection.

---

## 2. Full Feature Ablation Benchmark Results

| Experiment | Features Added | Total Features | CV $R^2$ Mean $\pm$ Std | CV MAE Mean | CV RMSE Mean | Train $R^2$ | $\Delta \text{CV } R^2$ vs Baseline | Holdout Test $R^2$ | Holdout Test MAE | Holdout Test RMSE | Selection Status | Decision Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Exp A: Baseline (Phase 2)** | 0 | 12 | **0.864777 $\pm$ 0.007915** | **0.342977** | **0.464089** | 0.982755 | **0.000000** | **0.890397** | **0.326545** | **0.442339** | **SELECTED (Retained)** | Highest CV $R^2$, lowest CV RMSE, most parsimonious |
| **Exp B: + `screen_to_sleep_ratio`** | 1 | 13 | 0.860611 $\pm$ 0.009569 | 0.352916 | 0.471299 | 0.982350 | -0.004166 | 0.886699 | 0.330051 | 0.449739 | **REJECTED** | Degraded CV $R^2$, increased error, higher fold variance |
| **Exp C: + `study_to_sleep_ratio`** | 1 | 13 | 0.860721 $\pm$ 0.007741 | 0.349274 | 0.471063 | 0.982216 | -0.004056 | 0.885174 | 0.335426 | 0.452757 | **REJECTED** | Degraded CV $R^2$, increased error |
| **Exp D: + `unlocks_per_usage_hour`** | 1 | 13 | 0.858581 $\pm$ 0.008594 | 0.352123 | 0.474593 | 0.981709 | -0.006197 | 0.880998 | 0.341968 | 0.460917 | **REJECTED** | Severe degradation in CV $R^2$ (-0.0062) and holdout (-0.0094) |
| **Exp E: + `active_to_sedentary_ratio`** | 1 | 13 | 0.861279 $\pm$ 0.008696 | 0.348283 | 0.470043 | 0.982165 | -0.003498 | 0.884912 | 0.336883 | 0.453273 | **REJECTED** | Degraded CV $R^2$, increased error |
| **Exp F: + All 4 Ratios** | 4 | 16 | 0.851395 $\pm$ 0.008231 | 0.367220 | 0.486641 | 0.980848 | **-0.013382** | 0.877244 | 0.351622 | 0.468130 | **REJECTED** | Compounded performance degradation across all metrics |

---

## 3. Detailed Experiment-by-Experiment Analysis

### Exp B: Addition of `screen_to_sleep_ratio`
* **Hypothesis:** High daily screen usage relative to low sleep hours would identify students at risk of elevated stress.
* **Empirical Outcome:** CV $R^2$ declined from $0.864777$ to $0.860611$ ($\Delta = -0.004166$). CV RMSE increased from $0.464089$ to $0.471299$. CV standard deviation increased from $\pm 0.0079$ to $\pm 0.0096$.
* **Mechanism:** As identified in the VIF analysis, `screen_to_sleep_ratio` is highly collinear with `Avg_Daily_Usage_Hours` ($r = +0.94$, VIF 48.8). Random Forest already splits nonlinearly on both features; adding their explicit ratio offered no new discriminatory boundaries while diluting split opportunities.

### Exp C: Addition of `study_to_sleep_ratio`
* **Hypothesis:** Heavy study loads competing with sleep would reveal academic strain.
* **Empirical Outcome:** CV $R^2$ declined to $0.860721$ ($\Delta = -0.004056$). CV RMSE increased to $0.471063$.
* **Mechanism:** `Study_Hours` VIF exploded from $4.42$ to $126.01$, and the ratio VIF reached $79.82$. The feature is over 98.7% linearly explained by existing features, providing redundant splits.

### Exp D: Addition of `unlocks_per_usage_hour`
* **Hypothesis:** Compulsive phone checking (frequent unlocks within limited screen time) would capture fragmented attention.
* **Empirical Outcome:** Worst individual performer. CV $R^2$ dropped by $-0.006197$ to $0.858581$. CV RMSE increased from $0.464089$ to $0.474593$.
* **Mechanism:** This ratio displays heavy right-skew (+1.96). In instances of low usage hours, unlock counts produce wide ratio swings that introduce noisy split points near the tree roots.

### Exp E: Addition of `active_to_sedentary_ratio`
* **Hypothesis:** Physical activity offsetting screen time would represent a protective behavioral balance.
* **Empirical Outcome:** CV $R^2$ declined to $0.861279$ ($\Delta = -0.003498$). CV RMSE rose to $0.470043$.
* **Mechanism:** Exercise hours were already floored at zero. For students with minimal screen time, the ratio exhibits high variance (+1.91 skewness) without offering consistent predictive signal across folds.

### Exp F: Addition of All 4 Ratios
* **Hypothesis:** Synergistic combinations of all behavioral ratios would collectively capture multi-dimensional student lifestyles.
* **Empirical Outcome:** **Severe cumulative degradation.** CV $R^2$ fell by $-0.013382$ to $0.851395$. CV RMSE degraded by $+0.022551$ to $0.486641$. CV MAE degraded from $0.342977$ to $0.367220$.
* **Mechanism:** Compounded multicollinearity (VIFs up to 126.0) severely diluted the random feature subspace. Decision trees consistently selected suboptimal pseudo-duplicate splits, impairing ensemble diversity.

The ablation cross-validation comparison plot is preserved in [`ml/evaluation/phase3_ablation_cv_comparison.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase3_ablation_cv_comparison.png).

---

## 4. Holdout Evaluation (Controlled Verification)

In strict accordance with Phase 3 instructions, the holdout test set (1,000 records) was evaluated **only after** all feature selection decisions were frozen from the training CV results.

The holdout test findings fully mirror and validate the cross-validation decisions:
* **Exp A (Baseline):** Test $R^2 = \mathbf{0.890397}$, Test RMSE = $\mathbf{0.442339}$, Test MAE = $\mathbf{0.326545}$
* **Exp B:** Test $R^2 = 0.886699$ (Degraded by -0.0037)
* **Exp C:** Test $R^2 = 0.885174$ (Degraded by -0.0052)
* **Exp D:** Test $R^2 = 0.880998$ (Degraded by -0.0094)
* **Exp E:** Test $R^2 = 0.884912$ (Degraded by -0.0055)
* **Exp F:** Test $R^2 = 0.877244$ (Degraded by -0.0132)

Every single candidate engineered feature set caused generalization to deteriorate on the holdout test partition.
