# PHASE 6 — SHAP INTERACTION & DEPENDENCE DYNAMICS REPORT

**Project:** Student Mental Health / Wellbeing Score Prediction  
**Phase:** 6 — SHAP Explainability & Model Interpretation  
**Date:** October 2026  
**Analyzed Model:** Tuned Extra Trees Regressor Pipeline (`models/phase5_tuned_extra_trees.joblib`)  
**Execution Notebook:** [`ml/notebooks/06_explainability_shap.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/06_explainability_shap.ipynb)  
**Interaction Visualizations:**  
- [`ml/evaluation/phase6_shap_interactions.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase6_shap_interactions.png)  
- [`ml/evaluation/phase6_shap_dependence_sleep.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase6_shap_dependence_sleep.png)  
- [`ml/evaluation/phase6_shap_dependence_screen_time.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase6_shap_dependence_screen_time.png)  

---

## 1. Executive Summary

Tree-based ensembles naturally model non-linear interactions across features by splitting on complementary attributes down hierarchical decision branches. Phase 6 investigated empirical two-way interaction dynamics across key behavioral and psychological survey variables to evaluate how joint feature states influence predicted wellbeing scores.

---

## 2. In-Depth Analysis of Key Feature Interactions

Using SHAP dependence plots with interaction color encodings ([`ml/evaluation/phase6_shap_interactions.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase6_shap_interactions.png)), four primary interaction relationships were characterized:

### 2.1 Sleep Hours × Daily Screen Usage
- **Observed Dynamic:** The negative impact of heavy daily screen usage ($> 6.0$ hours) is substantially mitigated when students achieve adequate sleep ($\ge 7.5$ hours). Conversely, when heavy screen usage coincides with short sleep ($< 5.0$ hours), the model applies a compounding downward penalty, reducing the prediction by more than the linear sum of both isolated factors.
- **Buffer Threshold:** At approximately $7.0$ hours of nightly sleep, the slope of the screen usage penalty flattens significantly, suggesting that the model treats adequate sleep as a protective buffer against digital fatigue patterns.

### 2.2 Stress Level × Sleep Hours
- **Observed Dynamic:** For students reporting `'Very High'` stress, increasing sleep from $5.0$ to $8.0$ hours produces an upward SHAP adjustment of $+0.45$ points. However, the model does not predict an escape from below-average wellbeing under `'Very High'` stress through sleep alone: the strong negative stress anchor dominates the overall trajectory.
- **Compounding Degradation:** For students reporting `'High'` or `'Very High'` stress combined with $< 5.5$ hours of sleep, the joint prediction drops into the lowest decile ($\le 4.0$).

### 2.3 Physical Activity × Daily Screen Usage
- **Observed Dynamic:** Physical activity ($> 2.0$ hours/day) acts as a moderate positive counterweight against moderate digital usage ($4.0 - 5.5$ hours). Students who engage in regular physical exercise maintain higher predicted scores than sedentary peers exhibiting identical screen usage.
- **Boundary Limit:** Beyond extreme screen time ($> 7.5$ hours/day), the compensatory effect of physical activity diminishes, indicating that physical activity does not fully offset extreme digital immersion in the model's learned representation.

### 2.4 Study Hours × Sleep Hours
- **Observed Dynamic:** The model treats academic study time ($> 4.0$ hours) favorably only when sleep is preserved. When elevated study hours co-occur with sleep deprivation ($< 5.0$ hours), the positive academic contribution is largely neutralized by the sleep deficit penalty.
- **Optimal Balance Region:** Predictions peak when students balance study hours between $3.5$ and $5.5$ hours while maintaining sleep duration between $7.5$ and $8.5$ hours.

---

## 3. Continuous Feature Response Landscapes

Individual feature dependence plots reveal distinct non-linear geometries:

### 3.1 Sleep Hours Response Curve ([`phase6_shap_dependence_sleep.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase6_shap_dependence_sleep.png))
- Below $6.0$ hours: Steep negative gradient (SHAP impact drops precipitously from $0.0$ to $-0.65$).
- Between $6.5$ and $8.0$ hours: Linear positive inflection.
- Above $8.5$ hours: Asymptotic plateau; additional sleep beyond $9.0$ hours yields diminishing marginal returns (+0.55 to +0.65 max lift).

### 3.2 Daily Usage Hours Response Curve ([`phase6_shap_dependence_screen_time.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase6_shap_dependence_screen_time.png))
- Below $3.5$ hours: Stable positive contribution (+0.30 to +0.50).
- Between $4.0$ and $6.0$ hours: Steep negative slope transition.
- Above $6.5$ hours: Severe negative impact plateauing near $-0.60$ points.

---

## 4. Strict Scientific & Responsible AI Disclaimers

1. **Correlational Modeling, Not Biological Causation:**
   - Observing an interaction between Sleep and Screen Time in this model does **not** prove that screen usage causes insomnia or that sleep restores cellular neurological health.
   - The interactions reflect co-occurrence regularities learned by the Extra Trees ensemble from survey records.
2. **Contextual Observational Data:**
   - Survey metrics are self-reported and subject to recall bias.
   - These patterns must be framed as *predictive associations* within the educational benchmark, not clinical prescriptions or interventions.
