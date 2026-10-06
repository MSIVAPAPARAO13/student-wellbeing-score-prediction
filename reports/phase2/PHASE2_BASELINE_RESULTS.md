# Phase 2: Verified Baseline Results & Overfitting Benchmark

**Benchmark Scope:** Final Holdout Test Evaluation & Cross-Phase Comparative Analysis  
**Holdout Set:** 20% Clean Dataset (`n = 1,000`, strictly untouched until evaluation)  
**Execution Context:** `ml/notebooks/02_data_quality_eda.ipynb`  
**Date:** October 2026  
**Auditor:** Antigravity AI Pair Programmer  

---

## 1. Verified Holdout Benchmark Table

All figures are empirically measured on the 1,000 holdout test samples:

| Model Candidate | Train $R^2$ | CV $R^2$ Mean (5-Fold) | Test $R^2$ | Test MAE | Test RMSE | Train-Test $R^2$ Gap | Train-CV $R^2$ Gap |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dummy (Mean Baseline)** | 0.000000 | -0.001237 | -0.000594 | 1.127571 | 1.336514 | +0.000594 | +0.001237 |
| **Linear Regression** | 0.725567 | 0.720578 | 0.742813 | 0.533889 | 0.677593 | -0.017246 | +0.004990 |
| **Ridge Regression ($\alpha=1.0$)** | 0.725563 | 0.720609 | 0.742845 | 0.533846 | 0.677551 | -0.017281 | +0.004954 |
| **Random Forest (Default)** | **0.982755** | **0.864777** | **0.890397** | **0.326545** | **0.442339** | **+0.092357 (9.24%)** | **+0.117978 (11.80%)** |
| **Random Forest (Regularized)** | 0.931164 | 0.841123 | 0.864058 | 0.374589 | 0.492630 | +0.067105 (6.71%) | +0.090040 (9.00%) |

---

## 2. Comparative Analysis: Phase 1 vs Phase 2

| Dimension / Metric | Phase 1 (Original Implementation) | Phase 2 (Leakage-Free Verified) | Delta / Shift Analysis |
| :--- | :--- | :--- | :--- |
| **Partition Split Ratio** | 70% Train / 30% Test | **80% Train / 20% Test** | Increased training cohort by 498 samples. |
| **Training Records ($N_{train}$)**| 3,500 (Un-deduplicated) | **3,998 (Deduplicated)** | Deduplicated clean training data. |
| **Test Records ($N_{test}$)** | 1,500 samples | **1,000 samples** | More compact, strictly isolated test set. |
| **Country Grouping Leakage** | **CONFIRMED LEAKAGE** | **COMPLETELY ELIMINATED** | Country frequencies derived strictly from $N_{train}$. |
| **Preprocessing Imputers** | Absent (Failed documentation claim) | **Explicit SimpleImputers Added** | Defensive production safeguard against runtime nulls. |
| **Validation Protocol** | Single holdout split only | **5-Fold Cross-Validation on Train** | Provides variance bounds ($\pm \sigma$) for model selection. |
| **Linear Regression Test $R^2$** | 0.739794 | **0.742813** | Consistent baseline ($+0.0030$). |
| **Linear Regression Test MAE** | 0.536178 | **0.533889** | Identical error magnitude within 0.002 points. |
| **Default RF Test $R^2$** | 0.878017 | **0.890397** | $+0.0124$ gain from larger training cohort ($N=3,998$). |
| **Default RF Test MAE** | 0.346502 | **0.326545** | Average error reduced from 0.347 to 0.327 points. |
| **Default RF Test RMSE** | 0.462870 | **0.442339** | Root mean square error improved from 0.463 to 0.442. |

> **Scientific Caution:** The improvement in Test $R^2$ from 0.878 to 0.890 must **not** be attributed to superior model complexity. It is primarily the direct mathematical consequence of training on 3,998 samples instead of 3,500, combined with duplicate removal and test partition re-sampling.

---

## 3. Overfitting & Regularization Findings

### Default Random Forest:
* **Train $R^2$:** 0.982755 (Nearly complete memorization).
* **Test $R^2$:** 0.890397.
* **Train-Test Gap:** **9.24%**.
* **Train-CV Gap:** **11.80%**.
* **Diagnosis:** Unconstrained depth (`max_depth=None`, `min_samples_leaf=1`) creates excessive memorization.

### Regularized Random Forest (`max_depth=12, min_samples_split=5, min_samples_leaf=2`):
* **Train $R^2$:** 0.931164.
* **Test $R^2$:** 0.864058.
* **Train-Test Gap:** **6.71%** (Reduced by 2.53 percentage points).
* **Train-CV Gap:** **9.00%** (Reduced by 2.80 percentage points).
* **Diagnosis:** Constraining tree depth and leaf size successfully curbs memorization while retaining strong predictive power ($R^2 > 0.86$). This demonstrates the clear pathway for Phase 4 hyperparameter optimization.

---

## 4. Residual & Error Analysis (Holdout Test Set)

Computed on the 1,000 holdout predictions from the Default Random Forest:

* **Residual Mean ($\bar{e}$):** $+0.0089$ ($\approx 0.0$, statistically unbiased).
* **Residual Standard Deviation ($\sigma_e$):** $0.4423$.
* **Maximum Over-Prediction:** $-1.4116$ score points (Predicted 7.81 for a true score of 6.40).
* **Maximum Under-Prediction:** $+1.7371$ score points (Predicted 6.16 for a true score of 7.90).
* **Error Bounds:** Exactly **95.2% of test predictions** fall within $\pm 0.87$ score points of the true value.
* **Residual Normality:** Visualized histogram confirms a symmetric, bell-shaped Gaussian distribution centered tightly at zero error.

---

## 5. Artifacts Created & Exported

1. **Lightweight Experiment Results:** [`ml/experiments/phase2_baseline_results.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase2_baseline_results.csv) (876 bytes).
2. **Phase 2 Baseline Model Artifact:** [`models/phase2_baseline.joblib`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/phase2_baseline.joblib) (29.2 MB complete Scikit-learn Pipeline with ColumnTransformer, SimpleImputers, Scalers, Encoders, and Random Forest).
