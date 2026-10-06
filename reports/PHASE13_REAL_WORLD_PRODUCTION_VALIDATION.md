# Phase 13: Real-World Production Validation & Controlled Shadow Observation

**Project**: Student Wellbeing Score Prediction  
**Phase**: 13 — Real-World Production Validation & Controlled Shadow Observation  
**Status**: ACTIVE / IN PROGRESS (Controlled Shadow Observation Initiated)  
**Authoritative Repository**: [https://github.com/MSIVAPAPARAO13/student-wellbeing-score-prediction](https://github.com/MSIVAPAPARAO13/student-wellbeing-score-prediction)  

---

## 1. Executive Summary

Phase 13 establishes the formal post-deployment operational validation lifecycle for **Candidate v1.2** (`models/candidate_v1_2_revalidated.joblib`) under live production conditions, while maintaining the frozen **Production Champion** (`models/phase5_tuned_extra_trees.joblib`) as the **sole user-facing inference model**.

The primary objective of Phase 13 is to transition the machine learning lifecycle from offline validation to empirical post-deployment observation. Crucially, governance mandates that offline metrics (Phases 1–12.2) cannot substitute for real-world evidence, synthetic data cannot be counted as production observations, and unverified feedback cannot be treated as ground truth.

At the onset of Phase 13:
- **Production Champion**: ACTIVE PRODUCTION (100% of user traffic, unchanged, frozen).
- **Candidate v1.2**: CHALLENGER / VALIDATING (executing strictly in shadow mode, zero user response routing).
- **Shadow Isolation**: Verified and enforced (candidate exceptions, timeouts, and faults have zero impact on Champion user responses).
- **Shadow Observation Period**: PENDING (0 / 14 consecutive calendar days completed; official start: `2026-10-06T09:30:00Z`).
- **Verified Production Labels**: 0 / 100 accumulated.
- **Human Approval**: PENDING.
- **Candidate Promotion**: **BLOCKED**.

---

## 2. Production Data Availability

A strict categorization hierarchy is enforced to prevent data contamination:
1. **Category A — Historical / Offline Data**: The 4,998 survey records used across Phases 1 through 12.2. These provide historical benchmarks but **cannot** satisfy post-deployment operational thresholds.
2. **Category B — Real Post-Deployment Observations**: Live incoming HTTP requests received by the production API (`POST /predict`). Pseudonymous identifiers correlate telemetry without logging student PII.
3. **Category C — Verified Production Labels**: Genuinely new, post-deployment follow-up survey outcomes verified against strict domain and lineage rules. **Only Category C counts toward the $\ge 100$ governance promotion threshold.**
4. **Category D — Synthetic / Demonstration Data**: Strictly forbidden from qualifying as production evidence.

### Current Availability Status
As recorded in `ml/experiments/phase13_verified_label_summary.csv`:
```
NO REAL PRODUCTION OBSERVATIONS AVAILABLE FOR EVALUATION YET.
Accumulated Verified Production Labels: 0 / 100
```
No historical records have been retroactively relabeled, and no mock labels have been injected. The system awaits legitimate incoming post-deployment observations.

---

## 3. Shadow Architecture

The production architecture enforces strict operational isolation between Champion and Candidate:

```
                  USER / FRONTEND CLIENT
                           |
                           v
                 PRODUCTION FASTAPI APP
                           |
       +-------------------+-------------------+
       |                                       |
       v                                       v
CHAMPION MODEL                         CANDIDATE v1.2
(phase5_tuned_extra_trees)             (candidate_v1_2_revalidated)
ACTIVE SYNCHRONOUS PATH                OUT-OF-BAND / SHADOW PATH
       |                                       |
       v                                       v
[Calculate Prediction & 90% Interval]   [Shadow Prediction & Telemetry]
       |                                       |
       v                                       v
RETURN HTTP 200 TO USER                 LOG PAIRED DIFFERENCE TO STORE
(Never affected by Candidate)           (NEVER returned to user)
```

### Key Technical Safeguards:
1. **Response Isolation**: Candidate predictions and uncertainty intervals are never returned in the `/predict` JSON response.
2. **Failure Isolation**: The candidate execution in `ShadowServingManager.evaluate_live_shadow()` is wrapped in non-blocking error handling. If Candidate throws an exception, crashes, or times out, the error is logged to operational telemetry and the Champion request completes with HTTP 200.
3. **Rollback Mechanism**: Shadow execution can be instantly disabled dynamically via registry flag (`shadow_serving_config.enabled = false`) without modifying or restarting the Champion pipeline.

---

## 4. Shadow Start Date

The formal shadow observation window commenced on:
- **`shadow_start_timestamp`**: `2026-10-06T09:30:00Z`
- **Elapsed Time**: 0.0 days
- **Consecutive Calendar Days Completed**: 0 days
- **Consecutive Calendar Days Required**: 14 days
- **Days Remaining**: 14 days
- **Observation Status**: IN PROGRESS

The timestamp is immutable and cannot be backdated.

---

## 5. Shadow Observation Status

Operational metrics collected for both models during live execution:
- **Total Production Requests**: 0
- **Successful Shadow Candidate Predictions**: 0
- **Shadow Exceptions (Isolated)**: 0
- **Shadow Timeouts (Isolated)**: 0
- **Candidate Latency ($P_{50}, P_{95}, P_{99}$)**: `DATA_NOT_AVAILABLE` (Awaiting live request volume)
- **User Response Impact**: **0 (Zero)**

The state is recorded in `ml/experiments/phase13_shadow_telemetry.csv`.

---

## 6. Verified Feedback Definition

The project strictly models `Mental_Health_Score` as a continuous survey-based wellbeing index on the domain $[1.0, 10.0]$. It does **not** assert medical, psychiatric, or diagnostic ground truth.

### Feedback Ingestion Lifecycle:
$$\text{SHADOW PREDICTION} \to \text{WAIT FOR VERIFIED OUTCOME} \to \text{FEEDBACK RECEIVED} \to \text{PENDING VERIFICATION} \to \text{VERIFIED} \to \text{USED FOR EVALUATION}$$

### Strict Verification Rules:
1. **Valid Prediction Lineage**: The feedback entry must reference an existing, valid `prediction_id` previously generated by the production API.
2. **Numeric Domain Bounds**: The observed score must fall strictly within $[1.0, 10.0]$. NaN, null, infinite, negative, or scores $> 10.0$ are immediately rejected (`REJECTED`).
3. **No Duplicate Ground Truth**: Multiple submissions for the same `prediction_id` are rejected (`REJECTED / DUPLICATE`).
4. **Unverified Exclusion**: Records marked `PENDING_VERIFICATION` or `RECEIVED` without formal verification are excluded from model evaluation datasets.
5. **Privacy Safeguards**: Feedback payloads must not store student names, emails, phone numbers, student IDs, or location coordinates. Only pseudonymous technical identifiers are stored.

---

## 7. Verified Label Count

A live counter tracks progress against the Phase 12.3 governance threshold:
- **Current Verified Labels**: `0 / 100`
- **Threshold Met**: **FALSE**
- **Data Mode**: `OFFLINE / NO VERIFIED PRODUCTION LABELS`

Progress is tracked truthfully without artificial acceleration.

---

## 8. Champion Online Performance

Because 0 verified post-deployment labels currently exist:
- **Real-World Sample Size**: 0
- **Real-World MAE**: `DATA_NOT_AVAILABLE`
- **Real-World RMSE**: `DATA_NOT_AVAILABLE`
- **Real-World $R^2$**: `DATA_NOT_AVAILABLE`
- **Mean Error**: `DATA_NOT_AVAILABLE`
- **Median Absolute Error**: `DATA_NOT_AVAILABLE`
- **Max Absolute Error**: `DATA_NOT_AVAILABLE`

*(Offline benchmark reference: $R^2 = 0.9275$, $\text{RMSE} = 0.3596$, $\text{MAE} = 0.2490$ on the historical test partition).*

---

## 9. Candidate Online Performance

Because 0 verified post-deployment labels currently exist:
- **Real-World Sample Size**: 0
- **Real-World MAE**: `DATA_NOT_AVAILABLE`
- **Real-World RMSE**: `DATA_NOT_AVAILABLE`
- **Real-World $R^2$**: `DATA_NOT_AVAILABLE`
- **Mean Error**: `DATA_NOT_AVAILABLE`
- **Median Absolute Error**: `DATA_NOT_AVAILABLE`
- **Max Absolute Error**: `DATA_NOT_AVAILABLE`

*(Offline clean common holdout benchmark reference: $R^2 = 0.9126$, $\text{RMSE} = 0.4077$, $\text{MAE} = 0.2644$ on the 201 unseen holdout records).*

---

## 10. Paired Production Comparison

Once verified post-deployment labels become available, symmetric paired comparison will be evaluated across identical production requests:
- Paired absolute error difference: $\Delta_{\text{abs}} = |e_{\text{champ}}| - |e_{\text{cand}}|$
- Non-parametric Wilcoxon signed-rank test (minimum $N \ge 30$)
- Paired t-test (normality evaluated via Shapiro-Wilk)

Current Status: `DATA_NOT_AVAILABLE` ($N = 0$).

---

## 11. Conformal Coverage

Offline calibration quantiles are frozen:
- Champion: $q_{80} = 0.4156$, $q_{90} = 0.5942$, $q_{95} = 0.7902$
- Candidate: $q_{80} = 0.4190$, $q_{90} = 0.5984$, $q_{95} = 0.7937$

### Post-Deployment Empirical Coverage Status:
| Nominal Target | Offline Champion | Offline Candidate | Production Champion | Production Candidate | Status |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **80%** | 83.58% | 83.58% | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | PENDING VERIFIED LABELS |
| **90%** | 92.70% | 92.54% | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | PENDING VERIFIED LABELS |
| **95%** | 96.52% | 96.52% | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | PENDING VERIFIED LABELS |

Automatic recalibration using ad-hoc incoming data is **strictly forbidden**.

---

## 12. Drift Analysis

Production monitoring actively tracks drift against the Phase 10 reference statistics (`ml/experiments/phase10_drift_reference_statistics.csv`):
- **Input Features PSI** (Population Stability Index, threshold $> 0.25$): `DATA_NOT_AVAILABLE`
- **Numerical Features KS Tests** (Kolmogorov-Smirnov p-value $< 0.01$): `DATA_NOT_AVAILABLE`
- **Categorical Features TVD** (Total Variation Distance $> 0.15$): `DATA_NOT_AVAILABLE`
- **Prediction Drift**: `DATA_NOT_AVAILABLE`
- **Interval Width Drift**: `DATA_NOT_AVAILABLE`
- **Error Drift**: `DATA_NOT_AVAILABLE` (Awaiting verified labels)

Monitoring infrastructure is healthy and initialized. No spurious synthetic drift alarms are triggered.

---

## 13. Subgroup Analysis

Descriptive tracking covers demographic and behavioral cohorts:
- `Gender` (Female, Male, Other)
- `Academic_Level` (High School, Undergraduate, Graduate)
- `Stress_Level` (Low, Medium, High)
- `Most_Used_Platform` (Instagram, YouTube, TikTok)
- `Purpose_Of_Use` (Education, Entertainment, Social)

Current Status: `NO REAL PRODUCTION OBSERVATIONS AVAILABLE` ($N = 0$ for all cohorts).  
When sample sizes reach statistical validity ($N \ge 30$), metrics will report observed subgroup performance without asserting clinical fairness guarantees.

---

## 14. Reliability & Failure Isolation Verification

Failure isolation was experimentally tested and verified:
1. **Candidate Exception Simulation**: When `shadow_manager.simulate_exception = True` was triggered, the Candidate failed gracefully, logged a warning, incremented `shadow_exceptions`, and the Champion synchronously returned HTTP 200 with identical predictions.
2. **Candidate Timeout Simulation**: When `shadow_manager.simulate_timeout = True` was triggered, the Candidate timed out safely, incremented `shadow_timeouts`, and the Champion response was completely unaffected.
3. **Artifact Integrity**:
   - Production Champion (`models/phase5_tuned_extra_trees.joblib`): `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8` (VERIFIED MATCH).
   - Candidate v1.2 (`models/candidate_v1_2_revalidated.joblib`): `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc` (VERIFIED MATCH).
   - Champion Calibration: `22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b` (VERIFIED MATCH).
   - Candidate Calibration: `b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af` (VERIFIED MATCH).

---

## 15. Promotion Gate

Evaluation of the 11 Phase 13 Governance Gates (`ml/experiments/phase13_governance_gate.csv`):

| Gate Dimension | Requirement | Current State | Gate Status | Blocker Reason |
| :--- | :--- | :--- | :---: | :--- |
| **Technical Integrity** | Champion & Candidate hash match | VERIFIED | **PASS** | None |
| **Failure Isolation** | Candidate error does not alter user response | VERIFIED | **PASS** | None |
| **Shadow Routing** | Candidate never returned to user | VERIFIED | **PASS** | None |
| **Verified Production Labels** | $\ge 100$ verified post-deployment labels | 0 / 100 | **FAIL** | Insufficient verified labels (0 of 100) |
| **Shadow Observation Duration** | $\ge 14$ consecutive calendar days | 0 / 14 days | **FAIL** | Observation window in progress (14 days left) |
| **Real-World Model Evaluation** | Paired evaluation on $\ge 100$ labels | DATA_NOT_AVAILABLE | **FAIL** | Pending verified post-deployment labels |
| **Uncertainty Evaluation** | Empirical coverage on verified labels | DATA_NOT_AVAILABLE | **FAIL** | Pending verified post-deployment labels |
| **Drift Governance** | No critical unresolved drift | Healthy / Baseline | **PASS** | Baseline established in Phase 10 |
| **Shadow Reliability** | Zero outages caused by candidate | Healthy | **PASS** | None |
| **Human Approval** | Model Governance Committee signoff | PENDING | **PENDING** | Requires completed shadow & $\ge 100$ labels |
| **Promotion Decision** | ALL GATES MUST PASS | BLOCKED | **BLOCKED** | Premature promotion strictly forbidden |

---

## 16. Human Governance & Limitations

- **No Clinical Claims**: The target represents self-reported survey wellbeing, not clinical pathology or diagnostic risk.
- **No Automatic Promotion**: Even if Candidate exhibits superior offline or early shadow metrics, promotion without formal Model Governance Committee review is architecturally blocked.
- **No Automatic Retraining**: Model retraining cannot occur on raw incoming traffic. Retraining belongs exclusively to future controlled phases.

---

## 17. Final Decision

Candidate v1.2 promotion is **BLOCKED**.  
Phase 13 remains **ACTIVE / IN PROGRESS** as the 14-day shadow window elapses and verified post-deployment observations accumulate.

```
PHASE 13 STATUS:
ACTIVE / IN PROGRESS

Production Champion:
ACTIVE PRODUCTION

Candidate:
CHALLENGER / VALIDATING

Shadow Mechanism:
READY / ACTIVE

Shadow Start:
2026-10-06T09:30:00Z

Shadow Days Completed:
0

Shadow Days Required:
14

Verified Production Labels:
0

Verified Labels Required:
100

Champion Real-World MAE:
DATA_NOT_AVAILABLE

Candidate Real-World MAE:
DATA_NOT_AVAILABLE

Champion Real-World RMSE:
DATA_NOT_AVAILABLE

Candidate Real-World RMSE:
DATA_NOT_AVAILABLE

Champion Real-World R²:
DATA_NOT_AVAILABLE

Candidate Real-World R²:
DATA_NOT_AVAILABLE

Real-World Conformal Coverage:
DATA_NOT_AVAILABLE

Drift Status:
BASELINE_READY / NO_UNRESOLVED_DRIFT

Human Approval:
PENDING

Promotion:
BLOCKED

Champion Modified:
NO

Automatic Retraining:
NO

Automatic Promotion:
NO
```
