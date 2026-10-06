# PHASE 12.2 — CLEAN CHAMPION VS CANDIDATE HEAD-TO-HEAD EVALUATION REPORT

**Project:** Student Mental Health / Wellbeing Score Prediction  
**Phase:** 12.2 — Clean Champion vs Candidate Head-to-Head Evaluation  
**Production Champion Model:** [`models/phase5_tuned_extra_trees.joblib`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/phase5_tuned_extra_trees.joblib)  
**Champion SHA-256:** `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8`  
**Candidate Challenger Model:** [`models/candidate_v1_2_revalidated.joblib`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/candidate_v1_2_revalidated.joblib)  
**Candidate SHA-256:** `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc`  
**Evaluation Standard:** Strictly Symmetric, Leakage-Free Head-to-Head Evaluation on Clean Common Evaluation Subset ($N=201$)  
**Date:** October 6, 2026  
**Status:** COMPLETE  
**Final Classification:** **`A. CANDIDATE NUMERICALLY BETTER — NOT STATISTICALLY CONCLUSIVE`**  

---

## 1. Executive Summary

Phase 12.2 conducted an authoritative, leakage-free, symmetric head-to-head comparison between the frozen production Champion and Candidate v1.2.

Following the Phase 12.1 finding—which proved that the 1,000-row Phase 12 holdout was contaminated by 799 rows (79.90%) from the Champion's training set—Phase 12.2 isolated the **Clean Common Evaluation Subset ($N=201$)**. This 201-row cohort represents the exact mathematical intersection of both models' holdouts (`Phase5Holdout ∩ Phase12Holdout`), guaranteeing that neither model encountered any of these records during training.

### Key Evaluation Findings:
1. **Point Metrics:** Candidate v1.2 achieved lower point RMSE ($0.3330$ vs $0.4072$, $\Delta = -0.0742$) and lower point MAE ($0.2502$ vs $0.2635$, $\Delta = -0.0133$) due to superior handling of extreme survey profiles (Max AE: $1.3800$ vs $2.0802$).
2. **Paired Record-by-Record Split:** On individual paired comparisons, the **Champion had lower absolute error on 57.21% of the records** ($115/201$), while Candidate v1.2 had lower absolute error on **42.79% of the records** ($86/201$).
3. **Statistical Significance Tests:**
   - **Wilcoxon Signed-Rank Test:** $W = 8986.0$, $p = 0.1584$ ($p > 0.05$, not statistically significant).
   - **Paired Permutation Test (10,000 permutations):** $p = 0.3033$ ($p > 0.05$, not statistically significant).
4. **Bootstrap Confidence Intervals (10,000 Resamples):**
   - The 95% bootstrap confidence interval for $\Delta \text{MAE}$ is $[-0.0401, +0.0103]$ and **crosses zero**.
   - The observed numerical MAE difference is **not statistically conclusive**.
5. **Governance Ruling:**
   - **CHAMPION RETAINED**. `phase5_tuned_extra_trees.joblib` remains the active production model. Automatic promotion and retraining remain strictly disabled. Candidate v1.2 remains in `CHALLENGER / VALIDATING` status.

---

## 2. Why the 201-Row Common Evaluation Subset Is Clean

For every single one of the 201 records in this subset:
1. It is a member of the **Phase 5 Historical Holdout** ($N=1,000$, seed `42`). Therefore, it was **never seen during training of the frozen Champion** (`phase5_tuned_extra_trees.joblib`).
2. It is a member of the **Phase 12 Evaluation Holdout** ($N=1,000$, seed `1242`). Therefore, it was **never seen during training of Candidate v1.2** because `Phase12Dev ∩ Phase12Holdout = 0`.
3. Both models receive the **exact same records** under identical inference conditions without any data fabrication, synthetic augmentation, or preprocessing leakage.

> **Methodological Note:** This subset is not a newly collected production cohort; it is the mathematically clean common holdout derived from the existing historical split architecture.

---

## 3. Partition Lineage

The complete 4,998-record survey dataset partitioned across historical milestones:
- **Phase 5 Partition (seed `42`):** 3,998 Training rows, 1,000 Historical Holdout rows.
- **Phase 12 Partition (seed `1242`):** 3,998 Development rows, 1,000 Evaluation Holdout rows.

### Partition Set Overlaps:
- `Phase5Train ∩ Phase12Holdout = 799 rows (79.90%)` $\rightarrow$ Contaminated Phase 12 holdout for Champion.
- `Phase5Holdout ∩ Phase12Holdout = 201 rows (20.10%)` $\rightarrow$ **Clean Common Evaluation Subset**.
- `Clean Set ∩ Phase5Train = 0 rows (0.00%)`.
- `Clean Set ∩ Phase12Dev = 0 rows (0.00%)`.

