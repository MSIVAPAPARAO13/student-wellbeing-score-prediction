# Phase 14: Real-World Model Decision, Validation & Controlled Promotion

**Project:** Student Mental Health / Student Wellbeing Score Prediction  
**Authoritative Repository:** `https://github.com/MSIVAPAPARAO13/student-wellbeing-score-prediction` (`main` branch)  
**Phase:** 14 — Real-World Model Decision, Validation & Controlled Promotion  
**Audit & Execution Date:** October 7, 2026  
**Final Governance Status:** **COMPLETE — INSUFFICIENT EVIDENCE (CHAMPION RETAINED)**  

---

## Executive Summary & Final Governance Decision

Phase 14 executes the formal production model decision gate governing whether **Candidate v1.2** (`models/candidate_v1_2_revalidated.joblib`) may be promoted to replace the frozen **Production Champion** (`models/phase5_tuned_extra_trees.joblib`) or whether the Champion must be retained in production.

Under the strict governance mandate established in `models/model_registry.json`, `app/governance.py`, and `reports/PHASE13_REAL_WORLD_PRODUCTION_VALIDATION.md`:
1. Candidate promotion requires satisfying **18 comprehensive promotion gates**, including completing $\ge 14$ consecutive calendar days under live shadow observation, accumulating $\ge 100$ verified post-deployment ground-truth labels, proving paired statistical and practical superiority, empirically validating conformal coverage, verifying absence of critical drift, and obtaining explicit human governance sign-off.
2. Offline historical data (the 4,998 survey records from Phases 1–12.2) **cannot** be counted as post-deployment production validation evidence.
3. Automatic promotion and automatic retraining are strictly **DISABLED**.

### Final Decision Determination:
```
========================================================================================
FINAL PHASE 14 DECISION: OPTION C — INSUFFICIENT EVIDENCE
----------------------------------------------------------------------------------------
Production Champion:    ACTIVE PRODUCTION (models/phase5_tuned_extra_trees.joblib)
Candidate v1.2:         CHALLENGER / VALIDATING (models/candidate_v1_2_revalidated.joblib)
Shadow Observation:     IN PROGRESS (0 / 14 calendar days elapsed; started 2026-10-06T09:30:00Z)
Verified Live Labels:   0 / 100 accumulated (DATA_NOT_AVAILABLE for live metrics)
Promotion State:        STRICTLY BLOCKED
Automatic Promotion:    DISABLED
Automatic Retraining:   DISABLED
Human Approval State:   PENDING
Rollback Architecture:  VERIFIED & READY (Champion retained; no rollback required)
========================================================================================
```

---

## A. Phase 13 Gate Verification

Before initiating any Phase 14 decision routines, the repository was audited against all 10 mandatory Phase 13 eligibility gates. Because 7 of the 10 gates are blocked, Candidate promotion is strictly blocked.

| Gate | Requirement | Required Threshold | Current Observed Value | Status | Evidence / Blocker Reason |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **A. Shadow Period** | Consecutive calendar days under shadow | $\ge 14$ days | **0 days** (~0.8 days elapsed) | **BLOCKED** | Shadow observation window initiated `2026-10-06T09:30:00Z`; 14 days remaining. |
| **B. Verified Labels** | Genuinely new verified post-deployment labels | $\ge 100$ labels | **0 labels** | **BLOCKED** | Zero post-deployment ground-truth labels accumulated. Offline data strictly separated. |
| **C. Shadow Eval** | Parallel shadow prediction execution | Completed run | **IN PROGRESS** (0 requests logged) | **BLOCKED** | Telemetry operational; awaiting production request volume. |
| **D. Paired Outcomes** | Paired live predictions with verified label | $\ge 100$ rows | **0 rows** (`DATA_NOT_AVAILABLE`) | **BLOCKED** | No paired real-world observations available. |
| **E. Real Point Metrics** | Live MAE, RMSE, $R^2$ from verified labels | Computable | `DATA_NOT_AVAILABLE` | **BLOCKED** | Cannot compute real-world error metrics without ground truth. |
| **F. Real Conformal Cov** | Empirical post-deployment coverage evaluation | Computable | `DATA_NOT_AVAILABLE` | **BLOCKED** | Empirical coverage requires verified post-deployment outcomes. |
| **G. Failure Isolation** | Candidate faults have 0 impact on Champion | 100% Isolated | **100% Isolated (PASS)** | **PASS** | Non-blocking exception handling verified in `app/governance.py`. |
| **H. Drift Governance** | Absence of unresolved critical population drift | No critical drift | **BASELINE_READY (PASS)** | **PASS** | Reference baseline established; status `NO_UNRESOLVED_DRIFT`. |
| **I. Governance Records** | Registry integrity & cryptographic hashes | Verified | **VERIFIED (PASS)** | **PASS** | Champion (`a012e7a1...`) and Candidate (`aad2f208...`) match exactly. |
| **J. Human Approval** | Sign-off from Model Governance Committee | Human Approved | **PENDING** | **BLOCKED** | Requires satisfied shadow window and verified label thresholds. |

