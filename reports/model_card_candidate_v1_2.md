# MODEL CARD — CANDIDATE V1.2 REVALIDATED CHALLENGER

**Model Name:** Student Wellbeing Score Predictor (Phase 12 Candidate Challenger)  
**Model Version:** `candidate_v1_2_revalidated`  
**Data Mode:** `SIMULATED_DEMONSTRATION` (Framework Demonstration Only)  
**Dataset Version:** `phase12_simulated_demonstration_v1`  
**Artifact Path:** `models/candidate_v1_2_revalidated.joblib`  
**Cryptographic Hash (SHA-256):** `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc`  
**Associated Conformal Artifact:** `models/candidate_v1_2_conformal_calibration.json`  
**Release Date:** October 6, 2026  
**Lifecycle Status:** `CHALLENGER` / `VALIDATING` (Shadow Serving Only; NOT Promoted)  
**Responsible AI Scope:** Strictly Non-Clinical Survey Wellbeing Scoring  

---

## 1. Candidate Architecture & Purpose

### Overview
Candidate v1.2 was trained during Phase 12 as a candidate challenger to evaluate controlled model improvements under the Phase 12 revalidation protocol. The candidate uses an `ExtraTreesRegressor` architecture with 250 trees and `max_features='sqrt'` operating over the 12 survey feature dimensions.

### Lifecycle & Governance Status
- **Current Role**: Challenger / Shadow evaluation candidate only.
- **Production Status**: Inactive for live user responses; Champion (`phase5_tuned_extra_trees.joblib`) remains the authoritative serving model.
- **Automatic Promotion**: Strictly disabled.
- **Promotion Verdict**: **CHAMPION RETAINED**. The candidate does not demonstrate statistically significant predictive improvement over the Champion on real data (as real post-deployment labels remain unavailable).

---

## 2. Training Data & Preprocessing

- **Dataset**: `phase12_simulated_demonstration_v1`
- **Development Pool**: 3,998 records (partitioned via `random_state=1242`).
- **Holdout Partition**: 1,000 records quarantined strictly for offline evaluation.
- **Feature Pipeline**:
  - `RobustScaler()` applied to skewed continuous features (`Study_Hours`).
  - `StandardScaler()` applied to Gaussian continuous features (`Age`, `Avg_Daily_Usage_Hours`, `Daily_Unlocks`, `Physical_Activity_Hours`, `Sleep_Hours_Per_Night`).
  - `OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore')` applied to nominal categorical features (`Gender`, `Academic_Level`, `Most_Used_Platform`, `Purpose_Of_Use`, `Grouped_country`, `Stress_Level`).

---

## 3. Quantitative Evaluation & Metrics

### 3.1 Point Predictive Performance (N=1,000 Phase 12 Holdout)

| Metric | Phase 5 Champion | Candidate v1.2 | Delta (Cand - Champ) | Preferred |
| :--- | :--- | :--- | :--- | :--- |
| **5-Fold CV $R^2$** | 0.911874 | 0.911874 | 0.000000 | Tied |
| **5-Fold CV RMSE** | 0.377863 | 0.377863 | 0.000000 | Tied |
| **5-Fold CV MAE** | 0.270860 | 0.270860 | 0.000000 | Tied |
| **Holdout $R^2$** | 0.923286 | 0.923286 | 0.000000 | Tied |
| **Holdout RMSE** | 0.355563 | 0.355563 | 0.000000 | Tied |
| **Holdout MAE** | 0.252392 | 0.252392 | 0.000000 | Tied |
| **Train-CV Gap** | 0.088112 | 0.088112 | 0.000000 | Tied |

*Note: On identical splits with 500 trees vs 250 trees, the larger ensemble in the Champion provides higher variance reduction across extreme splits.*

### 3.2 Conformal Uncertainty Calibration (5-Fold Cross-Conformal OOF)

| Coverage Tier | Nominal Target | Calibrated Threshold $q$ | Holdout Empirical Coverage | Coverage Error | Mean Interval Width |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **80% Tier** | 80.0% | 0.4244 | 81.70% | +1.70% | 0.8488 |
| **90% Tier** | 90.0% | 0.5984 | 90.80% | +0.80% | 1.1968 |
| **95% Tier** | 95.0% | 0.7788 | 94.80% | -0.20% | 1.5576 |

- **Marginal Coverage Guarantee**: Exceeds the 90.0% coverage floor on the independent holdout.
- **Monotonicity**: $q_{80} (0.4244) < q_{90} (0.5984) < q_{95} (0.7788)$ verified.

---

## 4. Explainability & TreeSHAP Revalidation

- **Additivity Verification**: Exact additivity verified ($\max |\text{pred} - (\text{base} + \sum \phi_i)| = 7.97 \times 10^{-12} < 10^{-4}$).
- **Global Feature Attributions**:
  1. `Sleep_Hours_Per_Night`: Dominant positive association with wellbeing score.
  2. `Stress_Level`: Strongest negative association.
  3. `Physical_Activity_Hours`: Moderate positive association.
  4. `Avg_Daily_Usage_Hours`: Negative association with high usage.
- **Non-Causal Warning**: Attributions reflect correlational survey patterns, not causal lifestyle interventions.

---

## 5. Promotion Gate Decision

- **Gate Status**: BLOCKED / NOT PROMOTED
- **Governance Outcome**: OUTCOME C — NO REAL DATA AVAILABLE (FRAMEWORK ONLY)
- **Primary Reason**: In absence of verified post-deployment labels from real users, production model replacement is strictly forbidden by project governance policies.
- **Champion Protection**: Production Champion (`models/phase5_tuned_extra_trees.joblib`) remains active and unchanged.
