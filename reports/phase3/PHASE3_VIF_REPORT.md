# Phase 3: Multicollinearity & Variance Inflation Factor (VIF) Report

**Project:** Student Mental Health / Student Wellbeing Score Prediction  
**Phase:** PHASE 3 — Controlled Feature Engineering & Feature Selection  
**Notebook Source of Truth:** [`ml/notebooks/03_preprocessing_feature_engineering.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/03_preprocessing_feature_engineering.ipynb)  
**Date:** October 2026  
**Auditor:** Antigravity AI Pair Programmer  

---

## 1. Overview & Diagnostic Methodology

Multicollinearity occurs when predictor variables are highly linearly dependent on each other, creating redundant information and unstable coefficient estimations in linear models, as well as feature subspace dilution in tree ensembles.

The **Variance Inflation Factor (VIF)** for feature $i$ is calculated from the coefficient of determination ($R_i^2$) obtained by regressing $X_i$ onto all remaining continuous predictors:

$$\text{VIF}_i = \frac{1}{1 - R_i^2} = \frac{1}{\text{Tolerance}_i}$$

### Interpretative Standards
* **$\text{VIF} < 5.0$ ($\text{Tolerance} > 0.20$):** Low to moderate collinearity; stable.
* **$5.0 \le \text{VIF} < 10.0$ ($\text{Tolerance} \in [0.10, 0.20]$):** Moderate collinearity; acceptable if domain-motivated.
* **$\text{VIF} \ge 10.0$ ($\text{Tolerance} < 0.10$):** High collinearity; potential instability.
* **$\text{VIF} > 50.0$ ($\text{Tolerance} < 0.02$):** Severe collinearity; feature is almost entirely predictable from remaining features.

---

## 2. Baseline Numerical Predictors VIF (Phase 2 Configuration)

Calculated on the 3,998 training records prior to adding any interaction terms:

| Feature | VIF | Tolerance ($1 - R^2$) | $R^2$ with Remaining Features | Diagnostic Interpretation | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`Age`** | **1.012** | 0.988 | 0.012 | Orthogonal to behavioural metrics | Retained |
| **`Avg_Daily_Usage_Hours`** | **17.096** | 0.058 | 0.942 | Moderate-high linear correlation with phone unlocks | Retained (Dominant baseline signal) |
| **`Daily_Unlocks`** | **12.797** | 0.078 | 0.922 | Moderate-high linear correlation with usage hours | Retained (Captures frequency of checking) |
| **`Study_Hours`** | **4.423** | 0.226 | 0.774 | Well-conditioned, independent signal | Retained |
| **`Physical_Activity_Hours`** | **1.651** | 0.606 | 0.394 | Low collinearity | Retained |
| **`Sleep_Hours_Per_Night`** | **2.905** | 0.344 | 0.656 | Low-moderate collinearity | Retained |

In the baseline model, `Avg_Daily_Usage_Hours` and `Daily_Unlocks` show elevated VIF (~13–17) because heavy phone users naturally have higher unlock counts. However, both features provide distinct behavioral dimensions that tree-based models leverage effectively.

---

## 3. Post-Feature Engineering VIF (Baseline + All 4 Candidate Ratios)

When the 4 engineered ratio features were introduced into the continuous predictor set, severe multicollinearity exploded across the feature matrix:

| Feature | Baseline VIF | New VIF | $\Delta$ VIF | Tolerance | $R^2$ with Others | Diagnostic Assessment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`Study_Hours`** | 4.423 | **126.009** | **+121.586** | 0.008 | **0.992** | Extreme collinearity with `study_to_sleep_ratio` |
| **`Avg_Daily_Usage_Hours`** | 17.096 | **115.756** | **+98.660** | 0.009 | **0.991** | Extreme collinearity with `screen_to_sleep_ratio` |
| **`study_to_sleep_ratio`** | *N/A* | **79.819** | *New* | 0.013 | **0.987** | Severe redundancy against `Study_Hours` & `Sleep` |
| **`Daily_Unlocks`** | 12.797 | **61.378** | **+48.581** | 0.016 | **0.984** | Severe redundancy against `unlocks_per_usage_hour` |
| **`screen_to_sleep_ratio`** | *N/A* | **48.814** | *New* | 0.020 | **0.980** | Severe redundancy against `Usage_Hours` & `Sleep` |
| **`Sleep_Hours_Per_Night`** | 2.905 | **33.639** | **+30.734** | 0.030 | **0.970** | High collinearity as denominator in 2 ratios |
| **`active_to_sedentary_ratio`** | *N/A* | **16.853** | *New* | 0.059 | **0.941** | High redundancy against `Physical_Activity` & `Usage` |
| **`unlocks_per_usage_hour`** | *N/A* | **15.085** | *New* | 0.066 | **0.934** | High redundancy against `Daily_Unlocks` & `Usage` |
| **`Physical_Activity_Hours`** | 1.651 | **5.263** | **+3.612** | 0.190 | **0.810** | Moderate inflation |
| **`Age`** | 1.012 | **1.029** | **+0.017** | 0.972 | **0.028** | Unaffected (remains orthogonal) |

---

## 4. Why VIF Exploded & Why It Harms Random Forest

### Mathematical Origin of Collinearity Inflation
Because each engineered feature is an exact deterministic quotient of two existing features (e.g., $X_{\text{screen\_to\_sleep}} = X_{\text{usage}} / X_{\text{sleep}}$), and because both denominators (`Sleep_Hours_Per_Night` and `Avg_Daily_Usage_Hours`) have relatively narrow positive ranges (mostly 4–10 hours), the resulting ratios are strongly linearly collinear with the primary numerator variable. Over 98% to 99% of the variance in `Study_Hours`, `Avg_Daily_Usage_Hours`, and their ratios is mutually explained ($R^2 > 0.985$).

### Mechanism of Degradation in Tree Ensembles (Random Forest)
A common misconception in applied machine learning is that decision tree ensembles are completely immune to multicollinearity. While an individual, unpruned decision tree can pick the better of two collinear variables at a single split without numerical error, Random Forests rely on **random feature subspace sampling** (`max_features`, default $\sqrt{p}$ or $p/3$):

1. **Subspace Dilution:** When four highly collinear variables are added, they do not introduce new orthogonal signal. Instead, they crowd the candidate feature pool available at each tree split.
2. **Signal Cannibalization:** When an informative feature (such as `Avg_Daily_Usage_Hours`) is considered alongside its pseudo-duplicate (`screen_to_sleep_ratio`), the probability that the tree selects a genuinely orthogonal complementary feature (such as `Study_Hours` or platform/country indicators) is reduced.
3. **Partition Inefficiency:** The trees spend depth and split capacity splitting on slight variations of the same underlying dimension, increasing ensemble variance without improving bias.

The VIF comparison plot is preserved in [`ml/evaluation/phase3_vif_comparison.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase3_vif_comparison.png).

---

## 5. Conclusion & Empirical Policy

High VIF was used as a diagnostic rather than an automatic veto. However, when combined with the systematic ablation findings (where every single ratio degraded cross-validated $R^2$, RMSE, and MAE), the extreme VIF levels ($> 100$) confirm that these interaction ratios introduced severe information redundancy rather than useful predictive structure.