---

## B. Phase 14 Work Completed

1. **Eligibility Audit:** Created `reports/PHASE14_READINESS_CHECK.md` and machine-readable `ml/experiments/phase14/phase14_readiness_gate.csv` formally auditing Phase 13 eligibility gates.
2. **Notebook-First Implementation:** Built and executed `ml/notebooks/14_production_model_decision.ipynb` through `nbconvert` with **zero cell errors**, performing data provenance auditing, statistical comparisons, conformal checks, latency evaluation, drift monitoring, and formal gate resolution.
3. **Machine-Readable Artifacts:** Created complete audit CSVs in `ml/experiments/phase14/`:
   - `phase14_readiness_gate.csv`
   - `phase14_promotion_gate.csv`
   - `phase14_model_comparison.csv`
   - `phase14_conformal_validation.csv`
   - `phase14_latency_reliability.csv`
   - `phase14_drift_summary.csv`
   - `phase14_production_evaluation.csv`
4. **Comprehensive Test Suite:** Added `tests/test_phase14_decision_gate.py` with 10 unit tests covering artifact immutability, data provenance separation, zero-label blocking, statistical CI rules, formal gate evaluation, and shadow isolation. All 114 test suite tests pass.
5. **Documentation & Walkthrough:** Updated `WALKTHROUGH.md` and `README.md` to document the Phase 14 decision and governance invariants.

---

## C. Real Production Dataset Size

- **Historical Offline Records:** 4,998 unique student survey records from Phases 1–12.2. These records are strictly cataloged as offline development data and **0 historical records** are counted toward production validation.
- **Incoming Production Telemetry:** 0 requests recorded in persistent storage.
- **Verified Post-Deployment Labels:** **0 / 100 labels**.
- **Paired Evaluation Dataset Size:** **0 rows** (`ml/experiments/phase14/phase14_production_evaluation.csv`).

---

## D & E. Champion & Candidate Real-World Performance Comparison

Metrics are evaluated with strict provenance separation: historical clean holdout metrics (201 records) are shown as reference, while live production metrics reflect actual ground truth availability.

| Metric | Offline Champion Ref | Offline Candidate Ref | Offline Difference | Production Champion | Production Candidate | Production Difference | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **MAE** | 0.263506 | 0.250220 | -0.013285 | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | **BLOCKED** |
| **RMSE** | 0.407234 | 0.333045 | -0.074190 | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | **BLOCKED** |
| **$R^2$** | 0.909767 | 0.939649 | +0.029882 | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | **BLOCKED** |
| **Median AE** | 0.178400 | 0.188000 | +0.009600 | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | **BLOCKED** |
| **Max AE** | 2.080200 | 1.380000 | -0.700200 | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | **BLOCKED** |
| **Mean Error** | -0.002367 | +0.008550 | +0.010917 | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | **BLOCKED** |
| **Win Count** | 115 (57.2%) | 86 (42.8%) | N/A | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | **BLOCKED** |
| **Tie Count** | 0 | 0 | 0 | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | **BLOCKED** |

---

