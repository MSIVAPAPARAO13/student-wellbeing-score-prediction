# Phase 14B: Controlled Shadow Observation, Production Evidence Accumulation & Governance Readiness

**Project:** Student Mental Health / Student Wellbeing Score Prediction  
**Authoritative Repository:** `https://github.com/MSIVAPAPARAO13/student-wellbeing-score-prediction` (`main` branch)  
**Execution Date:** October 7, 2026  
**Phase Status:** **ACTIVE / CONTROLLED SHADOW OBSERVATION IN PROGRESS**  

---

## Executive Summary

Phase 14B establishes and verifies a hardened production-observation layer that safely accumulates genuine evidence required for the eventual governance decision while strictly preserving:
- **Production Champion:** `models/phase5_tuned_extra_trees.joblib` serves 100% of live user traffic via `POST /predict`.
- **Candidate Challenger:** `models/candidate_v1_2_revalidated.joblib` evaluates out-of-band in defensive, isolated shadow execution.
- **Promotion Status:** **STRICTLY BLOCKED** (`Option C — Insufficient Evidence`).
- **Phase Output:** `"REAL-WORLD EVIDENCE ACCUMULATION IN PROGRESS"`.
- **Automatic Retraining:** **DISABLED** (governance policy strictly enforced).
- **Automatic Promotion:** **DISABLED** (governance policy strictly enforced).
- **Human Approval:** **PENDING** (mandatory governance sign-off required).
- **Model Modifications:** **ZERO** (weights, hyperparameters, and hashes remain 100% invariant).

---

## Authoritative Cryptographic Hashes (Bit-for-Bit Verification)

All four production model and conformal calibration artifacts were verified against their authoritative SHA-256 signatures:

| Artifact | File Path | Authoritative SHA-256 | Verification Status |
| :--- | :--- | :--- | :---: |
| **Production Champion** | `models/phase5_tuned_extra_trees.joblib` | `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8` | **MATCH (INVARIANT)** |
| **Candidate Challenger** | `models/candidate_v1_2_revalidated.joblib` | `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc` | **MATCH (INVARIANT)** |
| **Champion Conformal Calib** | `models/phase7_1_conformal_calibration.json` | `22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b` | **MATCH (INVARIANT)** |
| **Candidate Conformal Calib** | `models/candidate_v1_2_conformal_calibration.json` | `b99c8acd2d8fc2aea604228abf1e84365e601021407409ca154ba9b8c29d60af` | **MATCH (INVARIANT)** |

---

## Dynamic Shadow Window & Timeline

Shadow observation duration is calculated dynamically from the actual runtime timestamp relative to the formal launch timestamp:

- **Formal Shadow Launch Timestamp:** `2026-10-06T09:30:00Z`
- **Elapsed Duration:** $\approx 1.06$ days ($\approx 25.5$ hours, dynamically derived from runtime timestamp)
- **Required Duration:** $14$ full consecutive days
- **Remaining Duration:** $\approx 12.94$ days ($13$ calendar days remaining)
- **Days Completed:** $1 / 14$
- **Shadow Status:** `ACTIVE`
- **State Transition Constraint:** Transition to `READY_FOR_DECISION` is strictly forbidden until $\text{elapsed\_days} \ge 14.0$. Clock manipulation and artificial acceleration are strictly prevented.

---

## Historical Data Firewall

To ensure absolute governance integrity, the 4,998 historical offline records (and 3,998 deduplicated records) are partitioned behind a strict Historical Data Firewall:

1. **Firewall Rules:**
   - Historical records cannot increment the verified production label counter.
   - Historical records cannot increment shadow-observation day counts.
   - Historical records cannot populate production evaluation artifacts.
   - Historical records cannot be treated as post-deployment validation evidence.
2. **Automated Interception Mechanisms:**
   - Rejection of entries flagged with `is_historical: True`.
   - Rejection of prediction IDs containing prefixes `hist_`, `offline_`, or `historical_`.
   - Rejection of provenance sources referencing `offline`, `historical`, `dataset_v1`, `dataset_v2`, or `training_data`.
   - Feature-fingerprint matching against SHA-256 digests of all 4,998 offline rows.
3. **Audit Result:** Automated firewall tests in `test_phase14b_shadow_observation.py` pass 100%.

---

## Production Observation Record Layer

An auditable, lightweight observation record was integrated into `app/governance.py` without requiring a heavyweight database:

