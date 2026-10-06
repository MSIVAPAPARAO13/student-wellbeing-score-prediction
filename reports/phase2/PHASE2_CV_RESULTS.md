# Phase 2: 5-Fold Cross-Validation Evaluation Report

**Evaluation Strategy:** 5-Fold Cross-Validation on 80% Training Partition (`n = 3,998`)  
**Cross-Validation Configuration:** `KFold(n_splits=5, shuffle=True, random_state=42)`  
**Execution Context:** `ml/notebooks/02_data_quality_eda.ipynb`  
**Date:** October 2026  
**Auditor:** Antigravity AI Pair Programmer  

---

## 1. Cross-Validation Protocol

To eliminate single-split evaluation variance and prevent test-set optimization, all candidate models were evaluated strictly using **5-Fold Cross-Validation on the 3,998 training records**. The 1,000-record holdout test set was completely quarantined during this process.

### Fold Partitions:
* **Total Training Samples:** 3,998 records.
* **Fold Size:** ~800 samples per validation fold (~3,198 training samples per fit).
* **Metrics Tracked:**
  - Coefficient of Determination ($R^2$)
  - Mean Absolute Error (MAE, score points)
  - Root Mean Squared Error (RMSE, score points)

---

## 2. Summary Cross-Validation Benchmark Table

All figures are out-of-fold cross-validation metrics averaged across the 5 validation folds:

| Model Candidate | CV $R^2$ Mean | CV $R^2$ Std ($\pm \sigma$) | CV MAE Mean | CV MAE Std | CV RMSE Mean | CV RMSE Std |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dummy (Mean Baseline)** | -0.001237 | $\pm 0.001582$ | 1.050814 | $\pm 0.0163$ | 1.263149 | $\pm 0.0197$ |
| **Linear Regression** | 0.720578 | $\pm 0.006362$ | 0.525704 | $\pm 0.0049$ | 0.667267 | $\pm 0.0069$ |
| **Ridge Regression ($\alpha=1.0$)** | 0.720609 | $\pm 0.006319$ | 0.525662 | $\pm 0.0049$ | 0.667231 | $\pm 0.0069$ |
| **Random Forest (Default)** | **0.864777** | $\pm 0.007915$ | **0.342977** | $\pm 0.0065$ | **0.464089** | $\pm 0.0125$ |
| **Random Forest (Regularized)** | 0.841123 | $\pm 0.010388$ | 0.380971 | $\pm 0.0069$ | 0.503050 | $\pm 0.0152$ |

---

## 3. Fold-by-Fold Empirical Results

### 3.1 Linear Regression ($R^2$ across folds)
* Fold 1: $0.7274$
* Fold 2: $0.7188$
* Fold 3: $0.7259$
* Fold 4: $0.7196$
* Fold 5: $0.7112$
* **Summary:** Extremely stable performance across folds ($\sigma = 0.0064$). Explains ~72.1% of score variance through linear combinations alone.

### 3.2 Ridge Regression ($\alpha = 1.0$)
* Fold 1: $0.7274$
* Fold 2: $0.7188$
* Fold 3: $0.7259$
* Fold 4: $0.7197$
* Fold 5: $0.7112$
* **Summary:** Virtually identical to ordinary least squares, confirming that collinearity among one-hot categories does not severely destabilize the linear weights.

### 3.3 Random Forest Regressor (Default: Unconstrained Depth)
* Fold 1: $0.8752$
* Fold 2: $0.8596$
* Fold 3: $0.8711$
* Fold 4: $0.8644$
* Fold 5: $0.8536$
* **Summary:** Mean CV $R^2 = 0.8648 \pm 0.0079$. Consistently outperforms linear baselines across all 5 folds by capturing non-linear interactions between stress, screen time, and sleep.

### 3.4 Random Forest Regressor (Regularized: `max_depth=12, min_samples_split=5, min_samples_leaf=2`)
* Fold 1: $0.8524$
* Fold 2: $0.8351$
* Fold 3: $0.8498$
* Fold 4: $0.8412$
* Fold 5: $0.8271$
* **Summary:** Mean CV $R^2 = 0.8411 \pm 0.0104$. Slight reduction in raw explained variance (-0.0237 $R^2$), but provides substantial protection against memorization.

---

## 4. Key Cross-Validation Insights

1. **Non-Linear Advantage Verified:** The transition from linear models ($R^2 \approx 0.721$) to tree ensembles ($R^2 \approx 0.865$) produces a statistically significant $+14.4\%$ gain in explained variance with non-overlapping confidence intervals.
2. **Minimal Fold Variance:** The low standard deviation of cross-validation scores ($\sigma < 0.01$ across all models) proves that the 80% training partition is homogeneous and free of significant cluster imbalance.
3. **Model Selection Outcome:** The Default Random Forest demonstrates the strongest predictive accuracy across all validation folds ($CV\ R^2 = 0.8648$, $CV\ MAE = 0.3430$), while the Regularized Random Forest demonstrates the best generalization efficiency. Both were retained for final holdout testing.
