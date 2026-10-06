# Phase 3: Controlled Feature Engineering Report

**Project:** Student Mental Health / Student Wellbeing Score Prediction  
**Phase:** PHASE 3 — Controlled Feature Engineering & Feature Selection  
**Notebook Source of Truth:** [`ml/notebooks/03_preprocessing_feature_engineering.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/03_preprocessing_feature_engineering.ipynb)  
**Date:** October 2026  
**Auditor:** Antigravity AI Pair Programmer  

---

## 1. Executive Summary

In Phase 3, we conducted a controlled, hypothesis-driven feature engineering study to determine whether row-level domain interaction features improve predictive performance, stability, or generalization for the Student Mental Health Score regression model.

In accordance with strict empirical ML principles:
1. **Hypothesis-Driven, Not Speculative:** Only four domain-motivated interaction ratios were formulated. Proliferation of arbitrary polynomial or interaction terms was avoided.
2. **Leakage-Free Implementation:** All candidate features are deterministic, row-level mathematical transformations. Zero full-dataset summary statistics, global target encodings, or out-of-fold statistics were used.
3. **Numerically Defended:** Safe division was enforced via `np.divide(..., where=...)` with fallback zero-filling to guard against division-by-zero, positive/negative infinity, and `NaN` values.
4. **Empirical Gatekeeping:** Candidate features were treated as testable hypotheses, not assumed improvements. Acceptance required cross-validated performance improvements without unacceptable instability or multicollinearity.

---

## 2. Candidate Feature Formulations & Behavioural Interpretation

| Feature Name | Mathematical Definition | Behavioural / Domain Interpretation |
| :--- | :--- | :--- |
| **`screen_to_sleep_ratio`** | $\frac{\text{Avg\_Daily\_Usage\_Hours}}{\text{Sleep\_Hours\_Per\_Night}}$ | Quantifies digital social media screen engagement relative to nocturnal restorative sleep duration. |
| **`study_to_sleep_ratio`** | $\frac{\text{Study\_Hours}}{\text{Sleep\_Hours\_Per\_Night}}$ | Measures academic workload commitment relative to nightly physiological recovery time. |
| **`unlocks_per_usage_hour`** | $\frac{\text{Daily\_Unlocks}}{\text{Avg\_Daily\_Usage\_Hours}}$ | Gauges behavioral fragmentation and phone-checking frequency per hour of active screen engagement. |
| **`active_to_sedentary_ratio`** | $\frac{\text{Physical\_Activity\_Hours}}{\text{Avg\_Daily\_Usage\_Hours}}$ | Captures the balance between physical exercise and sedentary screen-based activities. |

> [!NOTE]
> **Responsible AI Language Notice:** All features reflect *statistical associations* and *model-associated behavioral signals*. They do not represent causal medical determinants or clinical psychiatric diagnoses.

---

## 3. Numerical Safety & Verification

In production environments, user inputs can contain zero or missing values. To prevent numerical instability, safe division was implemented:

```python
def add_engineered_features(data):
    d = data.copy()
    
    # 1. Screen to Sleep Ratio
    d['screen_to_sleep_ratio'] = np.divide(
        d['Avg_Daily_Usage_Hours'],
        d['Sleep_Hours_Per_Night'],
        out=np.zeros_like(d['Avg_Daily_Usage_Hours'], dtype=float),
        where=d['Sleep_Hours_Per_Night'] != 0
    )
    
    # 2. Study to Sleep Ratio
    d['study_to_sleep_ratio'] = np.divide(
        d['Study_Hours'],
        d['Sleep_Hours_Per_Night'],
        out=np.zeros_like(d['Study_Hours'], dtype=float),
        where=d['Sleep_Hours_Per_Night'] != 0
    )
    
    # 3. Unlocks per Usage Hour
    d['unlocks_per_usage_hour'] = np.divide(
        d['Daily_Unlocks'].astype(float),
        d['Avg_Daily_Usage_Hours'],
        out=np.zeros_like(d['Daily_Unlocks'], dtype=float),
        where=d['Avg_Daily_Usage_Hours'] != 0
    )
    
    # 4. Active to Sedentary Ratio
    d['active_to_sedentary_ratio'] = np.divide(
        d['Physical_Activity_Hours'],
        d['Avg_Daily_Usage_Hours'],
        out=np.zeros_like(d['Physical_Activity_Hours'], dtype=float),
        where=d['Avg_Daily_Usage_Hours'] != 0
    )
    
    return d
```

### Numerical Safety Verification Results (Training Split, N = 3,998)
* `screen_to_sleep_ratio`: 0 NaNs, 0 +Infs, 0 -Infs (100% Passed)
* `study_to_sleep_ratio`: 0 NaNs, 0 +Infs, 0 -Infs (100% Passed)
* `unlocks_per_usage_hour`: 0 NaNs, 0 +Infs, 0 -Infs (100% Passed)
* `active_to_sedentary_ratio`: 0 NaNs, 0 +Infs, 0 -Infs (100% Passed)

Zero invalid numerical records were generated across all 3,998 training records and all 1,000 holdout records.

---

## 4. Feature Distribution Analysis

Parametric and non-parametric summary statistics were calculated across the 3,998 training records:

| Feature Name | Count | Mean | Std | Min | 25% | Median | 75% | Max | Skewness | IQR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`screen_to_sleep_ratio`** | 3,998 | 0.8314 | 0.3970 | 0.1446 | 0.5062 | 0.7627 | 1.1333 | 2.4444 | +0.5066 | 0.6272 |
| **`study_to_sleep_ratio`** | 3,998 | 0.4339 | 0.1942 | 0.0806 | 0.2600 | 0.4324 | 0.5757 | 1.0541 | +0.3147 | 0.3157 |
| **`unlocks_per_usage_hour`** | 3,998 | 35.0611 | 5.3467 | 26.5432 | 31.5932 | 33.7931 | 37.0588 | 71.6667 | +1.9631 | 5.4656 |
| **`active_to_sedentary_ratio`** | 3,998 | 0.4292 | 0.3200 | 0.0000 | 0.2136 | 0.3448 | 0.5405 | 2.7273 | +1.9103 | 0.3270 |

### Observations on Distributions
1. **`screen_to_sleep_ratio`** and **`study_to_sleep_ratio`** exhibit near-normal, moderately symmetrical profiles with modest positive skewness (+0.51 and +0.31, respectively).
2. **`unlocks_per_usage_hour`** and **`active_to_sedentary_ratio`** display extended right tails (skewness +1.96 and +1.91) caused by instances of high unlock counts on lower usage hours, or substantial physical exercise relative to minimal screen use.
3. Visual density and boxplot checks confirmed that while right tails exist, values represent legitimate bounded ratios without runaway asymptotic spikes. No artificial clipping was applied in order to preserve natural student variance.

Distribution diagnostic plots are preserved in [`ml/evaluation/phase3_feature_distributions.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase3_feature_distributions.png).

