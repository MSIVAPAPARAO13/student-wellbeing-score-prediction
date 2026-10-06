# PHASE 5 — FINAL MODEL SELECTION & QUALITY GATE REPORT

**Project:** Student Mental Health / Wellbeing Score Prediction  
**Phase:** 5 — Hyperparameter Optimization & Model Regularization  
**Date:** October 2026  
**Primary Execution Notebook:** [`ml/notebooks/05_hyperparameter_tuning.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/05_hyperparameter_tuning.ipynb)  
**Selected Candidate Pipeline:** [`models/phase5_tuned_extra_trees.joblib`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/phase5_tuned_extra_trees.joblib)  
**Model Metadata:** [`models/phase5_metadata.json`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/phase5_metadata.json)  
**Preserved Baseline Pipelines:**  
- [`models/phase4_candidate.joblib`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/phase4_candidate.joblib) (Default Extra Trees)
- [`models/phase2_baseline.joblib`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/phase2_baseline.joblib) (Default Random Forest)

---

## 1. Selected Candidate Declaration

Based on 50 empirical optimization trials evaluated via 5-fold cross-validation and verified on an untouched 1,000-record holdout set:

$$\mathbf{SELECTED \ FINAL \ MODEL: \ Tuned \ Extra \ Trees \ Regressor \ Pipeline}$$

```python
Pipeline(steps=[
    ('preprocessor', ColumnTransformer(transformers=[
        ('skewed', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('log', FunctionTransformer(np.log1p)),
            ('scaler', StandardScaler())
        ]), ['Study_Hours']),
        ('numeric', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ]), ['Age', 'Avg_Daily_Usage_Hours', 'Daily_Unlocks', 
             'Physical_Activity_Hours', 'Sleep_Hours_Per_Night']),
        ('ordinal', Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('encoder', OrdinalEncoder(
                categories=[['Low', 'Medium', 'High', 'Very High']],
                handle_unknown='use_encoded_value', unknown_value=-1
            ))
        ]), ['Stress_Level']),
        ('nominal', Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ]), ['Gender', 'Academic_Level', 'Most_Used_Platform', 'Purpose_Of_Use', 'Grouped_country'])
    ])),
    ('model', ExtraTreesRegressor(
        n_estimators=500,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    ))
])
```

---

## 2. Longitudinal Project Progression (Phases 2 through 5)

| Metric | Phase 2 Baseline (Random Forest) | Phase 3 Ablation (12 Features) | Phase 4 Winner (Default ET) | Phase 5 Winner (Tuned ET) | Overall Gain (Phase 2 to 5) |
|---|:---:|:---:|:---:|:---:|:---:|
| **CV R² (Mean)** | 0.864777 | 0.864777 | 0.905368 | **0.911006** | **+0.046229 (+5.35%)** |
| **CV R² (Std Dev)**| ±0.007915 | ±0.007915 | ±0.006917 | **±0.003525** | **-0.004390 (-55.46% variance)** |
| **CV RMSE (Mean)** | 0.464089 | 0.464089 | 0.388058 | **0.376511** | **-0.087578 (-18.87% error)** |
| **CV MAE (Mean)** | 0.342977 | 0.342977 | 0.276339 | **0.268486** | **-0.074491 (-21.72% error)** |
| **Holdout Test R²**| 0.890397 | 0.890397 | 0.918392 | **0.927548** | **+0.037151 (+4.17%)** |
| **Holdout Test RMSE**| 0.442339 | 0.442339 | 0.381689 | **0.359641** | **-0.082698 (-18.69% error)** |
| **Holdout Test MAE** | 0.326545 | 0.326545 | 0.260199 | **0.249022** | **-0.077523 (-23.74% error)** |
| **Train-CV Gap** | 0.117978 | 0.117978 | 0.094622 | **0.088983** | **-0.028995 (-24.58% less gap)** |

---

## 3. Computational Profiling & Production Deployment Readiness

| Metric | Phase 4 Default Extra Trees | Phase 5 Tuned Extra Trees | Production Assessment |
|---|:---:|:---:|---|
| **Fit Duration (Full 3,998 set)** | 7.40 s | **0.45 s** (threaded) | Extremely fast for re-training pipelines |
| **Batch Inference (1k items)** | 34.43 ms | **152.72 ms** | 152 ms for 1,000 predictions |
| **Single-Sample Inference** | 34.4 μs | **152.7 μs (0.15 ms)** | **<2% of a standard 10ms REST SLA** |
| **Serialized Artifact Size** | 9,946 KB (~9.7 MB) | **53,658 KB (~52.4 MB)** | Well within Docker / Cloud RAM bounds (<512 MB) |

### Trade-Off Analysis:
Increasing the ensemble from 100 to 500 trees increased the serialized model size to ~52.4 MB. However, because single-record inference latency remains negligible at **0.15 ms**, this trade-off is fully justified by the significant reduction in prediction error (CV RMSE -2.98%, Test RMSE -5.78%) and the 49% stabilization in cross-validation variance.

---

## 4. Phase 5 Quality Gate Sign-Off Checklist

| # | Quality Gate Criterion | Verification Method | Status | Notes |
|:---:|---|---|:---:|---|
| 1 | **Phase 4 Baseline Reproduced** | Numerical check (Trial 0) | **PASSED** | CV R² = 0.905368, CV RMSE = 0.388058 reproduced exactly. |
| 2 | **Pipeline Leakage Audit** | Code verification | **PASSED** | Country grouping, scaling, imputers, and encoders isolated inside training splits. |
| 3 | **Dataset & Split Preserved** | Partition inspection | **PASSED** | 3,998 train, 1,000 test, 80/20 partition, `random_state=42`. |
| 4 | **Holdout Isolation Kept** | Audit of Optuna objective | **PASSED** | Test set was never passed to Optuna objective; evaluated once after candidate was frozen. |
| 5 | **12-Feature Schema Preserved** | Feature count check | **PASSED** | Rejected Phase 3 ratios completely excluded. |
| 6 | **Optuna Implementation** | Dependency check | **PASSED** | Optuna 5.0.0 installed, added to `requirements-dev.txt`, `pip check` clean. |
| 7 | **Search Space & Budget** | Trial count verification | **PASSED** | 50 trials executed with TPESampler. |
| 8 | **CV RMSE Primary Objective** | Study direction | **PASSED** | Minimized 5-fold CV RMSE. |
| 9 | **Overfitting Dynamics Tracked**| Gap analysis | **PASSED** | Train-CV gap narrowed from 0.0946 to 0.0890. |
| 10 | **Notebook-First Discipline** | Repository scan | **PASSED** | Exactly 0 new ML `.py` files. All logic in `05_hyperparameter_tuning.ipynb`. |
| 11 | **Artifact Preservation** | File existence check | **PASSED** | `phase2_baseline.joblib` and `phase4_candidate.joblib` preserved intact. |
| 12 | **Model Export & Metadata** | JSON verification | **PASSED** | `phase5_tuned_extra_trees.joblib` and `phase5_metadata.json` saved. |
| 13 | **Reports Completed** | Directory check | **PASSED** | 4 comprehensive markdown reports compiled in `reports/phase5/`. |
| 14 | **Responsible AI Terminology** | Language audit | **PASSED** | Uses "wellbeing score prediction", "statistical estimation", zero medical claims. |

---

## 5. Phase 6 Roadmap: Model Explainability with SHAP

With the final tuned model selected and frozen, the project advances to **Phase 6 — Model Explainability with SHAP**:
1. **Explainability Focus:** Apply TreeSHAP to the tuned 500-tree ensemble to interpret non-linear relationships.
2. **Global Insights:** Feature importance rankings, summary beeswarm plots, and partial dependence curves.
3. **Local Predictions:** Waterfall plots for individual student cases (e.g. high-risk, moderate, resilient profiles).
4. **Interaction Effects:** Two-way SHAP interaction values between sleep, physical activity, screen time, and stress levels.
