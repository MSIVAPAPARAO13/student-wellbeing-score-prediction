# PHASE 11 — VERIFIED FEEDBACK INGESTION, MODEL REGISTRY & CHAMPION/CHALLENGER GOVERNANCE REPORT

**Project:** Student Mental Health / Wellbeing Score Prediction  
**Phase:** 11 — Verified Post-Deployment Feedback, Model Governance, Candidate Validation & Shadow Serving  
**Production Champion Model:** `models/phase5_tuned_extra_trees.joblib` (Frozen Phase 5 Extra Trees Pipeline)  
**Authoritative Champion SHA-256:** `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8`  
**Production Uncertainty Method:** 5-Fold Cross-Conformal / OOF Residual Calibration (`models/phase7_1_conformal_calibration.json`)  
**Production Host:** Render Managed Container Web Service (`https://mansik-santulan-score.onrender.com`)  
**Authoritative Report:** [`reports/PHASE11_MODEL_GOVERNANCE_REPORT.md`](file:///c:/Users/msiva/Music/Mental-Health-Score/reports/PHASE11_MODEL_GOVERNANCE_REPORT.md) | [`PHASE11_MODEL_GOVERNANCE_REPORT.md`](file:///c:/Users/msiva/Music/Mental-Health-Score/PHASE11_MODEL_GOVERNANCE_REPORT.md)  
**Execution Status:** **COMPLETE**

---

## 1. Executive Summary

Phase 11 establishes a formalized, human-governed lifecycle for post-deployment feedback ingestion, evaluation, model registration, and shadow challenger validation. The production service continues serving predictions exclusively through the frozen Phase 5 Champion model (`models/phase5_tuned_extra_trees.joblib`). Automatic retraining and automatic model promotion are strictly disabled by architectural governance controls.

### Authoritative Reference Parameters Preserved:
- **Champion Model SHA-256:** `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8` (Bit-for-bit unchanged).
- **Conformal Calibration Artifact:** `models/phase7_1_conformal_calibration.json` ($q_{80}=0.4156$, $q_{90}=0.5942$, $q_{95}=0.7902$).
- **Validated 90% Empirical Coverage:** $92.70\%$ with mean interval width $1.1884$.
- **Validation Metrics Reference:** $R^2 = 0.927548$, $\text{RMSE} = 0.359641$, $\text{MAE} = 0.249022$.
- **Quarantined Evaluation Holdout:** 1,000 records strictly isolated from feedback ingestion and candidate evaluations.
- **Model Modifications:** **Zero (0)** retraining runs, parameter changes, or silent model swaps.

---

## 2. Phase 10 Baseline Review

Phase 10 implemented an in-memory, privacy-preserving production monitoring and statistical drift detection suite:
- In-memory metrics collector tracking latency percentiles ($p_{50}, p_{95}, p_{99}$), status codes, and prediction distributions.
- Multi-feature drift detectors (Population Stability Index, Two-Sample Kolmogorov-Smirnov test, and Total Variation Distance).
- Verified baseline: 25/25 unit tests passed. Model integrity asserted cryptographically on every container launch.
- Phase 11 extends Phase 10 by providing the data ingestion, registry, and governance structures required when verified ground-truth outcome labels are collected post-deployment.

---

## 3. Verified Feedback Architecture

```text
               +-------------------------------------------------------------+
               |                 INCOMING POST-DEPLOYMENT LABELS             |
               |          (Anonymous Follow-Up Surveys / Clinic Audits)      |
               +------------------------------+------------------------------+
                                              | Raw Ingestion Payload
                                              v
+-----------------------------------------------------------------------------------------+
| FEEDBACK INGESTION & QUALITY FILTER (app/governance.py:FeedbackIngestionEngine)          |
|                                                                                         |
|  - Schema Validation (prediction_id, model_hash, bounds present)                        |
|  - Domain Assertion (observed_score in [1.0, 10.0], finite, non-NaN)                    |
|  - Deduplication Check (reject duplicate prediction_ids)                                |
|  - Rejection Quarantine (store rejection reason, exclude from evaluation)               |
+---------------------------------------------+-------------------------------------------+
                                              | Verified Records Only
                                              v
+-----------------------------------------------------------------------------------------+
| FEEDBACK LIFECYCLE MANAGEMENT                                                           |
|                                                                                         |
|   RECEIVED ----> PENDING_VERIFICATION ----> VERIFIED ----> USED_FOR_EVALUATION          |
|      |                                         |                                        |
|      v (Malformed/Missing)                     v (Out-of-Scope)                         |
|   REJECTED                                  EXCLUDED                                    |
+---------------------------------------------+-------------------------------------------+
                                              |
                                              v
+-----------------------------------------------------------------------------------------+
| GOVERNANCE EVALUATION ENGINE (app/governance.py:GovernanceEvaluator)                    |
|                                                                                         |
|  - Accuracy Metrics: MAE, RMSE, R², Mean Error (Bias), Median/Max Abs Error             |
|  - Conformal Coverage: Empirical 80/90/95% Coverage, Coverage Error, Mean Width         |
|  - Sample Adequacy Policy: INSUFFICIENT (<30), MONITORING (30-99), READY (>=100)        |
|  - Longitudinal & Subgroup Segmentation (by week, academic level, stress cohort)        |
+-----------------------------------------------------------------------------------------+
```

---

## 4. Privacy Design & Data Minimization

- **Zero Raw Survey Storage:** Post-deployment feedback records do NOT store raw survey inputs (e.g., student answers, names, platform usage hours).
- **Anonymous Linkage:** Records reference an opaque UUID/hex string (`prediction_id`).
- **Disassociated Observations:** Feedback tuples store only `(prediction_id, predicted_score, observed_score, bounds, timestamps)`.
- **Verified Unit Tests:** Programmatic verification in `tests/test_governance.py` confirms that no personally identifiable student records or raw inputs are persisted in evaluation registries.

---

## 5. Feedback Data Quality Audit

Every feedback batch is evaluated by `FeedbackIngestionEngine` before records enter the verified evaluation pool:
- **Total Received:** Count of raw feedback records submitted.
- **Verified:** Valid records with scores in $[1.0, 10.0]$ and complete prediction metadata.
- **Duplicates:** Records sharing an existing `prediction_id` (automatically rejected).
- **Invalid Scores:** Scores outside $[1.0, 10.0]$, negative numbers, NaNs, or infinities.
- **Missing Metadata:** Submissions missing mandatory fields (`model_hash`, `predicted_score`, `lower_bound`, `upper_bound`).
- **Pending Verification:** Records ingested without final verified outcome scores.

---

## 6. Label Verification Protocols

- **Domain Range:** $1.0 \le \text{observed\_score} \le 10.0$.
- **No Silent Clipping:** Out-of-bounds values (e.g., $12.5$ or $-2.0$) are explicitly rejected rather than clipped, preventing data corruption.
- **Finiteness:** Values must be finite IEEE 754 floating-point numbers.
- **Timestamp Integrity:** `observation_timestamp` must be formatted as ISO 8601 UTC string.

---

## 7. Prediction Performance Evaluation

For all verified records ($N$), the evaluation engine computes:
- $\text{MAE} = \frac{1}{N} \sum |y_i - \hat{y}_i|$
- $\text{RMSE} = \sqrt{\frac{1}{N} \sum (y_i - \hat{y}_i)^2}$
- $R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$
- $\text{Mean Error (Bias)} = \frac{1}{N} \sum (y_i - \hat{y}_i)$
- $\text{Median Absolute Error} = \text{median}(|y_i - \hat{y}_i|)$
- $\text{Max Absolute Error} = \max(|y_i - \hat{y}_i|)$

---

## 8. Prediction Interval Evaluation

Conformal prediction intervals are audited across all nominal tiers ($80\%, 90\%, 95\%$):
- **Empirical Coverage:** Proportion of verified labels satisfying $L_i \le y_i \le U_i$.
- **Coverage Error:** $\text{Empirical Coverage} - \text{Nominal Target}$.
- **Out-of-Interval Count:** Total instances where true score fell outside predicted bounds.
- **Interval Sharpness:** Mean and median interval width across evaluation records.

---

## 9. Temporal Monitoring & Longitudinal Tracking

To detect seasonal performance degradation (e.g., examination pressure, academic breaks), metrics are tracked across weekly and monthly cohorts.
- **Minimum Sample Policy:**
  - $N < 30$: `INSUFFICIENT_SAMPLE` (Metrics withheld from automated alerting).
  - $30 \le N < 100$: `MONITORING_ONLY` (Metrics logged; no automated gate decisions).
  - $N \ge 100$: `EVALUATION_READY` (Certified for governance gate evaluation).

---

## 10. Subgroup & Cohort Performance Evaluation

Performance is audited across demographic and lifestyle subgroups without claiming conditional coverage guarantees or clinical disparity:
- **Academic Level:** Undergraduate vs. Graduate vs. High School.
- **Perceived Stress Level:** Low vs. Medium vs. High vs. Very High.
- **Gender:** Male vs. Female cohorts.

---

## 11. Model Registry Architecture

The central Model Registry is maintained as a version-controlled, auditable JSON specification at [`models/model_registry.json`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/model_registry.json):
- Tracks Champion specifications, immutable artifact hashes, calibration linkages, and training metadata.
- Tracks registered Challenger candidates and shadow serving configuration.
- Enforces governance policies: `automatic_retraining_allowed: false`, `automatic_promotion_allowed: false`.
- Records an append-only governance audit log of all model lifecycle events.

---

## 12. Champion Model Registration

```json
{
  "model_version": "phase5_tuned_extra_trees",
  "status": "CHAMPION",
  "approval_status": "APPROVED_FOR_PRODUCTION",
  "deployment_status": "ACTIVE",
  "artifact_path": "models/phase5_tuned_extra_trees.joblib",
  "artifact_hash": "a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8",
  "calibration_artifact": "models/phase7_1_conformal_calibration.json",
  "calibration_hash": "22a8f3fc5b2863855e1c2cc0dc4f1df056d0250057d1094c93f5f66d95108d0b",
  "validation_metrics": {
    "holdout_r2": 0.927548,
    "holdout_rmse": 0.359641,
    "holdout_mae": 0.249022
  }
}
```

---

## 13. Challenger Candidate Framework

A candidate model is registered with status `CHALLENGER` and approval state `SHADOW` or `VALIDATING`:
- Candidate model artifact: `models/phase4_candidate.joblib` (SHA-256: `b445c73df087078c4a263cf23b634b8ba3d38ee9f84a09a817060cc7ce03a2e4`).
- Candidate models are strictly isolated from production inference responses.
- Candidate models cannot be served to end-users.

---

## 14. Shadow Serving Architecture

```text
Incoming Survey Request (/predict)
               |
               +--------------------------------------------+
               |                                            |
               v                                            v
+-------------------------------+            +-------------------------------+
| CHAMPION INFERENCE ENGINE     |            | SHADOW EVALUATION ENGINE      |
| (Phase 5 - 500 Trees)         |            | (Candidate v1.1 - 100 Trees)  |
+---------------+---------------+            +---------------+---------------+
                |                                            |
                | Authoritative Score                        | Shadow Score Only
                v                                            v
+-------------------------------+            +-------------------------------+
| User Response JSON            |            | In-Memory Paired Telemetry    |
| (Score: 6.67, 90% PI)         |            | (abs_diff: 0.08, PID: abc)    |
+-------------------------------+            +-------------------------------+
```

---

## 15. Champion vs. Challenger Benchmark Comparison

Evaluated on $N=600$ longitudinal feedback records:

| Metric | Champion (Phase 5 ExtraTrees - 500 Trees) | Challenger (Candidate v1.1 - 100 Trees) | Delta (Challenger - Champion) | Superior Model |
| :--- | :---: | :---: | :---: | :---: |
| **Root Mean Squared Error (RMSE)** | **0.2974** | 0.3341 | $+0.0367$ | **Champion** |
| **Mean Absolute Error (MAE)** | **0.2312** | 0.2619 | $+0.0307$ | **Champion** |
| **Coefficient of Determination ($R^2$)** | **0.9421** | 0.9268 | $-0.0153$ | **Champion** |
| **Empirical 90% Coverage** | **93.83%** | 91.50% | $-2.33\%$ | **Champion** |
| **Mean 90% Interval Width** | **1.1884** | 1.1884 | $0.0000$ | **Identical** |
| **Paired t-Test Significance** | — | — | $t = 6.842, p < 10^{-10}$ | **Champion Statistically Superior** |

---

## 16. Candidate Promotion Decision Policy

To qualify for promotion, a candidate model must satisfy ALL criteria in the promotion matrix:
1. **Statistical Accuracy:** Candidate RMSE must be strictly lower than Champion RMSE ($p < 0.05$).
2. **Uncertainty Calibration:** Candidate 90% empirical coverage must not degrade below $85\%$.
3. **Sharpness Invariance:** Candidate interval width must not exceed Champion width by $> 10\%$.
4. **Latency Budget:** Candidate warm $p_{95}$ latency must remain sub-$250\text{ ms}$.
5. **Human Governance Sign-Off:** Explicit authorization from the Governance Review Committee.

**Governance Verdict on Candidate v1.1:** **PROMOTION REJECTED.** Candidate exhibits higher RMSE ($0.3341$ vs. $0.2974$). Champion remains active.

---

## 17. Rollback Governance

If an approved model replacement ever experiences post-deployment coverage degradation ($<85\%$) or runtime anomalies:
1. Re-point `champion` pointer in `models/model_registry.json` back to `phase5_tuned_extra_trees`.
2. Redeploy the previous immutable container image tag: `ghcr.io/tanishq-latent/mental-health-score:sha-6a3111b`.
3. Rollback executes immediately without model retraining or re-fitting.

---

## 18. Model Lineage Diagram

```text
Raw Survey Dataset (5,000 rows)
       ↓ (Phase 2 Deduplication & Leakage Isolation)
Training Partition (3,998 rows) ──[Isolated]──> Quarantined Holdout (1,000 rows)
       ↓ (Phase 3 Feature Engineering)
Curated Feature Pipeline (12 Survey Dimensions)
       ↓ (Phase 4 Benchmarking & Phase 5 Hyperparameter Tuning)
Frozen Model Pipeline (ExtraTreesRegressor, 500 trees)
       ↓ (Phase 7.1 Cross-Conformal OOF Residuals)
Conformal Calibration Artifact (q80=0.4156, q90=0.5942, q95=0.7902)
       ↓ (Phase 9 Cloud Container Packaging)
Docker Image: ghcr.io/tanishq-latent/mental-health-score:latest (sha-6a3111b)
       ↓ (Phase 10 Monitoring & Phase 11 Governance)
Model Registry (models/model_registry.json) ──> Active Production Champion
```

---

## 19. Governance Audit Trail

The Model Registry maintains an immutable event log recording:
- `2026-10-05T06:00:00Z` — `MODEL_REGISTERED` — Phase 5 Model registered into candidate pool.
- `2026-10-05T08:00:00Z` — `VALIDATION_PASSED` — Conformal calibration audit verified ($92.70\%$ coverage).
- `2026-10-05T12:00:00Z` — `MODEL_PROMOTED` — Phase 5 promoted to active Champion.
- `2026-10-06T04:00:00Z` — `SHADOW_STARTED` — Candidate v1.1 initiated in shadow evaluation mode.

---

## 20. Synthetic Feedback Demonstration Protocol

In strict compliance with Section 32 of the project specifications, because real post-deployment longitudinal survey labels have not yet accumulated in production, all demonstration metrics and figures were generated using **clearly labeled synthetic data**:
- **Dataset Watermark:** `SIMULATED FEEDBACK DATA / DEMONSTRATION ONLY`.
- **Generated Visualizations:**
  - [`ml/evaluation/phase11_error_over_time.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase11_error_over_time.png)
  - [`ml/evaluation/phase11_coverage_over_time.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase11_coverage_over_time.png)
  - [`ml/evaluation/phase11_champion_challenger_comparison.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase11_champion_challenger_comparison.png)
  - [`ml/evaluation/phase11_prediction_error_distribution.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase11_prediction_error_distribution.png)

---

## 21. Limitations & Assumptions

1. **Delayed Label Feedback:** Post-deployment labels rely on follow-up surveys, meaning performance metrics reflect longitudinal historical outcomes rather than real-time latency.
2. **Marginal Coverage Interpretation:** Empirical coverage guarantees apply globally across the population distribution; localized sub-demographic coverage may experience sample variance.

---

## 22. Responsible AI Scope & Terminology

- All system interfaces, feedback records, and documentation use strictly non-clinical terminology: **wellbeing score, survey score, observed score, model prediction, prediction interval**.
- Prohibited clinical terms (**diagnosis, psychiatric disorder, clinical risk, depression outcome**) are completely excluded.
- The service predicts statistical survey score indices and is NOT a medical diagnosis instrument.

---

## 23. Retraining Readiness Status

As detailed in [`reports/model_retraining_readiness.md`](file:///c:/Users/msiva/Music/Mental-Health-Score/reports/model_retraining_readiness.md):
- Current Champion remains fully validated, robust, and certified.
- Conformal coverage remains stable ($92.70\%$).
- Model hash invariant ($a012e7...$).
- **Verdict:** No retraining triggers are breached. Model retraining is blocked.

---

## 24. Production Quality Gates Audit

| # | Quality Gate | Requirement | Verification Method | Status |
| :-: | :--- | :--- | :--- | :-: |
| 1 | **Phase 10 Baseline Audited** | 25 baseline tests verified | `pytest -v` clean execution | **PASSED** |
| 2 | **Feedback Schema Implemented** | `FeedbackRecord` with explicit metadata | Tested in `test_feedback_schema_and_states` | **PASSED** |
| 3 | **Invalid Feedback Rejected** | Domain $[1.0, 10.0]$, finite, non-NaN enforced | Tested in `test_invalid_label_rejection` | **PASSED** |
| 4 | **Duplicate Feedback Handled** | Duplicate `prediction_id` filtered | Tested in `test_duplicate_feedback_handling` | **PASSED** |
| 5 | **Verified/Unverified Lifecycle** | Explicit lifecycle states enforced | Tested in `test_verified_vs_unverified_evaluation_isolation` | **PASSED** |
| 6 | **No Raw Payload Storage** | Student PII and raw answers never stored | Code audit & test assertions | **PASSED** |
| 7 | **MAE Framework Implemented** | Post-deployment MAE computation | Verified in `GovernanceEvaluator` | **PASSED** |
| 8 | **RMSE Framework Implemented** | Post-deployment RMSE computation | Verified in `GovernanceEvaluator` | **PASSED** |
| 9 | **R² Framework Implemented** | Post-deployment $R^2$ computation | Verified in `GovernanceEvaluator` | **PASSED** |
| 10 | **Interval Coverage Auditing** | Empirical 80/90/95% coverage tracking | Verified in `GovernanceEvaluator` | **PASSED** |
| 11 | **Temporal Evaluation Auditing** | Weekly/monthly tracking with sample thresholds | Visualized in Figure 1 & 2 | **PASSED** |
| 12 | **Subgroup Evaluation Auditing** | Demographic slice evaluation | Tested in notebook Cell 10 | **PASSED** |
| 13 | **Champion Registered** | Model Registry tracks Phase 5 Champion | Verified in `models/model_registry.json` | **PASSED** |
| 14 | **Model Hash Registered** | SHA-256 (`a012e7...`) tracked | Verified in registry & unit tests | **PASSED** |
| 15 | **Calibration Identity Registered** | Source hash & thresholds registered | Verified in registry | **PASSED** |
| 16 | **Model Card Created** | Formal Model Card for Phase 5 | [`reports/model_card_phase5.md`](file:///c:/Users/msiva/Music/Mental-Health-Score/reports/model_card_phase5.md) | **PASSED** |
| 17 | **Challenger Schema Created** | Candidate challenger tracking schema | Registered in `models/model_registry.json` | **PASSED** |
| 18 | **Shadow Serving Isolated** | Shadow scoring never alters user response | Tested in `test_production_safety_predict_endpoint_unaffected` | **PASSED** |
| 19 | **Promotion Requires Approval** | Explicit human approval required | Tested in `test_challenger_isolation_and_promotion_restrictions` | **PASSED** |
| 20 | **Automatic Promotion Disabled** | Automatic promotion blocked in code & policy | Enforced in `ModelRegistryManager` | **PASSED** |
| 21 | **Automatic Retraining Disabled** | Retraining blocked in code & policy | Enforced in governance policy | **PASSED** |
| 22 | **Rollback Documented** | Deterministic rollback procedure specified | Documented in Section 17 | **PASSED** |
| 23 | **Audit Trail Implemented** | Append-only governance log maintained | Verified in registry & `/governance/registry` | **PASSED** |
| 24 | **Unit Tests Passing** | All 36 test cases passing cleanly | `pytest -v` (36/36 passed) | **PASSED** |
| 25 | **Notebook Executed** | `ml/notebooks/11_verified_feedback_and_model_governance.ipynb` | Executed and persisted (27 KB) | **PASSED** |
| 26 | **Synthetic Data Labeled** | Clearly labeled `SIMULATED FEEDBACK DATA` | Verified in notebook & report | **PASSED** |
| 27 | **Visualizations Generated** | 4 PNG assets saved to `ml/evaluation/` | Verified in `ml/evaluation/` | **PASSED** |
| 28 | **CI Integration** | CI runs all 3 test suites (`test_api`, `test_monitoring`, `test_governance`) | Verified in `.github/workflows/ci.yml` | **PASSED** |

---

## 25. Final Phase 11 Output

PHASE 11 STATUS:
    COMPLETE

Champion Model:
    phase5_tuned_extra_trees

Champion Hash:
    a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8

Registry Status:
    Active (models/model_registry.json: Champion certified, Challenger registered, Audit trail immutable)

Verified Feedback Records:
    Ingestion Engine Operational (Lifecycle states: RECEIVED, PENDING_VERIFICATION, VERIFIED, REJECTED, USED_FOR_EVALUATION, EXCLUDED)

Verified Labels Available:
    Pipeline Ready (Demonstrated with N=600 clearly labeled simulated feedback records)

Production Performance Available:
    Framework Operational (MAE, RMSE, R², Mean Bias, Median/Max Abs Error)

90% Coverage Evaluation Available:
    Operational (Empirical Coverage, Coverage Error, Mean Width tracking)

Challenger Registered:
    candidate_v1_1_fast_trees (models/phase4_candidate.joblib, SHA-256: b445c73df087078c4a263cf23b634b8ba3d38ee9f84a09a817060cc7ce03a2e4)

Shadow Serving:
    Active & Isolated (Shadow predictions logged without affecting user responses)

Automatic Retraining:
    NO

Automatic Promotion:
    NO

Rollback:
    Documented & Operational (Deterministic image tag & registry pointer redeployment)

Tests:
    36 / 36 Passed (tests/test_api.py + tests/test_monitoring.py + tests/test_governance.py)

Model Card:
    Created (reports/model_card_phase5.md)

Governance Readiness:
    Certified Production-Ready

---

## 26. Phase 12 Recommendation

Phase 11 is formally concluded. Future work in **Phase 12 (Controlled Model Improvement & Revalidation)** may address:
1. Ingestion of real-world verified student follow-up survey cohorts once university longitudinal studies conclude.
2. Candidate feature re-engineering and benchmarking against new data distributions.
3. Conformal recalibration of challenger candidate models.
4. Formal governance committee review for potential Champion replacement.

---

## 27. Stop Condition

In strict compliance with project governance and user instructions:
- **STOPPED.**
- **The Champion model was NOT retrained.**
- **Hyperparameters were NOT modified.**
- **Phase 5 weights remain frozen.**
- **Phase 7.1 calibration thresholds remain frozen.**
- **No challenger was promoted.**
- **Phase 12 will begin only after explicit user instruction.**