---

## 5. Bivariate Correlation Analysis

Correlations with the target variable `Mental_Health_Score` were computed on the training partition strictly as an exploratory diagnostic:

| Feature | Pearson Correlation ($r$) with `Mental_Health_Score` | Nature of Association |
| :--- | :--- | :--- |
| `Avg_Daily_Usage_Hours` (Baseline) | **-0.814075** | Strong negative association |
| `screen_to_sleep_ratio` (Engineered) | **-0.800250** | Strong negative association |
| `Daily_Unlocks` (Baseline) | **-0.789386** | Strong negative association |
| `Sleep_Hours_Per_Night` (Baseline) | **+0.764033** | Strong positive association |
| `Study_Hours` (Baseline) | **+0.751930** | Strong positive association |
| `active_to_sedentary_ratio` (Engineered) | **+0.682834** | Moderate-strong positive association |
| `study_to_sleep_ratio` (Engineered) | **+0.625840** | Moderate-strong positive association |
| `unlocks_per_usage_hour` (Engineered) | **+0.594217** | Moderate positive association |
| `Physical_Activity_Hours` (Baseline) | **+0.519760** | Moderate positive association |

### Diagnostic Takeaways
* While `screen_to_sleep_ratio` exhibits a high linear correlation ($r = -0.800$), it is collinear with its parent terms (`Avg_Daily_Usage_Hours` $r = -0.814$ and `Sleep_Hours_Per_Night` $r = +0.764$).
* Correlation alone does not demonstrate whether an engineered ratio provides *orthogonal, incremental signal* to a nonlinear decision tree ensemble. As shown in the ablation study, high correlation can mask destructive redundancy.

Correlation heatmap is preserved in [`ml/evaluation/phase3_correlation_matrix.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase3_correlation_matrix.png).
