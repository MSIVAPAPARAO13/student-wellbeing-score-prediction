# Phase 15: Final Real-World Validation & Model Decision

**Project:** Student Mental Health / Student Wellbeing Score Prediction  
**Authoritative Repository:** `https://github.com/MSIVAPAPARAO13/student-wellbeing-score-prediction` (`main` branch)  
**Execution Date:** October 7, 2026  
**Phase Status:** **DECISION LOCKED / CHAMPION RETAINED**  

---

## Executive Summary

Phase 15 performs the definitive real-world model evaluation to determine whether Candidate v1.2 (`candidate_v1_2_revalidated`) should replace the active production Champion (`phase5_tuned_extra_trees`) using genuine post-deployment evidence.

In accordance with strict project governance rules, the evaluation begins with mandatory eligibility verification:

```
======================================================================
PHASE 15 ELIGIBILITY CHECK: UNFULFILLED
STATUS: PHASE 15 = BLOCKED
REASON: INSUFFICIENT REAL-WORLD EVIDENCE
======================================================================
```

Because the shadow observation window is in progress ($\approx 1.08$ days elapsed of 14 required) and zero verified post-deployment labels have accumulated ($0 / 100$), production ground truth cannot be fabricated. Therefore:

- **FINAL DECISION:** **C. INSUFFICIENT EVIDENCE (RETAIN CHAMPION)**
- **Production Champion:** `phase5_tuned_extra_trees` (ACTIVE PRODUCTION)
- **Candidate Challenger:** `candidate_v1_2_revalidated` (SHADOW / VALIDATING ONLY)
- **Candidate Promotion:** **STRICTLY BLOCKED**
- **Human Approval:** **REQUIRED (PENDING)**
- **Models Modified:** **NONE (0 weights, parameters, or artifacts modified)**
- **Models Retrained:** **NONE (Retraining strictly disabled)**

---

## 1. Eligibility Check (Prerequisites Verification)

Before conducting model comparison, the mandatory Phase 15 prerequisites were audited against live governance state:

| Prerequisite Gate | Governance Requirement | Observed Value | Gate Status | Detail / Action Required |
| :--- | :---: | :---: | :---: | :--- |
| **Shadow Observation Duration** | $\ge 14$ consecutive days | $\approx 1.08 / 14$ days | **BLOCKED** | Window active since `2026-10-06T09:30:00Z`; 13 calendar days remaining |
| **Verified Post-Deployment Labels** | $\ge 100$ verified outcomes | $0 / 100$ labels | **BLOCKED** | Real-world post-deployment evidence accumulation in progress |
| **Paired Production Observations** | $\ge 100$ matched pairs | $0$ pairs | **BLOCKED** | Matched Champion and Candidate production inferences |
| **Ground Truth Provenance** | Genuinely post-deployment | `DATA_NOT_AVAILABLE` | **BLOCKED** | No post-deployment labels submitted to date |
| **Historical Data Firewall** | Exclude offline data | $4,998$ records quarantined | **PASS** | Historical records strictly prevented from counting as production evidence |

### Eligibility Gate Conclusion:
```
PHASE 15 = BLOCKED
REASON = INSUFFICIENT REAL-WORLD EVIDENCE

Shadow Days:            1.08 / 14 days elapsed (13 calendar days remaining)
Verified Labels:        0 / 100 verified post-deployment outcomes collected
Paired Rows:            0 matched live observations
Remaining Requirements: Complete remaining 13 shadow days, collect >= 100 verified post-deployment labels
```

---

## 2. Real Production Data Discipline

In accordance with Section 2, the 4,998 historical offline records (and 3,998 deduplicated records) are partitioned behind the **Historical Data Firewall**:
- Historical offline records **CANNOT** increment verified production label counts.
- Historical offline records **CANNOT** increment shadow observation duration.
- Historical offline records **CANNOT** populate production evaluation tables.
- All post-deployment metrics truthfully report `DATA_NOT_AVAILABLE` until authentic production ground truth is collected.

---

## 3. Champion vs Candidate Model Comparison

### Evaluated Models:
- **Champion:** `models/phase5_tuned_extra_trees.joblib`  
  - SHA-256: `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8` (100% Invariant)
- **Candidate:** `models/candidate_v1_2_revalidated.joblib`  
  - SHA-256: `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc` (100% Invariant)

### Point Prediction Metrics (Real Production):

| Metric | Champion | Candidate | Target / SLA | Governance Status |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Absolute Error (MAE)** | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | $< 0.25$ | Awaiting $\ge 100$ verified labels |
| **Root Mean Squared Error (RMSE)** | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | $< 0.36$ | Awaiting $\ge 100$ verified labels |
| **R² Determination Coefficient** | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | $> 0.90$ | Awaiting $\ge 100$ verified labels |
| **Average Error (Bias)** | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | $|\text{Bias}| < 0.05$ | Awaiting $\ge 100$ verified labels |
| **Median Absolute Error** | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | Informational | Awaiting $\ge 100$ verified labels |
| **Per-Row Winner Count** | `DATA_NOT_AVAILABLE` | `DATA_NOT_AVAILABLE` | Candidate $> 50\%$ | Awaiting paired live observations |