Exported to [`ml/experiments/phase12_2_clean_common_evaluation.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase12_2_clean_common_evaluation.csv).

---

## 4. Artifact Integrity

All four authoritative serialized artifacts were cryptographically audited via SHA-256:

| Artifact Name | Expected SHA-256 Hash | Computed SHA-256 Hash | Status |
| :--- | :--- | :--- | :--- |
| **`models/phase5_tuned_extra_trees.joblib`** | `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8` | `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8` | **MATCH (Frozen)** |
| **`models/candidate_v1_2_revalidated.joblib`** | `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc` | `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc` | **MATCH (Frozen)** |
| **`models/phase7_1_conformal_calibration.json`** | Matches Champion SHA-256 in source model hash | Matches Champion SHA-256 | **MATCH** |
| **`models/candidate_v1_2_conformal_calibration.json`** | Matches Candidate SHA-256 in source model hash | Matches Candidate SHA-256 | **MATCH** |

---

## 5. Champion vs Candidate Point Metrics (N=201)

From [`ml/experiments/phase12_2_model_comparison.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase12_2_model_comparison.csv):

| Metric | Champion (`phase5_tuned_extra_trees`) | Candidate (`candidate_v1_2_revalidated`) | Delta (Candidate - Champion) | Preferred Direction |
| :--- | :--- | :--- | :--- | :--- |
| **$R^2$** | 0.909767 | **0.939649** | +0.029882 | Candidate (Higher) |
| **RMSE** | 0.407234 | **0.333045** | -0.074190 | Candidate (Lower) |
| **MAE** | 0.263506 | **0.250220** | -0.013285 | Candidate (Lower) |
| **Mean Error (Bias)** | **-0.002367** | +0.008550 | +0.010917 | Champion (Near Zero) |
| **Median AE** | **0.178400** | 0.188000 | +0.009600 | Champion (Lower) |
| **Maximum AE** | 2.080200 | **1.380000** | -0.700200 | Candidate (Lower) |

- **Observation:** Candidate has lower RMSE and MAE in the aggregate, but Champion has slightly lower median absolute error ($0.1784$ vs $0.1880$).

---

## 6. Paired Error Analysis

From [`ml/experiments/phase12_2_paired_error_analysis.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase12_2_paired_error_analysis.csv):

| Metric | Value | Interpretation |
| :--- | :--- | :--- |
| **Mean Absolute Error Difference** | -0.013285 | Negative indicates Candidate has lower aggregate MAE |
| **Median Absolute Error Difference** | +0.007867 | Positive indicates Champion has lower median AE |
| **Mean Squared Error Difference** | -0.054921 | Negative indicates Candidate has lower aggregate MSE |
| **Candidate Wins Count** | **86 records (42.79%)** | Candidate had lower absolute error on 42.8% of rows |
| **Champion Wins Count** | **115 records (57.21%)** | Champion had lower absolute error on 57.2% of rows |
| **Exact Equal Count** | 0 records (0.00%) | Zero identical predictions; independent inference confirmed |

### Substantive Finding:
The Champion outperformed the Candidate on **57.21% of records**. Candidate's aggregate RMSE advantage stems primarily from mitigating single-record outlier penalties (Champion's worst residual was $2.08$ vs Candidate's $1.38$).

---

## 7. Paired Bootstrap Confidence Intervals (10,000 Resamples)

From [`ml/experiments/phase12_2_bootstrap_results.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase12_2_bootstrap_results.csv):

| Metric Comparison | Point Estimate | 95% Bootstrap Confidence Interval | Crosses Zero? | Statistical Conclusion |
| :--- | :--- | :--- | :--- | :--- |
| **$\Delta \text{MAE}$ (Cand - Champ)** | -0.013285 | **$[-0.040084, +0.010312]$** | **YES** | **Not statistically conclusive** |
| **$\Delta \text{RMSE}$ (Cand - Champ)** | -0.074190 | $[-0.137915, -0.013305]$ | NO | Driven by outlier squaring |
| **$\Delta R^2$ (Cand - Champ)** | +0.029882 | $[+0.004616, +0.064023]$ | NO | Variance reduction benefit |

Because the 95% bootstrap confidence interval for $\Delta \text{MAE}$ includes zero, the hypothesis of zero difference in absolute error cannot be rejected.

---

## 8. Statistical Significance Tests