## F. Statistical Comparison & Superiority Gate

Under governance rules, Candidate promotion cannot occur merely because point metrics ($R^2$ or $\text{MAE}$) are numerically superior. Paired statistical significance and practical effect magnitude must be demonstrated.

1. **Bootstrap 95% Confidence Interval for $\Delta\text{MAE}$:**
   - Offline Clean Evaluation: $[-0.0336, 0.0071]$. Because this confidence interval crosses zero, statistical superiority cannot be claimed.
   - Production Evaluation: `DATA_NOT_AVAILABLE` (requires $\ge 100$ verified production labels).
2. **Paired Statistical Tests:**
   - Offline Wilcoxon Signed-Rank Test: $W = 8986.0$, $p = 0.1584$ ($p > 0.05$).
   - Offline Permutation Test: $p = 0.3033$ ($p > 0.05$).
   - Production Paired Test: `DATA_NOT_AVAILABLE`.
3. **Practical Improvement Threshold:**
   - Governance Requirement: $\Delta\text{MAE} \le -0.05$ ($\ge 0.05$ point MAE reduction).
   - Offline Observed Difference: $-0.0133$ (Fails threshold).
   - Production Observed Difference: `DATA_NOT_AVAILABLE`.
4. **Statistical Determination:**
   - Offline Status: `NUMERICALLY BETTER — NOT STATISTICALLY CONCLUSIVE`.
   - Production Status: `INSUFFICIENT EVIDENCE (BLOCKED)`.

---

## G. Real-World Conformal Uncertainty Validation

Conformal calibration parameters were extracted from authoritative artifacts:
- Champion: `models/phase7_1_conformal_calibration.json`
- Candidate: `models/candidate_v1_2_conformal_calibration.json`

| Nominal Level | Offline Champion Cov | Offline Candidate Cov | Production Champion Cov | Production Candidate Cov | Mean Interval Width | Interval Failures | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **80%** | 85.07% | 85.57% | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | **BLOCKED** |
| **90%** | 92.04% | 91.04% | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | **BLOCKED** |
| **95%** | 94.03% | 96.02% | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | **BLOCKED** |

*Note: Historical offline 92.70% coverage is treated strictly as an offline reference. Live production empirical coverage requires verified post-deployment labels.*

---

## H. Latency & Operational Reliability Comparison

Telemetry and benchmark analysis confirm candidate execution remains safely isolated from production serving. The authoritative production SLA established in Phase 12.3 (Gate 11) and Phase 8 (Table 12) defines a single-call point prediction latency budget of **P95 < 150 ms**:

| Operational Metric | Offline Benchmark Reference | Production Telemetry | Status | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **P50 Latency** | Champ: 95.83ms / Cand: 59.07ms | `DATA_NOT_AVAILABLE` | AWAITING_TRAFFIC | Benchmarked sub-100ms inference |
| **P95 Latency** | Champ: 115.10ms / Cand: 77.58ms | `DATA_NOT_AVAILABLE` | AWAITING_TRAFFIC | Candidate benchmark 77.58ms satisfies < 150ms SLA |
| **P99 Latency** | Champ: 122.79ms / Cand: 82.77ms | `DATA_NOT_AVAILABLE` | AWAITING_TRAFFIC | Sub-150ms tail latency |
| **Timeout Rate** | 0.0% | 0.0% | **PASS** | Zero shadow timeouts |
| **Exception Rate** | 0.0% | 0.0% | **PASS** | Zero shadow exceptions |
| **Candidate Failure Impact**| 0 events | 0 events | **PASS** | 100% isolated non-blocking execution |

---

## I. Production Population Drift Governance

Drift telemetry was evaluated using the Phase 10 monitoring implementation (`app/monitoring.py`):
- **Input Feature Numerical Drift (KS Test):** Threshold $p < 0.01$. Baseline established.
- **Input Feature Categorical Drift (TVD):** Threshold $> 0.15$. Baseline established.
- **Population Drift Index (PSI):** Threshold $> 0.25$. Baseline established.
- **Input Data Quality Checks:** Range and categorical enums enforced strictly via Pydantic; zero violations.
- **Overall Drift Classification:** **`NO_UNRESOLVED_DRIFT` (PASS)**.