```python
class ProductionObservationRecord:
    observation_id: str           # Unique observation identifier (e.g. obs_a1b2c3d4e5f6)
    timestamp: str                # ISO-8601 UTC timestamp
    model_version: str            # Identifier of the predicting model
    role: str                     # "champion" or "candidate"
    prediction: float             # Predicted score bounded in [1.0, 10.0]
    request_hash: str             # 16-hex SHA-256 of feature dictionary (NO PII)
    latency_ms: float             # Execution latency in milliseconds
    success: bool                 # Execution success flag
    shadow_execution_status: str  # CHAMPION_ACTIVE, SHADOW_SUCCESS, SHADOW_TIMEOUT, SHADOW_EXCEPTION
    label_status: str             # UNLABELED, VERIFIED, or REJECTED
```

### Privacy & Defensive Isolation Guarantees:
- **Zero Raw Student PII:** Student survey inputs are digested into a 16-hex hash with no identifying tokens.
- **Fail-Safe Isolation:** Candidate exceptions, timeouts, or numerical anomalies are caught within `evaluate_live_shadow()` and recorded with `success=False` without ever interrupting Champion execution or affecting user responses.

---

## Safe Label Ingestion API

A hardened feedback ingestion endpoint was exposed via `POST /governance/feedback`:

- **Input Validation:** Requires `observation_id`, `observed_score` in $[1.0, 10.0]$, and structured `provenance` metadata.
- **Duplicate Prevention:** Identical `observation_id` submissions are rejected immediately.
- **Firewall Integration:** Submissions identified as historical data fail with HTTP 400.
- **Zero Promotion Side Effects:** Incrementing verified labels does not bypass shadow duration or human sign-off gates.
- **Independent Counters:**
  - `verified_label_count`: Tracks confirmed post-deployment outcomes ($0 / 100$).
  - `paired_production_observation_count`: Tracks observations with matched Champion and Candidate inferences ($0 / 100$).

---

## Authoritative Latency SLA Policy

In accordance with Phase 12.3 (Gate 11) and Phase 8 (Table 12):
- **Production Latency SLA:** **Warm inference $P_{95} < 150\text{ ms}$**.
- **Candidate Benchmark:** $77.58\text{ ms}$ satisfies the $< 150\text{ ms}$ threshold.
- **Live Production Latency:** Cataloged as `DATA_NOT_AVAILABLE` until live observation traffic accumulates.

---

## Production Metrics Readiness (Cold-Start Governance State)

All production governance metrics return `DATA_NOT_AVAILABLE` when zero post-deployment labels exist, preventing statistical distortion from empty datasets:

| Metric Category | Metric | Current Value | Target / SLA | Governance Status |
| :--- | :--- | :---: | :---: | :---: |
| **Point Prediction** | MAE | `DATA_NOT_AVAILABLE` | $< 0.25$ | Awaiting $\ge 100$ verified labels |
| **Point Prediction** | RMSE | `DATA_NOT_AVAILABLE` | $< 0.36$ | Awaiting $\ge 100$ verified labels |
| **Point Prediction** | $R^2$ | `DATA_NOT_AVAILABLE` | $> 0.90$ | Awaiting $\ge 100$ verified labels |
| **Point Prediction** | Median Absolute Error | `DATA_NOT_AVAILABLE` | N/A | Awaiting $\ge 100$ verified labels |
| **Point Prediction** | Max Absolute Error | `DATA_NOT_AVAILABLE` | N/A | Awaiting $\ge 100$ verified labels |
| **Point Prediction** | Mean Error (Bias) | `DATA_NOT_AVAILABLE` | N/A | Awaiting $\ge 100$ verified labels |
| **Paired Comparison**| Paired MAE Differences | `DATA_NOT_AVAILABLE` | N/A | Awaiting paired observations |
| **Paired Comparison**| Per-Observation Winner | `DATA_NOT_AVAILABLE` | N/A | Awaiting paired observations |
| **Paired Comparison**| Mean Paired Error Diff | `DATA_NOT_AVAILABLE` | N/A | Awaiting paired observations |
| **Operational** | Live $P_{50}$ Latency | `DATA_NOT_AVAILABLE` | $< 100\text{ ms}$ | Awaiting live request stream |
| **Operational** | Live $P_{95}$ Latency | `DATA_NOT_AVAILABLE` | $< 150\text{ ms}$ | Awaiting live request stream |
| **Operational** | Candidate Benchmark $P_{95}$ | $77.58\text{ ms}$ | $< 150\text{ ms}$ | **PASS** |
| **Operational** | Timeout Rate | $0.0\%$ | $0.0\%$ | **PASS** |
| **Operational** | Exception Rate | $0.0\%$ | $0.0\%$ | **PASS** |
| **Operational** | Isolation Failures | $0$ | $0$ | **PASS** |
| **Uncertainty** | 80% Empirical Coverage | `DATA_NOT_AVAILABLE` | $\ge 0.80$ | Awaiting verified labels |
| **Uncertainty** | 90% Empirical Coverage | `DATA_NOT_AVAILABLE` | $\ge 0.90$ | Awaiting verified labels |
| **Uncertainty** | 95% Empirical Coverage | `DATA_NOT_AVAILABLE` | $\ge 0.95$ | Awaiting verified labels |
| **Uncertainty** | Mean Interval Width | `DATA_NOT_AVAILABLE` | $\le 1.25$ | Awaiting verified labels |
| **Drift** | Population Stability Index (PSI)| `DATA_NOT_AVAILABLE` | $< 0.10$ | Awaiting live distributions |
| **Drift** | Kolmogorov-Smirnov (KS) Test | `DATA_NOT_AVAILABLE` | $p \ge 0.05$ | Awaiting live distributions |
| **Drift** | Total Variation Distance (TVD) | `DATA_NOT_AVAILABLE` | $< 0.10$ | Awaiting live distributions |