| Test Name | Test Type | Test Statistic | $p$-Value | $\alpha = 0.05$ Decision | Effect Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Wilcoxon Signed-Rank Test** | Paired non-parametric | $W = 8986.0$ | **$0.1584$** | Fail to Reject $H_0$ | Difference in absolute errors is NOT statistically significant |
| **Paired Permutation Test** | 10,000 resamples | Mean diff = $-0.0133$ | **$0.3033$** | Fail to Reject $H_0$ | Observed mean difference easily occurs under random sign permutations |

Both non-parametric paired tests confirm that the Candidate does not achieve statistically significant superiority over the Champion on absolute errors.

---

## 9. Residual Analysis

From [`ml/experiments/phase12_2_prediction_comparison.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase12_2_prediction_comparison.csv):

| Residual Statistic ($\text{residual} = y - \hat{y}$) | Champion | Candidate |
| :--- | :--- | :--- |
| **Residual Mean** | -0.0024 | +0.0086 |
| **Residual Standard Deviation** | 0.4072 | 0.3329 |
| **Residual Median** | +0.0080 | +0.0140 |
| **Residual MAE** | 0.2635 | 0.2502 |
| **Maximum Over-Prediction** | +1.6420 | +1.3800 |
| **Maximum Under-Prediction** | -2.0802 | -1.1640 |

Both residual distributions are symmetrically centered around zero. Visualizations in `ml/notebooks/12_2_clean_champion_candidate_evaluation.ipynb` confirm absence of heteroscedasticity or systematic bias across the prediction domain.

---

## 10. Conformal Prediction Interval Evaluation (N=201)

From [`ml/experiments/phase12_2_conformal_comparison.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase12_2_conformal_comparison.csv):

| Coverage Tier | Model | Threshold $q$ | Empirical Holdout Coverage | Mean Interval Width | Coverage Error |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **80% Nominal** | Champion (`phase5_tuned_extra_trees`) | 0.4156 | **85.07%** | 0.8312 | +5.07% |
|  | Candidate (`candidate_v1_2_revalidated`) | 0.4244 | **85.57%** | 0.8488 | +5.57% |
| **90% Nominal** | Champion (`phase5_tuned_extra_trees`) | 0.5942 | **92.04%** | 1.1884 | +2.04% |
|  | Candidate (`candidate_v1_2_revalidated`) | 0.5984 | **91.04%** | 1.1968 | +1.04% |
| **95% Nominal** | Champion (`phase5_tuned_extra_trees`) | 0.7902 | **94.03%** | 1.5804 | -0.97% |
|  | Candidate (`candidate_v1_2_revalidated`) | 0.7788 | **96.02%** | 1.5576 | +1.02% |

### Conformal Uncertainty Finding:
Both models maintain empirical coverage comfortably exceeding the $90.0\%$ target level (Champion: $92.04\%$, Candidate: $91.04\%$) with virtually identical mean interval widths ($1.1884$ vs $1.1968$). Neither model demonstrates an uncertainty advantage on this cohort.

---

## 11. Score-Range Error Analysis

Partitioning the 201 target scores into 4 equal-width bins:

| Score Bin Range | Sample Size ($N$) | Champion MAE | Candidate MAE | Champion RMSE | Candidate RMSE |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **$[1.77, 3.42]$** | 18 | 0.2882 | 0.2811 | 0.3842 | 0.3621 |
| **$(3.42, 5.06]$** | 68 | 0.2641 | 0.2520 | 0.3891 | 0.3340 |
| **$(5.06, 6.70]$** | 82 | 0.2542 | 0.2441 | 0.3789 | 0.3182 |
| **$(6.70, 8.34]$** | 33 | 0.2711 | 0.2592 | 0.4981 | 0.3541 |

Across all four score bands, point MAE differences remain within $[0.007, 0.012]$ units. In the highest score range, Candidate exhibits lower RMSE due to Champion's single outlier residual.

---

## 12. Subgroup Descriptive Analysis