*(Historical offline metrics—Champion CV MAE 0.2635 vs Candidate CV MAE 0.2502—remain preserved strictly as offline development benchmarks and are not substituted for production metrics).*

---

## 4. Uncertainty Validation (Conformal Coverage Tiers)

Conformal intervals were evaluated using the existing frozen calibration artifacts (`phase7_1_conformal_calibration.json` and `candidate_v1_2_conformal_calibration.json`) without retraining:

| Nominal Tier | Champion Interval Width | Candidate Interval Width | Production Empirical Coverage | Status |
| :---: | :---: | :---: | :---: | :---: |
| **80% Nominal** | $0.8312$ ($2 \times 0.4156$) | $0.8488$ ($2 \times 0.4244$) | `DATA_NOT_AVAILABLE` | Awaiting ground truth |
| **90% Nominal** | $1.1884$ ($2 \times 0.5942$) | $1.1968$ ($2 \times 0.5984$) | `DATA_NOT_AVAILABLE` | Awaiting ground truth |
| **95% Nominal** | $1.5804$ ($2 \times 0.7902$) | $1.5576$ ($2 \times 0.7788$) | `DATA_NOT_AVAILABLE` | Awaiting ground truth |

---

## 5. Basic Operational Check & Latency SLA

Evaluated against the authoritative production latency SLA (**Warm inference $P_{95} < 150\text{ ms}$**):

- **Candidate Benchmark $P_{95}$:** **$77.58\text{ ms}$** (**PASS**, well within the $< 150\text{ ms}$ budget).
- **Live Production $P_{50}$ Latency:** `DATA_NOT_AVAILABLE` (awaiting live request stream).
- **Live Production $P_{95}$ Latency:** `DATA_NOT_AVAILABLE` (awaiting live request stream).
- **Shadow Error / Timeout Rate:** **$0.0\%$** (zero exceptions or timeouts leaked to users; fail-safe isolation verified).

---

## 6. Basic Distribution Drift Check

Using the existing production monitoring implementation:
- **Population Stability Index (PSI):** `DATA_NOT_AVAILABLE`
- **Kolmogorov-Smirnov (KS) Test:** `DATA_NOT_AVAILABLE`
- **Total Variation Distance (TVD):** `DATA_NOT_AVAILABLE`
- **Drift Status:** `DATA_NOT_AVAILABLE` (monitoring subsystem active; awaiting live production traffic).

---

## 7. Final Governance Decision

Selecting from the three allowed outcomes:
- **A. PROMOTE CANDIDATE:** Rejected (prerequisites unfulfilled; zero post-deployment evidence).
- **B. RETAIN CHAMPION:** Active status (Champion retained in active production).
- **C. INSUFFICIENT EVIDENCE:** **SELECTED OUTCOME**.

Governance policy mandates that whenever the Candidate does not demonstrate clear, reliable, statistically verified improvement over 14 production days and 100 labels, the system strictly retains the Champion.

---

## 8. Human Approval & Promotion Policy

Even if Candidate benchmarks showed offline promise:
- **Automatic Retraining:** **DISABLED** (governance policy strictly enforced).
- **Automatic Promotion:** **DISABLED** (governance policy strictly enforced).
- **Human Approval:** **REQUIRED (PENDING)**.
- **Promotion Status:** **STRICTLY BLOCKED**.

---

## 9. Machine-Readable Artifacts Catalog

1. **Governance Report:** [`reports/PHASE15_FINAL_MODEL_DECISION.md`](file:///c:/Users/msiva/Music/Mental-Health-Score/reports/PHASE15_FINAL_MODEL_DECISION.md)
2. **Audit Notebook:** [`ml/notebooks/15_final_model_decision.ipynb`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/notebooks/15_final_model_decision.ipynb)
3. **Structured CSV Summary:** [`ml/experiments/phase15_final_decision.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase15_final_decision.csv)
4. **Automated Test Suite:** [`tests/test_phase15_final_decision.py`](file:///c:/Users/msiva/Music/Mental-Health-Score/tests/test_phase15_final_decision.py) (12 passed)

---

## 10. Authoritative Summary Matrix

```
======================================================================
PRODUCTION MODEL DECISION REPORT — PHASE 15
======================================================================
Production Champion: phase5_tuned_extra_trees
Candidate:           candidate_v1_2_revalidated
Shadow days:         1.08 / 14 days elapsed (13 calendar days remaining)
Verified labels:     0 / 100 post-deployment labels collected
Paired rows:         0 paired observations
Champion MAE:        DATA_NOT_AVAILABLE
Candidate MAE:       DATA_NOT_AVAILABLE
Champion RMSE:       DATA_NOT_AVAILABLE
Candidate RMSE:      DATA_NOT_AVAILABLE
Champion R²:         DATA_NOT_AVAILABLE
Candidate R²:        DATA_NOT_AVAILABLE
Conformal coverage:  DATA_NOT_AVAILABLE
P95 latency:         77.58 ms (Benchmark) / DATA_NOT_AVAILABLE (Live)
Drift:               DATA_NOT_AVAILABLE
FINAL DECISION:      C. INSUFFICIENT EVIDENCE (RETAIN CHAMPION)
Human approval:      PENDING (REQUIRED)
======================================================================
```
