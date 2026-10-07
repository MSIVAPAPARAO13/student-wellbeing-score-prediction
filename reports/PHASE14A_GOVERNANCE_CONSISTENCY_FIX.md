# Phase 14A: Governance Consistency Fix, Latency Gate Correction & Shadow Validation Continuation

**Project:** Student Mental Health / Student Wellbeing Score Prediction  
**Authoritative Repository:** `https://github.com/MSIVAPAPARAO13/student-wellbeing-score-prediction` (`main` branch)  
**Execution Date:** October 7, 2026  
**Phase Status:** **COMPLETE — GOVERNANCE CONSISTENCY VERIFIED & ENFORCED**  

---

## A. Scope & Objective

Phase 14A was initiated to investigate and resolve an internal governance inconsistency identified in the Phase 14 promotion matrix regarding **Gate 12 (Latency Budget)**, verify that all documentation and machine-readable artifacts remain 100% consistent, and preserve the system in a controlled shadow-validation state without modifying model weights, fabricating live data, or prematurely authorizing promotion.

---

## B. Repository State Inspected

The following project files were audited prior to applying any modifications:
1. `reports/PHASE14_PRODUCTION_MODEL_DECISION.md` — Authoritative Phase 14 decision report.
2. `reports/PHASE14_READINESS_CHECK.md` — Formal audit of Phase 13 eligibility gates.
3. `ml/experiments/phase14/phase14_promotion_gate.csv` — Machine-readable 18-gate matrix.
4. `ml/experiments/phase14/phase14_latency_reliability.csv` — Operational telemetry and benchmark summary.
5. `reports/PHASE12_3_CANDIDATE_VALIDATION_GATE.md` — Phase 12.3 candidate validation report.
6. `ml/experiments/phase12_3_validation_gate.csv` — Phase 12.3 authoritative gate matrix.
7. `reports/phase8/PHASE8_PRODUCTION_API_REPORT.md` — Production FastAPI benchmarking and SLA report.
8. `reports/phase9/PHASE9_CLOUD_DEPLOYMENT_REPORT.md` — Cloud deployment SLA report.
9. `reports/phase4/PHASE4_COMPUTATIONAL_BENCHMARK.md` — Raw algorithmic complexity benchmark report.
10. `app/governance.py` & `app/monitoring.py` — Shadow serving and drift monitoring engines.
11. `models/model_registry.json` — Central governance policy registry.

---

## C. Original Gate 12 Inconsistency