---

## Machine-Readable Artifacts Catalog

The following four authoritative CSV artifacts were created in `ml/experiments/phase14/`:

1. `ml/experiments/phase14/phase14b_shadow_status.csv` — Contains dynamic shadow timeline, model roles, and policy gates.
2. `ml/experiments/phase14/phase14b_verified_labels.csv` — Records 0/100 verified labels, firewall enforcement, and provenance rules.
3. `ml/experiments/phase14/phase14b_production_observations.csv` — Auditable observation record schema with zero fabricated data.
4. `ml/experiments/phase14/phase14b_operational_metrics.csv` — Comprehensive metric catalog reporting `DATA_NOT_AVAILABLE` for unobserved evidence.

---

## Notebook-First Audit Execution

The audit notebook `ml/notebooks/14b_shadow_observation_audit.ipynb` was generated and executed end-to-end:
- 11 audit sections executed.
- All cell assertions passed with exit code 0.
- Confirmed bit-for-bit hash invariance, dynamic timeline tracking, firewall rejection of historical data, and blocked promotion state.

---

## Comprehensive Test Suite & Production Smoke Tests

1. **Full Pytest Suite:**
   - Command: `pytest -q`
   - Result: **135 passed, 0 failed, 10 warnings** in 63.63s.
2. **Phase 14B Dedicated Suite:**
   - Command: `pytest tests/test_phase14b_shadow_observation.py -v`
   - Result: **18 passed, 0 failed** in 11.53s.
3. **Live Production Smoke Tests:**
   - Server: `uvicorn app.main:app --port 8000 --host 127.0.0.1`
   - Script: `python tests/test_smoke_production.py --url http://127.0.0.1:8000`
   - Result: **All 6 checks PASSED (6 / 6 PASSED)**:
     1. `GET /health`: Health status `ok`, model loaded, uncertainty loaded, model hash verified.
     2. `POST /predict`: Estimated score within bounds, conformal interval ordering valid, width matches calibration artifact.
     3. Serving Equivalence: Direct local model prediction matches serving response within $\le 0.01$ delta.
     4. `POST /explain`: SHAP base value and 12 feature contributions correctly computed.
     5. `GET /docs`: OpenAPI Swagger documentation fully reachable.
     6. `GET /governance/shadow/status`: Shadow observation endpoint returns Champion `phase5_tuned_extra_trees`, Candidate `candidate_v1_2_revalidated`, and promotion status `BLOCKED`.

---

## Authoritative Governance Decision

```
======================================================================
DECISION: OPTION C — INSUFFICIENT EVIDENCE
STATUS: REAL-WORLD EVIDENCE ACCUMULATION IN PROGRESS
CHAMPION MODEL: models/phase5_tuned_extra_trees.joblib (ACTIVE PRODUCTION)
CANDIDATE CHALLENGER: models/candidate_v1_2_revalidated.joblib (SHADOW ONLY)
PROMOTION ELIGIBILITY: FALSE (STRICTLY BLOCKED)
AUTOMATIC RETRAINING: DISABLED
AUTOMATIC PROMOTION: DISABLED
HUMAN APPROVAL: PENDING
MODEL MODIFICATIONS: ZERO / NONE
======================================================================
```
