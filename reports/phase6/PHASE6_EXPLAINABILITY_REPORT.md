# PHASE 6 — COMPREHENSIVE SHAP EXPLAINABILITY & AUDIT REPORT

**Project:** Student Mental Health / Wellbeing Score Prediction  
**Phase:** 6 — SHAP Explainability & Model Interpretation  
**Date:** October 2026  
**Status:** Completed & Quality Gates Signed Off  
**Analyzed Model Artifact:** [`models/phase5_tuned_extra_trees.joblib`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/phase5_tuned_extra_trees.joblib)  
**Primary Execution Notebook:** [`ml/notebooks/06_explainability_shap.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/06_explainability_shap.ipynb)  
**Experiment Log Artifact:** [`ml/experiments/phase6_shap_feature_importance.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase6_shap_feature_importance.csv)  

---

## 1. Comprehensive Answers to Mandatory Phase 6 Questions

### Q1: Why was SHAP selected?
SHAP (SHapley Additive exPlanations) was selected because it is the only feature attribution framework grounded in cooperative game theory that simultaneously satisfies the four fundamental axioms of fair attribution:
1. **Efficiency (Additivity):** Feature attributions sum exactly to the difference between the model's prediction and the expected population baseline ($\sum \phi_j = f(x) - \mathbb{E}[f(X)]$).
2. **Symmetry:** Features making equal marginal contributions across all coalitions receive equal attribution.
3. **Dummy (Null Player):** Features that do not change predictions across any coalition receive exactly zero attribution.
4. **Additivity / Monotonicity:** If a model changes such that a feature's marginal contribution increases, its attribution cannot decrease.
Furthermore, **TreeSHAP** provides an exact polynomial-time algorithm for tree ensembles, avoiding the high variance and heuristic sampling instability of perturbation-based explainers like LIME.

### Q2: Which model was explained?
The **Tuned Extra Trees Regressor Pipeline** finalized in Phase 5 (`models/phase5_tuned_extra_trees.joblib`):
- **Estimator:** `ExtraTreesRegressor(n_estimators=500, max_depth=None, min_samples_split=2, min_samples_leaf=1, max_features='sqrt', random_state=42)`
- **Preprocessing:** 4-pipeline `ColumnTransformer` with 38 transformed output dimensions.
- **Model Freeze:** The model was preserved strictly intact without retraining, parameter changes, or feature alterations.

### Q3: Which dataset/sample was explained?
A representative explanation sample of **300 observations** drawn deterministically (`random_state=42`) from the 3,998-record training partition (`train_df`). The 1,000-record holdout test set was intentionally excluded to prevent explanation leakage or post-hoc model modifications.

### Q4: How was SHAP computed?
Using `shap.TreeExplainer(model)` from SHAP version 0.52.0 applied directly to the fitted 500-tree ensemble operating on the 38 transformed columns produced by `ColumnTransformer`. Feature attributions were calculated using the internal path-dependent tree conditional expectation algorithm.

### Q5: Does SHAP reconstruct model predictions?
**Yes, with exact mathematical precision.** Across all 300 observations evaluated:
$$\text{Reconstruction Error} = |f(x) - (\text{Base Value} + \sum_{j=1}^{38} \phi_j)|$$
- **Maximum Absolute Error:** **0.0000000000**
- **Mean Absolute Error:** **0.0000000000**
Every single model prediction matches the sum of the cohort expected baseline ($6.2246$) and the individual SHAP contributions to within floating-point epsilon.

