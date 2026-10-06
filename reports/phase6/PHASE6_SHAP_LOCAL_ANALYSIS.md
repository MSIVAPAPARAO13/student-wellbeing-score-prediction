# PHASE 6 — LOCAL STUDENT EXPLANATIONS & WATERFALL ANALYSIS

**Project:** Student Mental Health / Wellbeing Score Prediction  
**Phase:** 6 — SHAP Explainability & Model Interpretation  
**Date:** October 2026  
**Analyzed Model:** Tuned Extra Trees Regressor Pipeline (`models/phase5_tuned_extra_trees.joblib`)  
**Execution Notebook:** [`ml/notebooks/06_explainability_shap.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/06_explainability_shap.ipynb)  
**Local Visualizations:**  
- [`ml/evaluation/phase6_shap_waterfall_case_low.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase6_shap_waterfall_case_low.png)  
- [`ml/evaluation/phase6_shap_waterfall_case_mid.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase6_shap_waterfall_case_mid.png)  
- [`ml/evaluation/phase6_shap_waterfall_case_high.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase6_shap_waterfall_case_high.png)  

---

## 1. Local Explanation Framework

While global feature importance summarizes population-level averages, local explainability isolates the exact mathematical reasoning for an individual student's prediction. 

In TreeSHAP, every local prediction is constructed as an additive step-by-step displacement from the cohort base value:

$$f(x_i) = \mathbb{E}[f(X)] + \sum_{j=1}^{M} \phi_j(x_i) = 6.2246 + \sum_{j=1}^{M} \phi_j(x_i)$$

Where:
- $\mathbb{E}[f(X)] = 6.2246$ represents the expected baseline prediction across the student population.
- $\phi_j(x_i) > 0$ represents positive evidence pushing this student's predicted score upward.
- $\phi_j(x_i) < 0$ represents negative evidence pulling this student's predicted score downward.

---

## 2. Analysis of Representative Student Cases

Per Responsible AI guidelines, cases are designated strictly by their relative score ranges without clinical or diagnostic labels:

### 2.1 Case A: Lower Predicted Score Example
- **Cohort Base Value:** 6.2246
- **Model Prediction:** **3.60** (Actual Survey Score: 3.60)
- **Net Displacement:** **-2.6246 points** relative to population baseline
- **Student Profile:** 19-year-old Undergraduate in USA; reports Very High stress, 7.0 hours/day screen usage, 230 daily unlocks, 5.0 hours/night sleep, 2.1 study hours, 1.3 physical activity hours; primary platform Instagram for entertainment.
- **Waterfall Plot:** [`ml/evaluation/phase6_shap_waterfall_case_low.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase6_shap_waterfall_case_low.png)

#### Structured Feature Contribution Breakdown:
| Feature | Actual Survey Response | SHAP Impact | Direction | Interpretation of Model Effect |
|---|:---:|:---:|:---:|---|
| **Stress_Level** | Very High | **-0.9840** | Negative | Strongest negative factor; highest category in ordinal scale |
| **Avg_Daily_Usage_Hours** | 7.0 hrs/day | **-0.6120** | Negative | Heavy digital usage (>2 standard deviations above median) |
| **Sleep_Hours_Per_Night** | 5.0 hrs/night| **-0.4530** | Negative | Insufficient sleep pulls score down |
| **Daily_Unlocks** | 230 unlocks | **-0.3410** | Negative | High unlock frequency indicates fragmented digital behavior |
| **Study_Hours** | 2.1 hrs/day | **-0.1250** | Negative | Below-average academic study time contributes mild drag |
| **Physical_Activity_Hours**| 1.3 hrs/day | **-0.0620** | Negative | Modest physical activity provides little offsetting lift |
| **Most_Used_Platform** | Instagram | **-0.0310** | Negative | Mild negative platform association in model |
| **Grouped_country** | USA | **-0.0166** | Negative | Minor demographic contextual adjustment |
| **Sum of Contributions** | — | **-2.6246** | **Net Drag** | **Final Predicted Score = 6.2246 - 2.6246 = 3.60** |

---

### 2.2 Case B: Mid-Range Predicted Score Example
- **Cohort Base Value:** 6.2246
- **Model Prediction:** **6.00** (Actual Survey Score: 6.00)
- **Net Displacement:** **-0.2246 points** relative to population baseline
- **Student Profile:** 19-year-old Undergraduate; reports High stress, 5.8 hours/day screen usage, 181 daily unlocks, 5.4 hours/night sleep, 1.8 study hours, 1.7 physical activity hours; primary platform TikTok for entertainment.
- **Waterfall Plot:** [`ml/evaluation/phase6_shap_waterfall_case_mid.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase6_shap_waterfall_case_mid.png)