In the initial Phase 14 promotion matrix ([reports/PHASE14_PRODUCTION_MODEL_DECISION.md](file:///c:/Users/msiva/Music/Mental-Health-Score/reports/PHASE14_PRODUCTION_MODEL_DECISION.md) and [phase14_promotion_gate.csv](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase14/phase14_promotion_gate.csv)):
- **Requirement Stated:** `P95 latency <= 50.0 ms / benchmark`
- **Observed Candidate Benchmark:** `P95 = 77.58 ms`
- **Reported Gate Status:** `PASS`

### The Contradiction:
Mathematically and operationally, $77.58\text{ ms} > 50.0\text{ ms}$. If the governance requirement were strictly $P_{95} \le 50.0\text{ ms}$, an observed value of $77.58\text{ ms}$ **cannot** be marked `PASS`. Marking it `PASS` without reconciling the threshold represented an internal governance contradiction.

---

## D. Authoritative Latency Policy Discovered (Resolution Case B)

A systematic search across earlier lifecycle phases was conducted to determine whether an authoritative production latency SLA was already established in the repository:

1. **Phase 12.3 Authoritative Gate Matrix:**
   In [ml/experiments/phase12_3_validation_gate.csv](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase12_3_validation_gate.csv) (Row 12) and [reports/PHASE12_3_CANDIDATE_VALIDATION_GATE.md](file:///c:/Users/msiva/Music/Mental-Health-Score/reports/PHASE12_3_CANDIDATE_VALIDATION_GATE.md) (Gate 11):
   - **Requirement:** `Warm inference latency satisfies production SLA (< 150ms P95)`
   - **Observed Evidence:** `Candidate warm median 59.07ms, P95 77.58ms vs Champ P95 115.10ms`
   - **Gate Status:** `PASS`
2. **Phase 8 Production Microservice Benchmarks:**
   In [reports/phase8/PHASE8_PRODUCTION_API_REPORT.md](file:///c:/Users/msiva/Music/Mental-Health-Score/reports/phase8/PHASE8_PRODUCTION_API_REPORT.md) (Section 8.2, Table 12):
   - `POST /predict (Warm)` Median Latency SLA Target: $< 150\text{ ms}$ (Observed: $117.80\text{ ms}$, Status: `PASSED`).
   - `POST /predict (Warm)` Mean Latency SLA Target: $< 200\text{ ms}$ (Observed: $120.11\text{ ms}$, Status: `PASSED`).
3. **Phase 9 Cloud SLA Specifications:**
   In [reports/phase9/PHASE9_CLOUD_DEPLOYMENT_REPORT.md](file:///c:/Users/msiva/Music/Mental-Health-Score/reports/phase9/PHASE9_CLOUD_DEPLOYMENT_REPORT.md) (Section 18, Table):
   - `POST /predict (Warm Median)` Production SLA: $< 200\text{ ms}$ (Observed: $117.8\text{ ms}$, Status: `PASSED`).
4. **Origin of the Erroneous 50 ms String:**
   In Phase 4 ([reports/phase4/PHASE4_COMPUTATIONAL_BENCHMARK.md](file:///c:/Users/msiva/Music/Mental-Health-Score/reports/phase4/PHASE4_COMPUTATIONAL_BENCHMARK.md)), the benchmark evaluated isolated tree traversal speed ($34.4\text{ ms}$ per 1,000 samples, or $0.034\text{ ms}$ per sample) against a generic web microbenchmark ($P_{99} < 50\text{ ms}$). During the initial Phase 14 promotion matrix drafting, this raw model benchmark was erroneously conflated with the full end-to-end pipeline SLA ($< 150\text{ ms}$ P95).

**Conclusion (Case B Applied):** The project already has an authoritative, documented production SLA established in Phase 12.3 and Phase 8: **$P_{95} < 150\text{ ms}$ for warm single-call inference**.

---

## E. Corrected Gate 12 Decision

Under the authentic, documented SLA policy:
- **Requirement:** `Warm inference latency satisfies production SLA (P95 < 150 ms)`
- **Observed Candidate Benchmark:** `77.58 ms`
- **Observed Champion Benchmark:** `115.10 ms`
- **Live Production Telemetry:** `DATA_NOT_AVAILABLE` (0 requests processed in ongoing shadow observation)
- **Status Determination:**
  - Candidate benchmark ($77.58\text{ ms} < 150.0\text{ ms}$) satisfies the authoritative budget $\rightarrow$ **PASS (Benchmark SLA Met)**.
  - Live production latency remains honestly cataloged as `DATA_NOT_AVAILABLE` until live request volume accumulates.
  - Strict compliance logic verified: If an imaginary $50.0\text{ ms}$ SLA were enforced, Candidate would fail ($77.58\text{ ms} > 50.0\text{ ms}$); under the true $< 150\text{ ms}$ policy, it passes.

---

## F. Updated 18-Gate Promotion Matrix

All 18 promotion gates with the corrected Gate 12:

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

**Summary:** 6 Passed | 12 Blocked | Overall Promotion Decision: **STRICTLY BLOCKED**.

---

## G. Production Evidence Status & Provenance Separation

Strict separation of data categories is rigorously enforced:
- **Historical Offline Data:** 4,998 survey records (Phases 1–12.2) and the clean 201-row common evaluation cohort provide offline benchmarks only. **Zero historical records count toward production validation.**
- **Post-Deployment Ground Truth:** Exactly **0 / 100 verified post-deployment labels** exist.
- **Paired Production Observations:** **0 rows** in `ml/experiments/phase14/phase14_production_evaluation.csv`.
- **Live Error Metrics (MAE, RMSE, $R^2$, Coverage):** Strictly cataloged as **`DATA_NOT_AVAILABLE`**.

---

## H. Champion & Candidate Operational Status

- **Production Champion:** `models/phase5_tuned_extra_trees.joblib`
  - Runtime State: **ACTIVE PRODUCTION** (serving 100% of user traffic on `/predict`)
  - Status in Registry: `CHAMPION`, `APPROVED_FOR_PRODUCTION`
- **Candidate Challenger:** `models/candidate_v1_2_revalidated.joblib`
  - Runtime State: **CHALLENGER / VALIDATING (SHADOW ONLY)**
  - Shadow Execution: Non-blocking, out-of-band asynchronous evaluation
  - User Response Routing: **0% (Zero impact on user predictions)**

---

## I. Artifact Hash Verification

Cryptographic SHA-256 signatures verified with zero drift:

| Artifact | File Path | Authoritative SHA-256 Hash | Inspected Hash | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Champion Model** | `models/phase5_tuned_extra_trees.joblib` | `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8` | `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8` | **MATCHED (INVARIANT)** |
| **Candidate Model** | `models/candidate_v1_2_revalidated.joblib` | `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc` | `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc` | **MATCHED (INVARIANT)** |
| **Champion Calib** | `models/phase7_1_conformal_calibration.json` | `22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b` | `22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b` | **MATCHED (INVARIANT)** |
| **Candidate Calib** | `models/candidate_v1_2_conformal_calibration.json` | `b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af` | `b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af` | **MATCHED (INVARIANT)** |

Zero models were retrained, modified, or re-serialized.

---

## J. Automated Test Results

Expanded test suite in `tests/test_phase14_decision_gate.py` incorporates explicit unit tests for Gate 12 latency policy verification:
1. `test_gate_12_latency_policy_consistency()`: Asserts Gate 12 requirement references the authoritative $< 150\text{ ms}$ P95 SLA and verifies $77.58\text{ ms} < 150.0\text{ ms}$.
2. `test_latency_strict_threshold_exceedance_fails()`: Proves that a metric exceeding a strict threshold (e.g. $77.58\text{ ms} > 50\text{ ms}$) cannot be marked `PASS`.
3. `test_missing_or_undefined_latency_policy_cannot_silently_pass()`: Proves that an undefined or missing policy returns `BLOCKED_POLICY_UNDEFINED` and never `PASS`.

### Pytest Execution:
```bash
pytest -q tests/test_phase14_decision_gate.py
.............                                                            [100%]
13 passed, 4 warnings in 4.87s
```

Full repository test suite:
```bash
pytest -q
117 passed, 10 warnings in 54.12s
```

---

## K. Production Smoke-Test Results

Executed live against running production service (`http://127.0.0.1:8000`):
```
=== INITIATING PRODUCTION SMOKE TESTS AGAINST: http://127.0.0.1:8000 ===
1. Testing GET /health ...
   [PASSED] Health status: ok | Model: phase5_tuned_extra_trees
2. Testing POST /predict ...
   [PASSED] Score: 6.67 | 90% PI: [6.07, 7.26] | Width: 1.1884 (Derived from q90=0.5942)
3. Testing Local Pipeline vs Serving Equivalence ...
   [PASSED] Direct local model prediction: 6.6675 (API match delta: 0.0000)
4. Testing POST /explain ...
   [PASSED] Base value: 6.22 | Top factors identified: 8 positive, 4 negative
5. Testing GET /docs ...
   [PASSED] OpenAPI Swagger docs reachable.
=== ALL PRODUCTION SMOKE TESTS COMPLETED SUCCESSFULLY ===
```

---

## L. Final Governance Status

```
========================================================================================
FINAL PHASE 14A GOVERNANCE AUDIT SUMMARY
----------------------------------------------------------------------------------------
Implementation Status:  COMPLETE
Phase 13:               ACTIVE / IN PROGRESS (0 / 14 calendar days elapsed)
Phase 14:               COMPLETE — GOVERNANCE EVALUATION EXECUTED
Production Champion:    ACTIVE PRODUCTION (models/phase5_tuned_extra_trees.joblib)
Candidate Challenger:   CHALLENGER / VALIDATING (models/candidate_v1_2_revalidated.joblib)
Promotion Decision:     STRICTLY BLOCKED
Formal Decision:        OPTION C — INSUFFICIENT EVIDENCE
Verified Labels:        0 / 100 accumulated
Automatic Retraining:   DISABLED
Automatic Promotion:    DISABLED
Human Approval State:   PENDING
========================================================================================
```

---

## M. Next Permitted Action

The system must remain strictly in **CONTROLLED SHADOW OBSERVATION**.
No promotion, no model replacement, and no retraining is permitted until:
1. $\ge 14$ consecutive calendar days under live shadow observation elapse.
2. $\ge 100$ genuinely new, verified post-deployment labels accumulate.
3. Paired Champion and Candidate observations are collected on live traffic.
4. Production point error metrics (MAE, RMSE, $R^2$) are computed from verified labels.
5. Production empirical conformal coverage is independently calculated.
6. All 18 promotion gates are evaluated from real post-deployment evidence.
7. Formal human approval is explicitly signed off by the Model Governance Committee.
