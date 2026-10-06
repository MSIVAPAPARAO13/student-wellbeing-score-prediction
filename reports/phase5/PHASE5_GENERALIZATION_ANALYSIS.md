# PHASE 5 — GENERALIZATION & OVERFITTING DYNAMICS REPORT

**Project:** Student Mental Health / Wellbeing Score Prediction  
**Phase:** 5 — Hyperparameter Optimization & Model Regularization  
**Date:** October 2026  
**Artifact Referenced:** [`models/phase5_metadata.json`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/phase5_metadata.json)  
**Visualization:** [`ml/evaluation/phase5_train_vs_cv_gap.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase5_train_vs_cv_gap.png)  

---

## 1. Executive Summary

A critical objective in Phase 5 was investigating whether tuning could mitigate the gap between training and validation performance without sacrificing the model's non-linear expressive power. 

Because Extra Trees grows unpruned trees to leaf purity ($R^2_{\text{train}} \approx 0.99999$), assessing generalization requires tracking the **Train-CV Gap** ($\Delta R^2 = R^2_{\text{train}} - R^2_{\text{CV}}$) and confirming whether cross-validation performance translates reliably to completely untouched test data.

---

## 2. Longitudinal Overfitting Progression Across Phases

Tracking the model progression across all project phases reveals consistent shrinkage of the overfitting margin alongside increasing predictive accuracy:

| Phase & Milestone | Architecture / Pipeline | Train R² | 5-Fold CV R² | Train-CV Gap | Test R² (Holdout) | Test RMSE |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Phase 2 Baseline** | Random Forest (Default) | 0.982755 | 0.864777 | **0.117978** | 0.890397 | 0.442339 |
| **Phase 4 Selection** | Extra Trees (Default) | 0.999990 | 0.905368 | **0.094622** | 0.918392 | 0.381689 |
| **Phase 5 Tuned** | Extra Trees (`n=500, feat='sqrt'`) | 0.999990 | **0.911006** | **0.088983** | **0.927548** | **0.359641** |

```
Overfitting Gap Evolution (Train-CV Gap ↓):
Phase 2 Baseline (RF)        : [============================] 0.1180
Phase 4 Extra Trees (Default): [=======================]      0.0946  (-19.8% over baseline)
Phase 5 Tuned Extra Trees    : [=====================]        0.0890  (-24.6% over baseline)
```

### Key Analytical Takeaways:
1. **Structural Regularization via Random Subspacing:**
   - Shifting from `max_features = 1.0` to `max_features = 'sqrt'` narrowed the Train-CV gap by an additional **-0.005639**, reaching the project's lowest overfitting gap for non-linear tree models (**0.088983**).
2. **Generalization Without Artificially Imposed Bias:**
   - While shallow trees (`max_depth = 10`) produced a smaller nominal gap (~0.029), their CV R² collapsed to 0.794. The tuned configuration successfully reduced the generalization gap while simultaneously *increasing* CV R² to 0.9110 and Test R² to 0.9275.

---

## 3. Quarantined Holdout Test Evaluation

Per project requirements, the 1,000-record holdout test set remained strictly quarantined throughout all 50 Optuna trials and was evaluated **exactly once** after the candidate configuration was finalized:

| Metric | Phase 4 Candidate (Default ET) | Phase 5 Winner (Tuned ET) | Net Change | Relative Improvement |
|---|:---:|:---:|:---:|:---:|
| **Test R²** | 0.918392 | **0.927548** | **+0.009156** | **+1.00%** |
| **Test RMSE** | 0.381689 | **0.359641** | **-0.022048** | **-5.78% (Error Reduction)** |
| **Test MAE** | 0.260199 | **0.249022** | **-0.011177** | **-4.30% (Error Reduction)** |

### Generalization Fidelity Check:
- The holdout Test R² of **0.927548** aligns closely with the upper bound of the cross-validation distribution ($0.911006 \pm 0.003525 \times 2 \approx [0.9040, 0.9181]$), demonstrating that the model does not suffer from holdout degradation or negative transfer.
- Test RMSE dropped from **0.3817** to **0.3596**, confirming genuine out-of-sample error reduction on completely independent student responses.

---

## 4. Pipeline Leakage Audit & Verification

To verify that the generalization performance is genuine and not an artifact of data leakage, the pipeline was audited against five leakage vectors:

1. **Target Leakage:** Target (`Mental_Health_Score`) was strictly isolated from `X_train` and `X_test` feature matrices.
2. **Country Grouping:** Top 10 country categories were learned strictly from `train_df` frequency distributions. Unseen or low-frequency countries in both validation folds and the test set were deterministically assigned to `'Other'`.
3. **Scaling & Imputation:** `SimpleImputer` and `StandardScaler` instances were fitted exclusively inside each CV training fold and transformed on validation/test partitions.
4. **Categorical Encoders:** `OrdinalEncoder` (4 levels) and `OneHotEncoder(handle_unknown='ignore')` learned categories strictly from training folds.
5. **No Optimization Leakage:** Optuna objectives and trial samplers evaluated CV folds only. Zero test set queries were executed during the 50 trials.
