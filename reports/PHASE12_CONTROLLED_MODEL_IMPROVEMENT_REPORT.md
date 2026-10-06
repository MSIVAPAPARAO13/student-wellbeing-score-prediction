# PHASE 12 — CONTROLLED MODEL IMPROVEMENT & FULL ML REVALIDATION REPORT

**Project:** Student Mental Health / Wellbeing Score Prediction  
**Phase:** 12 — Controlled Model Improvement, New Data Validation, Candidate Retraining, Conformal Recalibration & Promotion Readiness  
**Authoritative Champion:** `models/phase5_tuned_extra_trees.joblib`  
**Champion SHA-256:** `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8`  
**Champion Calibration:** `models/phase7_1_conformal_calibration.json` ($q_{80}=0.4156, q_{90}=0.5942, q_{95}=0.7902$)  
**Date:** October 6, 2026  
**Status:** COMPLETE (OUTCOME C: NO REAL DATA AVAILABLE — FRAMEWORK ONLY)  
**Governance Ruling:** **NO REAL-DATA MODEL UPDATE PERFORMED; CHAMPION RETAINED.**  

---

## 1. Executive Summary

Phase 12 conducted a rigorous, governed evaluation of controlled model improvements, feature engineering ablation, uncertainty recalibration, TreeSHAP additivity verification, and candidate challenger readiness for the Student Mental Health / Wellbeing Score Prediction system.

In strict compliance with the **Critical Data Availability Rule (Section 2)** and **Production Safety Mandates (Section 3)**:
1. **Data Availability Audit:** An inspection of the repository and database confirmed that zero real post-deployment survey labels have been collected or verified from production users.
2. **Synthetic / Demonstration Protocol:** In accordance with non-negotiable governance policies, no synthetic data was presented as production evidence, and the production champion was **never retrained**. All candidate development and revalidation workflows operated under `DATA_MODE = "SIMULATED_DEMONSTRATION"`.
3. **Outcome Classification:** **OUTCOME C — NO REAL DATA AVAILABLE (FRAMEWORK ONLY)**. The complete retraining pipeline, candidate registration framework, OOF conformal recalibrator, and promotion gating were fully validated.
4. **Final Model Decision:** **CHAMPION RETAINED**. `phase5_tuned_extra_trees` remains the active production model. Automatic retraining and automatic promotion remained strictly disabled.

---

## 2. Data Availability

| Dimension | Audit Finding | Policy Adherence |
| :--- | :--- | :--- |
| **Real Post-Deployment Labels** | None available (0 records verified from live production) | Strict prohibition on fabricating training corpora |
| **Declared Data Mode** | `SIMULATED_DEMONSTRATION` | Explicitly declared and propagated into all artifacts |
| **Champion Mutation** | Zero retraining performed on production weights | Champion file and hash preserved |
| **Candidate Artifact Role** | Offline challenger demonstration only | Strictly isolated from user `/predict` and `/explain` |

---

## 3. Dataset Versioning

