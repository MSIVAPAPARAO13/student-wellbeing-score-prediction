# MODEL RETRAINING READINESS & GOVERNANCE HANDOFF SPECIFICATION

**Project:** Student Mental Health / Wellbeing Score Prediction  
**Phase:** 11 — Model Governance & Feedback Lifecycle  
**Target Document:** [`reports/model_retraining_readiness.md`](file:///c:/Users/msiva/Music/Mental-Health-Score/reports/model_retraining_readiness.md)  
**Current Production Champion:** `phase5_tuned_extra_trees` (SHA-256: `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8`)  
**Status:** **RETRAINING BLOCKED (Current Champion Certified & Stable)**

---

## 1. Governance Policy on Production Retraining

### Non-Negotiable Core Rule:
**Automatic retraining is strictly prohibited.** Under no circumstances may an automated CI/CD pipeline, monitoring alert, or telemetry threshold silently retrain, alter, or replace the production model artifact.

Any retraining must be treated as a **formal, human-governed Machine Learning engineering project (Phase 12+)**, adhering to all data leakage audits, holdout quarantines, uncertainty calibrations, and safety reviews.

---

## 2. Retraining Triggers (Evidence Required to Open a New ML Phase)

A new model development and retraining lifecycle may be initiated ONLY if one or more of the following quantitative evidence gates are documented:

| Trigger Category | Operational Condition | Measurement Method | Severity Action |
| :--- | :--- | :--- | :--- |
| **Sustained Coverage Failure** | Verified 90% conformal coverage falls below $85\%$ across $\ge 200$ consecutive verified labels | Post-deployment feedback evaluation | **CRITICAL:** High priority review |
| **Sustained Accuracy Drop** | Verified post-deployment $R^2$ drops below $0.85$ or $\text{RMSE} > 0.45$ across $\ge 200$ labels | Verified label evaluation pipeline | **HIGH:** Model performance drift |
| **Severe Input Drift** | Key features (`Sleep_Hours_Per_Night`, `Stress_Level`, `Daily_Unlocks`) exhibit sustained $\text{PSI} \ge 0.25$ over $\ge 30$ days | In-memory drift detection & monitoring audits | **MEDIUM:** Data distribution shift |
| **Survey Schema Evolution** | University adds new survey questions or deprecates existing platforms/options | Ingress schema audit & validation failure spike ($> 15\%$) | **MEDIUM:** Contract change |
| **New Ground-Truth Corpus** | Accumulation of $\ge 1,000$ verified, anonymized longitudinal survey labels | Feedback ingestion registry | **OPPORTUNITY:** Planned model upgrade |
| **Superior Candidate Architecture** | Challenger model demonstrates statistically superior RMSE, valid coverage, and equivalent latency in shadow serving | Paired shadow evaluation report | **OPPORTUNITY:** Scheduled candidate promotion |

---

## 3. Mandatory Pre-Retraining Audit Checklist

Before any retraining script or notebook may execute in Phase 12, the engineering team must satisfy:

- [ ] **Problem Formulation Check:** Target definition remains continuous statistical survey wellbeing score ($1.0$ to $10.0$). Non-clinical scope re-verified.
- [ ] **Data Hygiene & Deduplication:** Raw corpus deduplicated and screened for synthetic artifacts.
- [ ] **Holdout Redesign:** A completely untouched, quarantined evaluation holdout of at least $1,000$ records is reserved and isolated.
- [ ] **Leakage Isolation:** Transformers, encoders, and scalers fitted strictly inside CV folds.
- [ ] **Uncertainty Calibration:** Cross-conformal OOF residual calibration methodology applied to new candidate weights.
- [ ] **Explainability Consistency:** TreeSHAP aggregation verified for human interpretability.
- [ ] **Shadow Validation Requirement:** New candidate must complete at least 14 days of shadow evaluation before promotion consideration.

---

## 4. Retraining Handoff Workflow Diagram

```text
+-----------------------+     Threshold Breach     +-------------------------------+
| Production Telemetry  +------------------------->| Governance Alert Log          |
| (Monitoring & Drift)  |                          | (Flagged: REVIEW_REQUIRED)    |
+-----------------------+                          +---------------+---------------+
                                                                   |
                                                                   v
+-----------------------+     Audit Passed         +---------------+---------------+
| Candidate Retraining  |<-------------------------| Governance Review Committee   |
| (Phase 12 Notebooks)  |                          | (Human Approval Required)     |
+-----------+-----------+                          +-------------------------------+
            |
            v
+-----------------------+     All Gates Passed     +-------------------------------+
| Shadow Serving        +------------------------->| Human Promotion Approval      |
| (14-Day Dual Run)     |                          | -> Promoted to New Champion   |
+-----------------------+                          +-------------------------------+
```

---

## 5. Current Recommendation

The Phase 5 Champion continues to exhibit exceptional accuracy ($R^2 = 0.9275$, $\text{RMSE} = 0.3596$) and robust coverage ($92.70\%$ with width $1.1884$). Zero retraining triggers have been breached.

**Conclusion:** The production model is fully certified and stable. No retraining is recommended at this time.
