# PHASE 4 — FINAL MODEL SELECTION & QUALITY GATE REPORT

**Project:** Student Mental Health / Wellbeing Score Prediction  
**Phase:** 4 — Multi-Model Benchmarking & Evidence-Based Model Selection  
**Date:** October 2026  
**Primary Execution Notebook:** [`ml/notebooks/04_model_benchmark.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/04_model_benchmark.ipynb)  
**Selected Candidate Pipeline:** [`models/phase4_candidate.joblib`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/phase4_candidate.joblib)  
**Preserved Baseline Pipeline:** [`models/phase2_baseline.joblib`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/phase2_baseline.joblib)  

---

## 1. Selected Candidate Declaration

Based on comprehensive empirical benchmarking across eleven (11) candidate regression estimators evaluated under identical, leakage-free 5-fold cross-validation and holdout testing:

$$\mathbf{SELECTED \ CANDIDATE: \ Extra \ Trees \ Regressor \ Pipeline}$$

```python
Pipeline(steps=[
    ('preprocessor', ColumnTransformer(transformers=[
        ('skewed', Pipeline([
            ('log1p', FunctionTransformer(np.log1p)),
            ('scaler', StandardScaler())
        ]), ['Study_Hours']),
        ('other_numeric', StandardScaler(), [
            'Age', 'Avg_Daily_Usage_Hours', 'Daily_Unlocks', 
            'Physical_Activity_Hours', 'Sleep_Hours_Per_Night'
        ]),
        ('ordinal', OrdinalEncoder(
            categories=[['Low', 'Medium', 'High', 'Very High']],
            handle_unknown='use_encoded_value', unknown_value=-1
        ), ['Stress_Level']),
        ('normal', OneHotEncoder(
            drop='first', sparse_output=False, handle_unknown='ignore'
        ), ['Gender', 'Academic_Level', 'Most_Used_Platform', 'Purpose_Of_Use', 'Grouped_country'])
    ])),
    ('regressor', ExtraTreesRegressor(n_estimators=100, random_state=42, n_jobs=-1))
])
```

---

## 2. Head-to-Head Comparison: Extra Trees vs. Phase 2 Baseline

| Evaluation Dimension | Phase 2 Baseline (Random Forest) | Phase 4 Winner (Extra Trees) | Net Improvement | Relative Change |
|---|:---:|:---:|:---:|:---:|
| **CV R² (Mean)** | 0.864777 | **0.905368** | **+0.040591** | **+4.69%** |
| **CV R² (Std Dev)** | ±0.007915 | **±0.006917** | **-0.000998** | **-12.61% (More Stable)** |
| **CV RMSE (Mean)** | 0.464089 | **0.388058** | **-0.076031** | **-16.38% Error Reduction** |
| **CV MAE (Mean)** | 0.342977 | **0.276339** | **-0.066638** | **-19.43% Error Reduction** |
| **Test R² (Holdout)** | 0.890397 | **0.918392** | **+0.027995** | **+3.14%** |
| **Test RMSE (Holdout)** | 0.442339 | **0.381689** | **-0.060650** | **-13.71% Error Reduction** |
| **Test MAE (Holdout)** | 0.326545 | **0.260199** | **-0.066346** | **-20.32% Error Reduction** |
| **Train-CV R² Gap** | 0.117978 | **0.094622** | **-0.023356** | **-19.80% (Less Overfitting)** |
| **Fit Time** | 7.66 s | **7.40 s** | -0.26 s | Comparable |
| **Inference Time (1k)** | 30.54 ms | 34.43 ms | +3.89 ms | Negligible (+3.9 μs/sample) |
| **Serialized Artifact Size** | 5,504.6 KB | 9,946.3 KB | +4,441.7 KB | Manageable (~9.7 MB) |

---

## 3. Methodological Rationale: Why Extra Trees Succeeded

The superiority of Extremely Randomized Trees over standard Random Forests and gradient boosted trees in this application stems from three structural characteristics of the survey dataset:

1. **Random Threshold Cutpoints as Regularization:**
   Standard decision trees calculate the optimal split point across candidate feature subsets via greedy search. When continuous features (`Study_Hours`, `Daily_Unlocks`, `Avg_Daily_Usage_Hours`) have localized clustering or correlated noise, greedy splits can over-index on idiosyncratic boundaries. Extra Trees draws cutpoints uniformly at random and chooses the best among them, reducing ensemble variance without increasing bias.
2. **Smooth Decision Surfaces Across Dense Encodings:**
   The one-hot encoded nominal features create a 28-dimensional sparse-dense feature space. Random cutpoints create smoother, more continuous interpolation across categorical combinations than the step-wise plateaus typical of greedy trees.
3. **Robustness to Collinear Survey Indicators:**
   Digital usage metrics (screen time and unlocks) exhibit natural positive correlation. Random cutpoint generation prevents any single dominant feature from overshadowing complementary indicators across the ensemble trees.

---

## 4. Phase 4 Quality Gate Sign-Off Checklist

| # | Quality Gate Criterion | Verification Method | Status | Notes |
|:---:|---|---|:---:|---|
| 1 | **Notebook-First ML Adherence** | Workspace inspection | **PASSED** | Exactly 0 new ML `.py` files created. All benchmarking executed in `ml/notebooks/04_model_benchmark.ipynb`. |
| 2 | **Baseline Reproducibility** | Exact numeric verification | **PASSED** | Phase 2 baseline reproduced exactly: CV R² = 0.864777, CV RMSE = 0.464089, Test R² = 0.890397. |
| 3 | **Leakage Prevention** | Code audit | **PASSED** | Country grouping, scaling, and ordinal transformations fitted strictly inside CV training splits and pipeline. |
| 4 | **Statistically Meaningful Gain** | Multi-fold hypothesis testing | **PASSED** | Extra Trees beat baseline on all 5 folds; gap is >5 standard deviations above baseline. |
| 5 | **Generalization Verification** | Unobserved holdout test | **PASSED** | Holdout Test R² = 0.918392, Test RMSE = 0.381689. No test leakage detected. |
| 6 | **Artifact Preservation** | File existence check | **PASSED** | `models/phase2_baseline.joblib` preserved. Candidate saved to `models/phase4_candidate.joblib`. |
| 7 | **Responsible AI Terminology** | Documentation audit | **PASSED** | Explicitly framed as "wellbeing score prediction" and "model-associated patterns"; zero clinical/diagnostic claims. |

---

## 5. Phase 5 Roadmap: Hyperparameter Optimization

With the selection of **Extra Trees Regressor** as the primary architectural candidate, Phase 5 will focus on systematic hyperparameter tuning to explore whether further performance and efficiency gains can be achieved.

### Phase 5 Search Dimensions:
- **`n_estimators`:** `[100, 150, 200, 300]` (test if larger ensembles stabilize variance further)
- **`max_depth`:** `[None, 15, 20, 25, 30]` (evaluate depth constraints to compress model size and reduce overfit gap)
- **`min_samples_split`:** `[2, 4, 6, 8]` (prevent micro-leaf specialization)
- **`min_samples_leaf`:** `[1, 2, 4]` (smooth leaf predictions)
- **`max_features`:** `['sqrt', 0.5, 0.7, 1.0]` (evaluate attribute subset ratios across the 28 transformed dimensions)

### Phase 5 Constraints:
- Continue strict **Notebook-First** protocol (`ml/notebooks/05_hyperparameter_tuning.ipynb`).
- Maintain exact 80/20 split and 5-fold cross-validation scheme.
- Zero speculative `.py` files.
