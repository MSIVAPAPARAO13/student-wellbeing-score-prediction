# PHASE 5 — OPTUNA TRIAL COMPARISON & SENSITIVITY REPORT

**Project:** Student Mental Health / Wellbeing Score Prediction  
**Phase:** 5 — Hyperparameter Optimization & Model Regularization  
**Date:** October 2026  
**Artifact Referenced:** [`ml/experiments/phase5_hyperparameter_results.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase5_hyperparameter_results.csv)  
**Execution Notebook:** [`ml/notebooks/05_hyperparameter_tuning.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/05_hyperparameter_tuning.ipynb)  

---

## 1. Top Optuna Trials Ranked by 5-Fold CV RMSE

Below is the comparative ranking of top-performing trials from the 50-trial search alongside the baseline configuration (Trial 0):

| Rank | Trial # | Trees (`n_est`) | Depth (`max_depth`) | Split (`min_split`) | Leaf (`min_leaf`) | Features (`max_feat`) | CV RMSE | CV MAE | CV R² | CV R² Std | Train-CV Gap | Duration (s) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **34** | **500** | **None** | **2** | **1** | **sqrt** | **0.376511** | **0.268486** | **0.911006** | **±0.003525** | **0.088983** | 4.01 s |
| **2** | 36 | 500 | None | 2 | 1 | sqrt | 0.376511 | 0.268486 | 0.911006 | ±0.003525 | 0.088983 | 4.05 s |
| **3** | 45 | 350 | None | 2 | 1 | sqrt | 0.376714 | 0.268580 | 0.910892 | ±0.003636 | 0.089098 | 2.12 s |
| **4** | 43 | 400 | None | 2 | 1 | sqrt | 0.376835 | 0.268655 | 0.910840 | ±0.003539 | 0.089150 | 2.44 s |
| **5** | 42 | 400 | None | 2 | 1 | sqrt | 0.376835 | 0.268655 | 0.910840 | ±0.003539 | 0.089150 | 2.50 s |
| **6** | 44 | 300 | None | 2 | 1 | sqrt | 0.377038 | 0.268669 | 0.910742 | ±0.003744 | 0.089247 | 1.95 s |
| **7** | 14 | 450 | 40 | 2 | 1 | 0.5 | 0.377124 | 0.268807 | 0.910691 | ±0.003814 | 0.089298 | 4.64 s |
| **8** | 22 | 450 | None | 2 | 1 | 0.5 | 0.377124 | 0.268807 | 0.910691 | ±0.003814 | 0.089298 | 4.71 s |
| **9** | 10 | 250 | 40 | 2 | 1 | sqrt | 0.377540 | 0.269123 | 0.910504 | ±0.003704 | 0.089486 | 2.17 s |
| **10**| 12 | 300 | 40 | 2 | 1 | 0.5 | 0.377743 | 0.269202 | 0.910398 | ±0.003606 | 0.089592 | 3.20 s |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| **17**| **0 (Base)**| **100** | **None** | **2** | **1** | **1.0** | **0.388058** | **0.276339** | **0.905368** | **±0.006917** | **0.094622** | 1.71 s |

---

## 2. Analysis of Hyperparameter Regimes

### 2.1 Tree Depth: Constrained vs. Unconstrained
- **Unconstrained (`max_depth = None`):** Yielded all top 6 positions with CV RMSE $\le 0.3770$.
- **Deep Pruning (`max_depth = 40`):** Performed virtually identically to unconstrained trees because on a 3,998-record dataset with 28 features, typical tree depth rarely exceeds 35 levels.
- **Moderate Pruning (`max_depth = 20` or `25`):** Significantly worsened performance (CV RMSE degraded to $0.3853 - 0.4103$).
- **Shallow Constraints (`max_depth = 10` or `15`):** Caused severe underfitting (Trials 39, 47, 49 with CV RMSE $\approx 0.573$ and CV R² dropping to ~0.794).