---

## J. Formal 18-Gate Promotion Matrix

All 18 governance promotion gates evaluated from real evidence:

| Gate | Requirement | Actual Observed Value | Status | Evidence Source |
| :---: | :--- | :---: | :---: | :--- |
| **1** | 14-day shadow observation | 0 days (~0.8 days elapsed) | **BLOCKED** | `phase13_shadow_telemetry.csv` (started `2026-10-06T09:30:00Z`) |
| **2** | $\ge 100$ verified post-deployment labels | 0 verified labels | **BLOCKED** | `phase13_verified_label_summary.csv` |
| **3** | Statistical superiority (CI > 0; p < 0.05) | `DATA_NOT_AVAILABLE` | **BLOCKED** | Offline CI spans zero; live CI not computable |
| **4** | Practical improvement ($\Delta\text{MAE} \le -0.05$) | `DATA_NOT_AVAILABLE` | **BLOCKED** | Offline difference $-0.0133$; live diff not computable |
| **5** | Production MAE improvement | `DATA_NOT_AVAILABLE` | **BLOCKED** | Requires $\ge 100$ verified post-deployment labels |
| **6** | Production RMSE improvement | `DATA_NOT_AVAILABLE` | **BLOCKED** | Requires $\ge 100$ verified post-deployment labels |
| **7** | Production $R^2$ improvement | `DATA_NOT_AVAILABLE` | **BLOCKED** | Requires $\ge 100$ verified post-deployment labels |
| **8** | Conformal 80% empirical coverage | `DATA_NOT_AVAILABLE` | **BLOCKED** | Requires verified production outcomes |
| **9** | Conformal 90% empirical coverage | `DATA_NOT_AVAILABLE` | **BLOCKED** | Requires verified production outcomes |
| **10** | Conformal 95% empirical coverage | `DATA_NOT_AVAILABLE` | **BLOCKED** | Requires verified production outcomes |
| **11** | Interval width non-degrading | `DATA_NOT_AVAILABLE` | **BLOCKED** | Requires post-deployment conformal predictions |
| **12** | Latency budget (P95 $< 150$ms / Phase 12.3 & 8 SLA) | 77.58ms (Benchmark) / `DATA_NOT_AVAILABLE` (Live) | **PASS** | Candidate benchmark 77.58ms satisfies authoritative $< 150$ms SLA; live telemetry awaiting traffic |
| **13** | Error rate isolation (0% crash impact) | 0.0% (Zero shadow crashes) | **PASS** | Candidate execution 100% isolated |
| **14** | Drift status ($\text{PSI} < 0.25$) | `NO_UNRESOLVED_DRIFT` | **PASS** | Baseline active in `app/monitoring.py` |
| **15** | Feature schema compatibility (12 features) | 100% Compatible | **PASS** | 12 survey features identical across models |
| **16** | Artifact cryptographic hash integrity | MATCHED (`a012e7a1...`, `aad2f208...`) | **PASS** | Exact SHA-256 match verified |
| **17** | SHAP explainability compatibility | 100% Compatible | **PASS** | TreeExplainer succeeds across all 12 dimensions |
| **18** | Governance approval (Human sign-off) | PENDING | **BLOCKED** | Requires satisfied observation window and labels |

**Summary:** 6 Passed | 12 Blocked | Overall: **BLOCKED**.

---

## K. Final Decision

Because 12 of the 18 promotion gates are unresolved due to the in-progress observation window (0 / 14 days) and absence of ground-truth labels (0 / 100 labels):

### **DECISION: OPTION C — INSUFFICIENT EVIDENCE**
- **Production Champion:** RETAINED as ACTIVE PRODUCTION (`models/phase5_tuned_extra_trees.joblib`).
- **Candidate v1.2:** RETAINED as CHALLENGER / VALIDATING (`models/candidate_v1_2_revalidated.joblib`).
- **Promotion:** STRICTLY BLOCKED.
- **Action:** Continue controlled shadow observation until 14 full consecutive calendar days elapse and $\ge 100$ verified post-deployment labels are accumulated.