### Q6: What are the top global features?
Aggregating the 38 transformed columns back to the 12 original survey dimensions yields the definitive ranking:
1. **`Stress_Level`** (Mean |SHAP| = **0.2437**)
2. **`Avg_Daily_Usage_Hours`** (Mean |SHAP| = **0.2293**)
3. **`Sleep_Hours_Per_Night`** (Mean |SHAP| = **0.2052**)
4. **`Daily_Unlocks`** (Mean |SHAP| = **0.1747**)
5. **`Study_Hours`** (Mean |SHAP| = **0.1190**)
6. **`Most_Used_Platform`** (Mean |SHAP| = **0.0810**)
7. **`Grouped_country`** (Mean |SHAP| = **0.0728**)
8. **`Purpose_Of_Use`** (Mean |SHAP| = **0.0579**)
9. **`Physical_Activity_Hours`** (Mean |SHAP| = **0.0492**)
10. **`Academic_Level`** (Mean |SHAP| = **0.0466**)
11. **`Gender`** (Mean |SHAP| = **0.0421**)
12. **`Age`** (Mean |SHAP| = **0.0307**)

### Q7: Which features push predictions upward/downward?
- **Features Pushing Upward (Protective Predictors):**
  - **Adequate Sleep ($\ge 7.5$ hours):** Contributes up to $+0.70$ points.
  - **Low Stress (`'Low'`):** Contributes up to $+0.92$ points.
  - **Controlled Screen Time ($< 3.5$ hours):** Contributes up to $+0.48$ points.
  - **Dedicated Study Time ($> 4.0$ hours):** Contributes up to $+0.30$ points.
  - **Regular Physical Activity ($> 2.0$ hours):** Contributes up to $+0.18$ points.
- **Features Pushing Downward (Risk Predictors):**
  - **High Stress (`'High'`, `'Very High'`):** Drags predictions down by $-0.38$ to $-0.98$ points.
  - **Heavy Screen Usage ($> 6.5$ hours):** Drags predictions down by $-0.40$ to $-0.65$ points.
  - **Sleep Deprivation ($< 5.5$ hours):** Drags predictions down by $-0.35$ to $-0.60$ points.
  - **Frequent Unlocks ($> 180$ unlocks/day):** Drags predictions down by $-0.20$ to $-0.35$ points.

### Q8: How do local explanations differ from global importance?
Global importance reflects the average magnitude of influence across the whole student population. In individual student predictions, idiosyncratic feature combinations can reorder local priorities:
- In **Case A** (low score), `Avg_Daily_Usage_Hours` (7.0h) contributed $-0.61$, almost matching the impact of `Stress_Level` ($-0.98$).
- In **Case B** (mid-range score), physical activity (+0.14) and moderate unlocks mitigated high stress, producing a near-average prediction.
Local explanations reveal the specific combination of compensatory and compounding factors unique to each student.

### Q9: Which interactions were observed?
1. **Sleep × Screen Usage:** Adequate sleep ($\ge 7.5$ hours) buffers against the negative predictive impact of moderate-to-heavy screen time.
2. **Stress × Sleep:** Very high stress combined with sleep deprivation creates a non-linear compounding penalty, pulling predictions into the lowest decile ($\le 3.6$).
3. **Physical Activity × Screen Usage:** Physical exercise provides a moderate positive counterweight against digital usage up to ~5.5 hours, but fails to offset extreme screen time ($>7.5$ hours).
4. **Study × Sleep:** Academic study time is predictive of higher wellbeing only when sleep is preserved; sleep-deprived studying is penalized by the model.

### Q10: What was the SHAP computational cost?
- **Total Calculation Duration:** **436.82 seconds (~7.28 minutes)** across 300 observations for 500 unconstrained trees.
- **Average Latency Per Sample:** **1,456.07 ms (~1.46 seconds)** per observation.
- **Computational Driver:** Traversal of 500 deep unconstrained decision trees across 38 transformed features requires millions of recursive split evaluations.

### Q11: What are the limitations?
1. **TreeSHAP Latency:** 1.46 seconds per observation is too slow for synchronous REST API requests (standard SLA $< 50$ ms).
2. **Observational Data:** SHAP reveals how the model associates features with survey responses; it cannot prove causal real-world mechanisms.
3. **Collinearity Artifacts:** Highly correlated features (e.g. screen time and unlocks) share credit across tree branches.
4. **Survey Subjectivity:** Stress level is self-reported, and its strong predictive weight may reflect shared subjective reporting variance with the wellbeing score.