From [`ml/experiments/phase12_2_subgroup_analysis.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase12_2_subgroup_analysis.csv):

| Demographic Dimension | Category Group | $N$ | Champion MAE | Candidate MAE | Champion RMSE | Candidate RMSE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gender** | Female | 102 | 0.2682 | 0.2541 | 0.4121 | 0.3392 |
| **Gender** | Male | 99 | 0.2586 | 0.2462 | 0.4021 | 0.3265 |
| **Academic Level** | Graduate | 66 | 0.2612 | 0.2514 | 0.3992 | 0.3312 |
| **Academic Level** | High School | 68 | 0.2591 | 0.2482 | 0.4011 | 0.3291 |
| **Academic Level** | Undergraduate | 67 | 0.2701 | 0.2510 | 0.4212 | 0.3389 |
| **Stress Level** | High | 68 | 0.2694 | 0.2562 | 0.4152 | 0.3412 |
| **Stress Level** | Low | 66 | 0.2562 | 0.2451 | 0.3981 | 0.3241 |
| **Stress Level** | Moderate | 67 | 0.2650 | 0.2493 | 0.4082 | 0.3340 |

> **Governance Standard Notice:** Observed subgroup performance was similar within this evaluation sample. No formal fairness claim or conditional coverage guarantee is asserted.

---

## 13. Production Schema & Preprocessing Confirmation

- **Input Features:** Both models accept the exact canonical 12 survey feature schema.
- **Transformed Feature Dimensionality:**
  - Champion: **38 features** (`log1p + StandardScaler` on `Study_Hours`, `OrdinalEncoder` on `Stress_Level`, `OneHotEncoder(sparse=False)` on nominals).
  - Candidate: **35 features** (`RobustScaler` on `Study_Hours`, `OneHotEncoder(drop='first')` on all nominals).
- **Architecture Difference:** Candidate uses `drop='first'` on categorical dummies and 250 trees, while Champion uses ordinal encoding on stress and 500 trees. Both pipelines execute cleanly without inference error.

---

## 14. Evidence Interpretation & Evaluation Summary

| Evaluation Dimension | Empirical Evidence | Verdict |
| :--- | :--- | :--- |
| **RMSE & MAE Point Comparison** | Candidate RMSE $-0.0742$, Candidate MAE $-0.0133$ | Numerically Favors Candidate |
| **Median Absolute Error** | Champion Median AE lower by $+0.0096$ | Numerically Favors Champion |
| **Paired Record Error Split** | Champion wins on $57.21\%$ of records vs Candidate $42.79\%$ | Favors Champion |
| **Bootstrap 95% CI on $\Delta \text{MAE}$** | Crosses zero ($[-0.0401, +0.0103]$) | Not Statistically Conclusive |
| **Wilcoxon Signed-Rank Test** | $p = 0.1584 > 0.05$ | Not Statistically Significant |
| **Paired Permutation Test** | $p = 0.3033 > 0.05$ | Not Statistically Significant |
| **Conformal Prediction Intervals** | Both models achieve $\approx 91\%-92\%$ empirical 90% coverage | Indistinguishable Quality |
| **Overall Scientific Ruling** | Candidate is numerically better on outlier-sensitive metrics but statistically indistinguishable on typical records | **No Proven Superiority** |

---

## 15. Governance Decision

Under Section 16 of the Governance Decision Framework, the evidence warrants exactly one classification:

### **`A. CANDIDATE NUMERICALLY BETTER — NOT STATISTICALLY CONCLUSIVE`**

### Non-Negotiable Governance Directives:
1. **No Promotion Permitted:** Candidate v1.2 remains in `CHALLENGER / VALIDATING` status.
2. **Champion Retained:** Production Champion (`models/phase5_tuned_extra_trees.joblib`) remains the active model.
3. **No Retraining:** Automatic retraining remains strictly disabled.

---

## 16. Limitations

1. **Sample Size:** The Clean Common Evaluation Subset contains 201 records. While statistically sufficient for paired non-parametric tests, confidence intervals are wider than on 1,000-record cohorts.
2. **Survey Data Context:** Survey responses are observational and self-reported; findings reflect statistical correlation, not causal mechanisms.

---

## 17. Final Status & Summary Block

```
PHASE 12.2 STATUS:
    COMPLETE

Clean Common Evaluation Rows:      201

Champion Training Overlap:         0
Candidate Training Overlap:        0

Champion Evaluation Integrity:     PASS — CLEAN COMMON SUBSET
Candidate Evaluation Integrity:    PASS — CLEAN COMMON SUBSET

Champion R²:                       0.909767
Champion RMSE:                     0.407234
Champion MAE:                      0.263506

Candidate R²:                      0.939649
Candidate RMSE:                    0.333045
Candidate MAE:                     0.250220

Candidate vs Champion:
    Candidate Numerically Better (Outlier Variance Reduction)

Bootstrap Evidence:
    95% CI Crosses Zero [-0.040084, 0.010312] — Not Conclusive

Paired Statistical Evidence:
    Wilcoxon p=0.1584, Permutation p=0.3033 — Not Significant

Conformal Coverage:
    Both Models Satisfy Marginal Target Floor

Governance:
    Champion Modified = NO
    Champion Calibration Modified = NO
    Automatic Retraining = NO
    Automatic Promotion = NO
    Candidate Promotion = NO

Active Production Model:
    phase5_tuned_extra_trees

Candidate Status:
    CHALLENGER / VALIDATING
```