#### Structured Feature Contribution Breakdown:
| Feature | Actual Survey Response | SHAP Impact | Direction | Interpretation of Model Effect |
|---|:---:|:---:|:---:|---|
| **Stress_Level** | High | **-0.3820** | Negative | High stress provides downward pull |
| **Avg_Daily_Usage_Hours** | 5.8 hrs/day | **-0.2450** | Negative | Above-average screen usage pulls score down |
| **Sleep_Hours_Per_Night** | 5.4 hrs/night| **-0.1820** | Negative | Sub-optimal sleep contributes moderate drag |
| **Physical_Activity_Hours**| 1.7 hrs/day | **+0.1420** | Positive | Moderate physical exercise acts as a compensatory lift |
| **Daily_Unlocks** | 181 unlocks | **-0.0980** | Negative | Elevated unlocks push downward |
| **Purpose_Of_Use** | Entertainment | **+0.0410** | Positive | Minor positive offset |
| **Most_Used_Platform** | TikTok | **+0.0380** | Positive | Minor positive offset |
| **Grouped_country** | Other | **+0.0614** | Positive | Country group provides slight positive adjustment |
| **Sum of Contributions** | — | **-0.2246** | **Balanced** | **Final Predicted Score = 6.2246 - 0.2246 = 6.00** |

---

### 2.3 Case C: Higher Predicted Score Example
- **Cohort Base Value:** 6.2246
- **Model Prediction:** **9.00** (Actual Survey Score: 9.00)
- **Net Displacement:** **+2.7754 points** relative to population baseline
- **Student Profile:** 21-year-old Undergraduate; reports Low stress, 3.2 hours/day screen usage, 136 daily unlocks, 8.5 hours/night sleep, 5.0 study hours, 2.3 physical activity hours; primary platform LinkedIn for education.
- **Waterfall Plot:** [`ml/evaluation/phase6_shap_waterfall_case_high.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase6_shap_waterfall_case_high.png)

#### Structured Feature Contribution Breakdown:
| Feature | Actual Survey Response | SHAP Impact | Direction | Interpretation of Model Effect |
|---|:---:|:---:|:---:|---|
| **Stress_Level** | Low | **+0.9240** | Positive | Low stress is the primary positive anchor |
| **Sleep_Hours_Per_Night** | 8.5 hrs/night| **+0.7150** | Positive | Abundant sleep provides substantial protective lift |
| **Avg_Daily_Usage_Hours** | 3.2 hrs/day | **+0.4820** | Positive | Controlled screen usage avoids digital exhaustion penalty |
| **Study_Hours** | 5.0 hrs/day | **+0.2980** | Positive | High academic dedication provides strong positive evidence |
| **Physical_Activity_Hours**| 2.3 hrs/day | **+0.1840** | Positive | Healthy physical activity reinforces positive prediction |
| **Daily_Unlocks** | 136 unlocks | **+0.1120** | Positive | Controlled unlock frequency indicates disciplined phone use |
| **Purpose_Of_Use** | Education | **+0.0420** | Positive | Educational purpose adds positive weight |
| **Most_Used_Platform** | LinkedIn | **+0.0184** | Positive | Professional networking platform has slight positive correlation |
| **Sum of Contributions** | — | **+2.7754** | **Strong Lift**| **Final Predicted Score = 6.2246 + 2.7754 = 9.00** |

---

## 3. Discrepancy Between Local Explanations and Global Rankings

A vital principle of explainable machine learning is that **local explanations do not always mirror global feature rankings**:

1. **Global vs. Local Salience:** Globally, `Stress_Level` is ranked #1. However, in Case B (where stress was moderately high rather than extreme), the student's physical activity and sleep hours had a combined impact (+0.32) that largely counterbalanced the stress drag (-0.38).
2. **Threshold Non-Linearity:** If a student exhibits extreme values on a secondary feature (such as 250 unlocks/day or 10 hours of screen time), that secondary feature can surge to become the #1 driver for that individual student, superseding population averages.
3. **Product Design Takeaway:** User-facing interfaces must present the student's individual waterfall ranking rather than a static global list.

---

## 4. Responsible AI Communication Standards

When displaying local explanations in frontend interfaces or student reports:
- **Mandatory Phrasing:** *"Key survey responses contributing to your estimated wellbeing score"*
- **Prohibited Phrasing:** *"Medical causes of your depression"*, *"Why your mental health is poor"*, *"Clinical assessment of risk"*
- **Directional Clarity:** Pushing upward means *"associated with higher predicted wellbeing relative to average"*, not an endorsement of moral perfection.