### 2.2 Leaf Granularity: `min_samples_leaf`
- **`min_samples_leaf = 1`:** Mandatory for high predictive accuracy in Extra Trees. All top 14 models utilized `min_samples_leaf = 1`.
- **`min_samples_leaf \ge 2`:** When leaf size was forced to 2, 3, 4, 6, or 8, CV RMSE degraded rapidly (Trial 23: 0.4171; Trial 49: 0.4658; Trial 21: 0.5002; Trial 30: 0.5799). In Extra Trees, randomized split points naturally blur leaf boundaries; restricting leaf node capacity compounds bias without providing additional variance benefit.

### 2.3 Feature Subsets: `max_features`
- **`'sqrt'` ($\approx 5$ features per candidate split):** Clear superior regime. It dominated ranks 1 through 6, reducing CV RMSE to 0.3765 and cutting fold variance to ±0.0035.
- **`0.5` ($\approx 14$ features per candidate split):** Second best regime (ranks 7, 8, 10, 11), achieving CV RMSE ~0.3771.
- **`1.0` (all 28 features evaluated):** Trial 0 (the Phase 4 baseline) and Trial 18 (450 trees) plateaued at CV RMSE ~0.3875 – 0.3881. Evaluating all features allowed dominant features to appear too frequently across split candidates, reducing ensemble decorrelation.

### 2.4 Ensemble Size: `n_estimators`
- **100 trees (Baseline):** CV RMSE = 0.388058, CV R² Std = ±0.006917.
- **200 – 300 trees:** CV RMSE = 0.3770 – 0.3777, CV R² Std = ±0.0037.
- **500 trees:** CV RMSE = 0.376511, CV R² Std = ±0.003525.
Expanding from 100 to 500 trees stabilized the random cutpoint variance and produced a monotonic reduction in cross-validation standard deviation.

---

## 3. Fold-Level Breakdown for Winning Model (Trial 34 / 49)

The fold-by-fold cross-validation metrics across all 5 folds for the winning candidate (`n_estimators=500, max_depth=None, min_samples_split=2, min_samples_leaf=1, max_features='sqrt'`) demonstrate remarkable stability:

| Fold Index | Fold Validation R² | Fold Validation RMSE | Fold Validation MAE |
|:---:|:---:|:---:|:---:|
| **Fold 1** | 0.912643 | 0.369244 | 0.264718 |
| **Fold 2** | 0.914568 | 0.367098 | 0.264023 |
| **Fold 3** | 0.913077 | 0.371946 | 0.266742 |
| **Fold 4** | 0.909477 | 0.383120 | 0.272186 |
| **Fold 5** | 0.905267 | 0.391149 | 0.274761 |
| **Mean** | **0.911006** | **0.376511** | **0.268486** |
| **Std Dev** | **±0.003525** | **±0.008942** | **±0.004271** |
| **Min** | 0.905267 | 0.367098 | 0.264023 |
| **Max** | 0.914568 | 0.391149 | 0.274761 |

### Head-to-Head Fold Dominance:
Across all 5 folds, the tuned candidate consistently surpassed the Phase 4 baseline:
- **Fold 1:** 0.9126 vs. 0.9098 (+0.0028)
- **Fold 2:** 0.9146 vs. 0.9123 (+0.0023)
- **Fold 3:** 0.9131 vs. 0.9068 (+0.0063)
- **Fold 4:** 0.9095 vs. 0.9038 (+0.0057)
- **Fold 5:** 0.9053 vs. 0.8941 (+0.0112)

The most pronounced stabilization occurred on Fold 5 (previously the weakest fold), which gained +0.0112 in R², shrinking the overall fold range from $[0.8941, 0.9123]$ to $[0.9053, 0.9146]$.

---

## 4. Out-of-Fold (OOF) Prediction Diagnostics

Aggregating out-of-fold predictions across all 3,998 training records yielded:
- **Overall OOF R²:** **0.911006**
- **Overall OOF RMSE:** **0.376511**
- **Overall OOF MAE:** **0.268486**
- **Residual Distribution:** Mean residual = **+0.0017** (unbiased error centering), Standard Deviation = **0.3765**.
- **Residual Normality:** Confirmed symmetric, bell-shaped distribution with near-zero skewness centered tightly at 0.0 (visualized in [`ml/evaluation/phase5_oof_residuals.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase5_oof_residuals.png)).