### Q12: Which explanations are safe to expose to users?
- **Safe to Expose:**
  - Waterfalls displaying relative factor contributions (e.g. *"Your reported sleep hours contributed +0.5 points to your estimated score"*).
  - Categorization into *"Protective Factors"* (positive contributions) and *"Key Areas for Balance"* (negative contributions).
  - Educational benchmarks showing population distributions.
- **Unsafe to Expose:**
  - Any claim framing SHAP values as medical causes, diagnoses, or clinical risks.
  - Assertions that reducing screen time by X hours will causally cure depression.

### Q13: What belongs in the future API?
1. **Asynchronous Explanation Pipeline:** Decouple prediction (which runs in 0.15 ms) from TreeSHAP explanation (which requires 1.46 s). Return the prediction immediately; provide SHAP explanations via background jobs or pre-computed caches.
2. **Aggregated Feature Payload:** Return SHAP values aggregated by original survey feature name (`Stress_Level`, `Sleep_Hours_Per_Night`), suppressing confusing one-hot dummy column names (`nominal__Most_Used_Platform_Instagram`).
3. **Responsible AI Disclaimers:** Include mandatory ethical disclaimers in every API response payload: *"Model-generated statistical association; not a clinical assessment."*

---

## 2. Phase 6 Quality Gate Sign-Off Checklist

| # | Quality Gate Criterion | Verification Method | Status | Audit Findings |
|:---:|---|---|:---:|---|
| 1 | **Exact Additivity Verification** | Floating-point delta | **PASSED** | $\text{Max Error} = 0.0000000000$. Exact reconstruction verified. |
| 2 | **Frozen Model Preservation** | Hash and metadata check | **PASSED** | Phase 5 model artifact and metadata left completely untouched. |
| 3 | **Notebook-First ML Adherence** | Workspace scan | **PASSED** | Exactly 0 new ML `.py` files. All logic in `06_explainability_shap.ipynb`. |
| 4 | **No Leakage to Holdout** | Script audit | **PASSED** | 300 explanation samples drawn strictly from training partition. Holdout untouched. |
| 5 | **Programmatic Feature Mapping**| Assertion check | **PASSED** | All 38 transformed features mapped to 12 parent survey dimensions. |
| 6 | **Original Feature Aggregation** | Mathematical validation | **PASSED** | One-hot dummy contributions aggregated signed per sample before mean absolute ranking. |
| 7 | **Representative Cases Selected** | Decile inspection | **PASSED** | Low (3.60), Mid (6.00), High (9.00) analyzed without clinical labeling. |
| 8 | **All Diagnostic Plots Saved** | File system audit | **PASSED** | 8 figures generated and verified in `ml/evaluation/`. |
| 9 | **Experiment CSV Exported** | File check | **PASSED** | `phase6_shap_feature_importance.csv` logged with 12 features. |
| 10 | **Responsible AI Terminology** | Documentation audit | **PASSED** | Zero diagnostic/causal claims. Purely framed as statistical model contributions. |

---

## 3. Transition Roadmap: Phase 7 — Uncertainty Quantification

With model transparency, global importance, and local explanations established, the project is ready for **Phase 7 — Uncertainty Quantification & Prediction Intervals**:
- **Objective:** Move beyond point predictions ($\hat{y} = 6.2$) to calibrated prediction intervals ($\hat{y} \in [5.7, 6.7]$ at $90\%$ confidence).
- **Core Technology:** Evaluate Conformal Prediction (MAPIE) and Quantile Regression to provide finite-sample coverage guarantees.
- **User Value:** Communicate prediction certainty to students and educators, flagging instances with wide error bounds for cautious interpretation.
