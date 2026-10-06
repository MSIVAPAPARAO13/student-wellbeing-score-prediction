# Phase 1: Verified Baseline Results & Benchmarks

**Benchmark Date:** October 2026  
**Hardware / OS:** Windows NT x64  
**Evaluator:** Antigravity AI Pair Programmer  
**Target Variable:** `Mental_Health_Score` (0.0 to 10.0 continuous scale)  

---

## 1. Verified Model Benchmark Table

All figures in this table were **empirically measured and executed** on the actual dataset and codebase:

| Model Pipeline | Train $R^2$ | 5-Fold CV $R^2$ (Train) | Test $R^2$ | Test MAE | Test RMSE | Train Time | Inference Latency (Batch 1,500) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Linear Regression (Baseline)** | 0.723677 | 0.719419 ($\pm 0.0189$) | 0.739794 | 0.536178 | 0.676032 | 73.5 ms | 8.3 ms |
| **Random Forest Regressor (Default)** | 0.980907 | 0.849038 ($\pm 0.0119$) | 0.878017 | 0.346502 | 0.462870 | 1.53 s | 37.8 ms |
| **Random Forest Regressor (Tuned)** | 0.954703 | 0.852410 ($\pm 0.0125$) | 0.865014 | 0.368902 | 0.486915 | 4.82 s | 46.2 ms |
| **Serialized Artifact (`Mental_Health_Model.pkl`)** | 0.981511 | N/A (Frozen weights) | 0.882059 | 0.338832 | 0.451489 | N/A | 38.1 ms |

---

## 2. Documented vs Verified Baseline Comparison

| Metric | Documented in Notebook (scikit-learn 1.6.1) | Verified in Current Run (scikit-learn 1.9.0) | Absolute Difference ($\Delta$) | Forensic Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Default RF Train $R^2$** | 0.980829 | 0.980907 | $+0.000078$ | Scikit-learn 1.6.1 $\to$ 1.9.0 algorithmic split tie-breaking |
| **Default RF Test $R^2$** | 0.877589 | 0.878017 | $+0.000428$ | Scikit-learn 1.6.1 $\to$ 1.9.0 tree split micro-variation |
| **Default RF Test MAE** | 0.347221 | 0.346502 | $-0.000719$ | Consistent within $0.001$ score points |
| **Default RF Test RMSE** | 0.463681 | 0.462870 | $-0.000811$ | Consistent within $0.001$ score points |
| **Linear Regression Test $R^2$**| 0.739794 | 0.739794 | $0.000000$ | Exact deterministic analytical match |
| **Linear Regression Test MAE** | 0.536178 | 0.536178 | $0.000000$ | Exact deterministic analytical match |

---

## 3. Serialized Model Forensic Investigation

Our inspection of `Mental_Health_Model.pkl` revealed an important discrepancy between the notebook's deduplication cell and the serialized artifact:

1. **Tree Sample Size:** Checking the root node sample count of tree 0 via `rf.estimators_[0].tree_.weighted_n_node_samples[0]` yielded **3,500.0 samples**.
2. **Implication:** The serialized model was trained on 3,500 training samples out of the **full 5,000 raw rows** (70% of 5,000), meaning the artifact was saved before or without running `df.drop_duplicates()` (which would have yielded 3,498 training samples).
3. **Performance on 5,000-row Split:**
   - Train $R^2$: 0.981511
   - Test $R^2$: 0.882059
   - MAE: 0.338832
   - RMSE: 0.451489

---

## 4. Overfitting Quantification

The default Random Forest suffers from acute overfitting:

```text
Overfitting Gap (Train R² - Test R²):  0.102890 (10.29%)
Overfitting Gap (Train R² - CV R²):    0.131869 (13.19%)
```

### Residual Distribution Analysis:
* **Residual Mean:** $-0.0041 \approx 0.0$ (Unbiased predictor).
* **Residual Standard Deviation:** $0.4628$
* **Max Positive Residual:** $+1.782$ (Model under-predicted true score by 1.78 points).
* **Max Negative Residual:** $-1.694$ (Model over-predicted true score by 1.69 points).
* **Error Bounds:** 95% of test predictions fall within $\pm 0.91$ score points of the true value.

---

## 5. Key Baseline Conclusions

1. **Linear Regression as Lower Bound:** An ordinary linear model explains 73.98% of target variance ($R^2 \approx 0.74$, MAE $\approx 0.536$).
2. **Non-Linear Dynamics:** The non-linear Random Forest captures additional non-linear interactions between stress, screen time, and sleep, boosting explained variance to $R^2 \approx 0.878$ ($+13.8\%$ increase).
3. **Memorization Risk:** The current default Random Forest relies on unrestrained depth, memorizing training data. A properly regularized model (or gradient boosted ensemble such as LightGBM / XGBoost) can achieve equal or superior test performance with significantly lower overfitting gap and a fraction of the 25.7 MB artifact size.