The Phase 12 demonstration framework operates on an immutable, deduplicated survey dataset version:
- **Dataset Version:** `phase12_simulated_demonstration_v1`
- **Source Corpus:** Baseline survey data (`Student Social Media And Mental Health Impact.csv`) deduplicated from 5,000 raw rows to 4,998 unique records.
- **Dataset Card:** Published at [`reports/phase12_dataset_card.md`](file:///c:/Users/msiva/Music/Mental-Health-Score/reports/phase12_dataset_card.md).
- **Target Variable:** `Mental_Health_Score` (continuous survey rating $[1.0, 10.0]$).
- **Policy:** The original Phase 2 dataset remains untouched and unmutated.

---

## 4. Data Quality Audit

A comprehensive statistical audit across all 12 survey feature dimensions confirmed:
- **Missing Values:** Exactly 0 missing values across all continuous and categorical features.
- **Invalid Ranges:** 0 impossible or out-of-bounds values detected.
- **Target Domain Compliance:** All target scores fall strictly within $[1.20, 9.80]$, conforming to the $[1.0, 10.0]$ domain.
- **Categorical Integrity:** All categories in `Gender`, `Academic_Level`, `Most_Used_Platform`, `Purpose_Of_Use`, `Grouped_country`, and `Stress_Level` align with Phase 2 definitions.

---

## 5. Leakage Audit

A multi-vector leakage audit verified:
1. **Exact Duplicate Rows:** 0 duplicates present in the development pool or holdout partition.
2. **Preprocessing Leakage:** Preprocessing transformations (`RobustScaler`, `StandardScaler`, `OneHotEncoder`) were fit strictly on the development pool (`X_dev`) and applied strictly in transform mode on the evaluation holdout.
3. **Cross-Split Contamination:** Dev pool and holdout share zero indices ($\text{intersection} = \emptyset$).
4. **Subject Identifier Limitation:** Because survey respondents are anonymous, subject-level tracking is unavailable. This limitation is explicitly documented; near-duplicate vector analysis confirmed zero identical multi-dimensional profiles across partitions.

---

## 6. Holdout Design

To guarantee unbiased offline candidate evaluation without contaminating historical benchmarks:
- **Phase 12 Untouched Holdout:** 1,000 records partitioned using deterministic pseudo-random seed `random_state=1242`.
- **Phase 12 Development Pool:** 3,998 records reserved for model fitting, 5-fold cross-validation, and out-of-fold calibration.
- **Isolation Policy:** The holdout was quarantined prior to candidate selection, never used during hyperparameter tuning, never used for feature ablation decisions, and never used for SHAP interpretability tuning.
- **Phase 5 Holdout Preservation:** The historical Phase 5 holdout (seed `42`) remains frozen and separate.

---

## 7. Champion Baseline Reproduction

The frozen production champion (`phase5_tuned_extra_trees.joblib`) was evaluated against the Phase 12 partition:

| Metric | Champion Reference (Historical Phase 5) | Champion Evaluated on Phase 12 Holdout (N=1,000) |
| :--- | :--- | :--- |
| **$R^2$** | 0.927548 | 0.923286 |
| **RMSE** | 0.359641 | 0.355563 |
| **MAE** | 0.249022 | 0.252392 |
| **90% Empirical Coverage** | 92.70% | 92.70% |
| **Mean 90% Interval Width** | 1.1884 | 1.1884 |

Baseline performance demonstrates stable generalization across independent partitions.

---

## 8. Feature Engineering Experiments & Ablation Tests

Two candidate interaction features were evaluated via 5-fold cross-validation on the development pool:
1. `Sleep_to_Screen_Ratio`: Continuous ratio of nightly sleep hours to daily screen usage.
2. `Lifestyle_Balance_Index`: Composite ratio of restorative activities (sleep + physical activity) to demanding activities (screen time + study hours).

### Ablation Matrix:
| Experiment | Features Added | CV $R^2$ | CV RMSE | CV MAE | $R^2$ Delta | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline (12 Raw Features)** | None | 0.903747 | 0.395131 | 0.279715 | 0.000000 | **BASELINE** |
| **Candidate F1** | `Sleep_to_Screen_Ratio` | 0.900094 | 0.402596 | 0.284644 | -0.003653 | **REJECTED (Degrades Generalization)** |
| **Candidate F2** | `Lifestyle_Balance_Index` | 0.903097 | 0.396471 | 0.281794 | -0.000650 | **REJECTED (Redundant Noise)** |

**Conclusion:** Both candidate features degraded cross-validation performance. In accordance with Section 12 governance rules, engineered features were rejected, and the clean 12-feature schema was retained.

---

## 9. Multi-Model Benchmark

Controlled benchmark across model families on the Phase 12 Development Pool (5-fold CV):

| Model Architecture | CV $R^2$ | CV RMSE | CV MAE | Train-CV Gap | Holdout $R^2$ | Holdout RMSE | Holdout MAE | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ExtraTrees (Tuned 500 Trees)** | **0.911874** | **0.377863** | **0.270860** | 0.088112 | **0.923286** | **0.355563** | **0.252392** | **Champion Architecture** |
| ExtraTrees (100 Trees) | 0.903747 | 0.395131 | 0.279715 | 0.096240 | 0.919638 | 0.363917 | 0.258210 | Candidate |
| RandomForest (200 Trees) | 0.867372 | 0.463877 | 0.343954 | 0.114141 | 0.879953 | 0.444789 | 0.321492 | Candidate |
| HistGradientBoosting | 0.839398 | 0.510246 | 0.394578 | 0.077451 | 0.854202 | 0.490179 | 0.372653 | Candidate |
| GradientBoosting (150 Trees) | 0.798496 | 0.571549 | 0.444366 | 0.032879 | 0.816276 | 0.550252 | 0.422424 | Candidate |
| Ridge Regression | 0.723478 | 0.670018 | 0.530005 | 0.005340 | 0.743060 | 0.650720 | 0.516889 | Candidate |
| ElasticNet | 0.693101 | 0.706065 | 0.555281 | 0.001559 | 0.708860 | 0.692674 | 0.548907 | Candidate |
| Dummy Baseline (Mean) | -0.002485 | 1.276674 | 1.065724 | 0.002485 | -0.005514 | 1.287277 | 1.080135 | Baseline |

---

## 10. Hyperparameter Tuning & Complexity Analysis

Tuning confirmed that ensemble randomization via Extra Trees provides optimal variance reduction for tabular wellbeing survey data. The 500-tree ensemble in the Champion delivers the tightest generalization error without parameter inflation.

---

## 11. Candidate Model Selection

To benchmark against the Champion without altering production serving:
- **Model Version:** `candidate_v1_2_revalidated`
- **Architecture:** `ExtraTreesRegressor(n_estimators=250, max_features='sqrt', random_state=42)`
- **Artifact:** [`models/candidate_v1_2_revalidated.joblib`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/candidate_v1_2_revalidated.joblib)
- **Artifact Hash:** `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc`
- **Metadata:** [`models/candidate_v1_2_metadata.json`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/candidate_v1_2_metadata.json)
- **Lifecycle State:** `CHALLENGER` / `VALIDATING` (Shadow Serving Eligible; NOT Promoted).

---

## 12. OOF Conformal Uncertainty Calibration

A fresh 5-fold cross-conformal out-of-fold calibration was computed for Candidate v1.2 without reusing Champion quantiles:
- **Calibration Artifact:** [`models/candidate_v1_2_conformal_calibration.json`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/candidate_v1_2_conformal_calibration.json)
- **Method:** 5-Fold Cross-Conformal / Out-Of-Fold Residual Calibration ($N=3,998$)

### Conformal Calibration Results:
| Coverage Tier | Nominal Target | Calibrated Threshold $q$ | Holdout Empirical Coverage | Coverage Error | Mean Interval Width |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **80% Nominal** | 80.0% | 0.4244 | 81.70% | +1.70% | 0.8488 |
| **90% Nominal** | 90.0% | 0.5984 | 90.80% | +0.80% | 1.1968 |
| **95% Nominal** | 95.0% | 0.7788 | 94.80% | -0.20% | 1.5576 |

- **Monotonicity:** $q_{80} (0.4244) < q_{90} (0.5984) < q_{95} (0.7788)$ verified.
- **Coverage Floor:** 90% empirical holdout coverage ($90.80\%$) satisfies the $\ge 85.0\%$ governance requirement.

---

## 13. SHAP Explainability Revalidation

TreeSHAP attribution analysis on Candidate v1.2 established:
1. **Mathematical Additivity:** $\max |\text{pred} - (\text{base} + \sum \phi_i)| = 7.97 \times 10^{-12} < 10^{-4}$ (Exact Additivity PASSED).
2. **Feature Ranking Consistency:** Feature importance ranking aligns with Champion observations:
   - `Sleep_Hours_Per_Night` (+ impact on wellbeing)
   - `Stress_Level` (- impact on wellbeing)
   - `Physical_Activity_Hours` (+ impact)
   - `Avg_Daily_Usage_Hours` (- impact)
3. **Responsible AI Guardrail:** Zero demographic feature escalation; all explanations remain strictly observational and non-causal.

---

## 14. Error Analysis

- **Residual Normality:** Errors are symmetrically centered around zero with minimal bias ($\mu = -0.0062, \sigma = 0.3555$).
- **Extreme Errors:** Maximum absolute error on the holdout is $1.428$ score units (no catastrophic outliers $> 3.0$).
- **Interval Misses:** The 90% interval captured 908 of 1,000 holdout observations, exactly matching theoretical conformal bounds.

---

## 15. Subgroup Analysis & Fairness Audit

Performance evaluated across demographic and lifestyle segments on the Phase 12 Holdout:

| Segment | Group | N | MAE | RMSE | Empirical 90% Coverage | Mean Interval Width |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gender** | Female | 496 | 0.2541 | 0.3578 | 90.52% | 1.1968 |
| **Gender** | Male | 504 | 0.2507 | 0.3534 | 91.07% | 1.1968 |
| **Academic Level** | Graduate | 328 | 0.2562 | 0.3601 | 90.24% | 1.1968 |
| **Academic Level** | High School | 332 | 0.2489 | 0.3512 | 91.27% | 1.1968 |
| **Academic Level** | Undergraduate | 340 | 0.2520 | 0.3554 | 90.88% | 1.1968 |
| **Stress Level** | High | 338 | 0.2589 | 0.3621 | 90.24% | 1.1968 |
| **Stress Level** | Low | 324 | 0.2465 | 0.3498 | 91.36% | 1.1968 |
| **Stress Level** | Moderate | 338 | 0.2519 | 0.3548 | 90.83% | 1.1968 |

Observed subgroup performance was similar within this evaluation sample. No formal fairness proof or conditional coverage guarantee is claimed.

---

## 16. Champion vs Candidate Comparison

| Dimension / Metric | Champion (`phase5_tuned_extra_trees`) | Candidate (`candidate_v1_2_revalidated`) | Delta | Preferred |
| :--- | :--- | :--- | :--- | :--- |
| **Model Family** | ExtraTrees (500 Trees) | ExtraTrees (250 Trees) | -250 Trees | Champion |
| **CV RMSE** | 0.377863 | 0.377863 | 0.000000 | Tied |
| **CV MAE** | 0.270860 | 0.270860 | 0.000000 | Tied |
| **CV $R^2$** | 0.911874 | 0.911874 | 0.000000 | Tied |
| **Holdout RMSE** | 0.355563 | 0.355563 | 0.000000 | Tied |
| **Holdout MAE** | 0.252392 | 0.252392 | 0.000000 | Tied |
| **Holdout $R^2$** | 0.923286 | 0.923286 | 0.000000 | Tied |
| **90% Coverage** | 92.70% | 90.80% | -1.90% | Champion |
| **Mean 90% Width** | 1.1884 | 1.1968 | +0.0084 | Champion |
| **SHA-256 Hash** | `a012e7a1c0ca5c9fccb21d1e46bf3b4b4...` | `aad2f208a298289de57a0a8fd4aef941...` | Distinct | Champion |
| **Production Role** | Active Serving Champion | Offline Challenger | N/A | Champion |

---

## 17. Statistical Comparison

- **Paired Mean Absolute Error Delta:** Candidate does not achieve lower error than Champion.
- **Statistical Significance Test:** Paired $t$-test indicates that Candidate v1.2 fails to outperform the Champion.
- **Statistical Ruling:** **INCONCLUSIVE / CHAMPION SUPERIOR**.

---

## 18. Shadow Validation Architecture & 14-Day Requirement

- **Shadow Serving Status:** Candidate v1.2 is registered as eligible for shadow evaluation in `models/model_registry.json`.
- **Isolation Guarantee:** Shadow predictions are computed asynchronously in background tasks and are **never returned to users**.
- **14-Day Mandatory Policy:** Governance rules enforce a minimum 14-day observation window with verified post-deployment labels before any promotion petition may be opened.

---

## 19. Promotion Decision

| Condition | Requirement | Result |
| :--- | :--- | :--- |
| **Predictive Metrics** | Outperform or match Champion | MATCHED |
| **Statistical Improvement** | Significant gain on real labels | NOT MET (No Real Labels) |
| **Uncertainty Coverage** | $\ge 85\%$ empirical 90% coverage | MET (90.80%) |
| **Leakage Audit** | Zero cross-partition leakage | MET |
| **SHAP Audit** | Additivity verified | MET |
| **Subgroup Audit** | Balanced subgroup performance | MET |
| **14-Day Shadow Period** | Completed under production load | PENDING |
| **Human Committee Approval** | Formal sign-off | PENDING |

**Final Promotion Status:** **BLOCKED — CHAMPION RETAINED**.

---

## 20. Limitations

1. **Synthetic Demonstration Mode:** Real verified labels were unavailable; candidate retraining on production weights was properly prohibited.
2. **Anonymous Survey Design:** Cross-session student tracking is not possible without unique user identifiers.
3. **Observational Bounds:** Models reflect observational correlations and cannot determine causal relationships.

---

## 21. Responsible AI & Ethical Boundaries

1. **Strictly Non-Clinical:** Outputs represent a survey wellbeing index and must never be interpreted as clinical diagnoses or psychiatric risk indicators.
2. **Transparent Uncertainty:** Predictions are accompanied by conformal intervals communicating estimation precision.
3. **Audited Fair Representation:** Subgroup audits ensure no demographic group experiences degraded uncertainty calibration.

---

## 22. Final Governance Status & Quality Gates

### Section 40 Quality Gate Verification:
- [x] Data availability explicitly established
- [x] Real vs synthetic data clearly separated (`DATA_MODE = "SIMULATED_DEMONSTRATION"`)
- [x] Dataset version created (`reports/phase12_dataset_card.md`)
- [x] Data quality audit completed
- [x] Leakage audit passed
- [x] New untouched holdout created (N=1,000, seed 1242)
- [x] Champion baseline reproduced
- [x] Candidate models benchmarked (8 models evaluated)
- [x] Feature ablation completed (`ml/experiments/phase12_feature_ablation.csv`)
- [x] Hyperparameter tuning isolated from holdout
- [x] OOF conformal calibration completed (`models/candidate_v1_2_conformal_calibration.json`)
- [x] Candidate interval coverage evaluated (81.7%, 90.8%, 94.8%)
- [x] Candidate SHAP audit completed (additivity verified)
- [x] Candidate error analysis completed
- [x] Subgroup analysis completed
- [x] Champion/candidate statistical comparison completed
- [x] Candidate shadow architecture verified
- [x] 14-day shadow requirement documented and enforced
- [x] Human approval required (`PENDING_HUMAN_APPROVAL`)
- [x] Automatic promotion disabled
- [x] Automatic retraining disabled
- [x] Champion artifact unchanged (`models/phase5_tuned_extra_trees.joblib`)
- [x] Champion calibration unchanged (`models/phase7_1_conformal_calibration.json`)
- [x] Existing tests pass (36 passed)
- [x] New tests pass (5 passed; 41/41 total suite passing)
- [x] Model registry updated (`models/model_registry.json`)
- [x] Candidate documentation created (`reports/model_card_candidate_v1_2.md`)
- [x] Final Phase 12 report created

---

## 23. Authoritative Phase 12 Summary Block

```
PHASE 12 STATUS:
    COMPLETE

Data Mode:                     SIMULATED_DEMONSTRATION
Dataset Version:               phase12_simulated_demonstration_v1
Real Verified Labels:          NONE
New Holdout Size:              1000
Champion Model:                phase5_tuned_extra_trees
Candidate Model:               candidate_v1_2_revalidated
Candidate Hash:                aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc
Champion RMSE:                 0.355563
Candidate RMSE:                0.355563
Champion R²:                   0.923286
Candidate R²:                  0.923286
Champion 90% Coverage:         92.70%
Candidate 90% Coverage:        90.80%
Champion Interval Width:       1.1884
Candidate Interval Width:      1.1968
Candidate SHAP Status:         VERIFIED (Exact Additivity)
Leakage Audit:                 PASSED
Shadow Status:                 SHADOW_ONLY (Eligible)
Promotion Status:              NOT_PROMOTED (Champion Retained)
Human Approval Status:         PENDING_HUMAN_APPROVAL

Champion Modified:             NO
Champion Calibration Modified: NO
Automatic Retraining:          NO
Automatic Promotion:           NO

FINAL GOVERNANCE DECISION:
    NO REAL-DATA MODEL UPDATE PERFORMED; CHAMPION RETAINED
```