---

## L. Human Approval Status

- **Status:** **PENDING**
- **Policy:** Explicit human approval from the Model Governance Committee is mandatory for production promotion. Automatic promotion is disabled. Human approval cannot be granted while mandatory eligibility gates remain blocked.

---

## M. Rollback State

- **Rollback Architecture:** Fully operational.
- **Action Required:** NONE. Because Candidate promotion did not occur, the production Champion was never modified or replaced.
- **Rollback Artifact:** `models/phase5_tuned_extra_trees.joblib` (SHA-256: `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8`).

---

## N. Artifact Hash Verification

Pre-evaluation and post-evaluation cryptographic signatures verified with zero drift:

| Artifact | File Path | Expected SHA-256 Hash | Post-Evaluation SHA-256 Hash | Integrity Status |
| :--- | :--- | :---: | :---: | :---: |
| **Champion Model** | `models/phase5_tuned_extra_trees.joblib` | `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8` | `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8` | **MATCHED (INVARIANT)** |
| **Candidate Model** | `models/candidate_v1_2_revalidated.joblib` | `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc` | `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc` | **MATCHED (INVARIANT)** |
| **Champion Calib** | `models/phase7_1_conformal_calibration.json` | `22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b` | `22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b` | **MATCHED (INVARIANT)** |
| **Candidate Calib** | `models/candidate_v1_2_conformal_calibration.json` | `b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af` | `b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af` | **MATCHED (INVARIANT)** |

Zero model artifacts were retrained, replaced, or modified.

---

## O. Pytest Result

The automated test suite was executed against the repository:
```
114 passed, 10 warnings in 96.12s
```
All existing tests (Phases 1–13A) and all 10 new Phase 14 governance tests in `tests/test_phase14_decision_gate.py` passed with **zero failures and zero regressions**.

---

## P. Smoke-Test Result

Smoke testing executed via `tests/test_smoke_production.py` and FastAPI TestClient confirms:
- `/health` endpoint returns `200 OK` with production Champion status (`phase5_tuned_extra_trees`).
- `/predict` returns valid predictions and conformal intervals from the Champion model.
- `/explain` generates observational SHAP contributions across all 12 survey features.
- Candidate shadow execution runs asynchronously with 100% failure isolation.

---

## Q. Files Created & Modified

### Created Files:
1. `reports/PHASE14_READINESS_CHECK.md` — Formal audit of Phase 13 operational eligibility gates.
2. `reports/PHASE14_PRODUCTION_MODEL_DECISION.md` — Authoritative Phase 14 governance decision report.
3. `ml/notebooks/14_production_model_decision.ipynb` — Executed notebook with zero cell errors.
4. `ml/experiments/phase14/phase14_readiness_gate.csv` — Machine-readable Phase 13 eligibility audit.
5. `ml/experiments/phase14/phase14_promotion_gate.csv` — Machine-readable 18-gate promotion matrix.
6. `ml/experiments/phase14/phase14_model_comparison.csv` — Machine-readable model performance comparison.
7. `ml/experiments/phase14/phase14_conformal_validation.csv` — Machine-readable conformal coverage comparison.
8. `ml/experiments/phase14/phase14_latency_reliability.csv` — Machine-readable latency and reliability telemetry.
9. `ml/experiments/phase14/phase14_drift_summary.csv` — Machine-readable population drift summary.
10. `ml/experiments/phase14/phase14_production_evaluation.csv` — Machine-readable paired evaluation dataset template.
11. `tests/test_phase14_decision_gate.py` — Unit test suite for Phase 14 governance and decision rules.

### Modified Files:
1. `WALKTHROUGH.md` — Added Section 18 documenting Phase 14 real-world decision methodology and gate matrix.
2. `README.md` — Updated project status to reflect `Phase 14 COMPLETE — INSUFFICIENT EVIDENCE (CHAMPION RETAINED, CANDIDATE SHADOW IN PROGRESS)`.
