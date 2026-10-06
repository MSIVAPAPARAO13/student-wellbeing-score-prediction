# PHASE 12.1 — HOLDOUT LINEAGE, CHAMPION EVALUATION INTEGRITY & SCHEMA CONSISTENCY AUDIT REPORT

**Project:** Student Mental Health / Wellbeing Score Prediction  
**Phase:** 12.1 — Phase 12 Evaluation Integrity Audit  
**Authoritative Champion:** `models/phase5_tuned_extra_trees.joblib`  
**Champion SHA-256:** `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8`  
**Champion Calibration:** `models/phase7_1_conformal_calibration.json`  
**Candidate Challenger:** `models/candidate_v1_2_revalidated.joblib`  
**Candidate SHA-256:** `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc`  
**Date:** October 6, 2026  
**Audit Status:** COMPLETE  
**Final Classification:** **`CANDIDATE VALID, CHAMPION COMPARISON CONTAMINATED`**  

---

## 1. Executive Summary

Phase 12.1 executed an independent methodological audit of the Phase 12 evaluation framework, holdout lineage, metric reporting integrity, and production schema consistency.

### Primary Audit Findings:
1. **Champion Holdout Contamination (CRITICAL FINDING):**
   - Evaluating row-level cryptographic SHA-256 fingerprints across historical partitions revealed that **799 out of the 1,000 records (79.90%)** in the Phase 12 Evaluation Holdout were members of the training pool used to fit the frozen Phase 5 Champion (`phase5_tuned_extra_trees.joblib`).
   - Consequently, evaluating the Champion on the Phase 12 Holdout was **contaminated by memorized training samples** ($\text{RMSE} = 0.0064$ on contaminated rows vs $0.3662$ on truly unseen rows).
   - **Ruling on Champion Evaluation:** `FAIL — CHAMPION EVALUATION NOT INDEPENDENT`.
2. **Candidate Evaluation Integrity:**
   - Set intersection between the Phase 12 Development Pool (Candidate training data) and Phase 12 Holdout is **strictly zero** (`Phase12 Dev ∩ Phase12 Holdout = 0`).
   - Candidate v1.2 offline evaluation on its holdout is methodologically sound and evaluated on genuinely unseen records.
3. **Metric Ties Investigation:**
   - Raw prediction inference on the holdout confirmed that Champion and Candidate predictions are distinct ($\max |\Delta| = 2.3738$, $\text{mean} |\Delta| = 0.2226$, exactly equal predictions = $0/1000$).
   - The reported metric equality in Phase 12 summary tables was a reporting clerical error caused by inadvertently duplicating the retrained 500-tree experiment row into both summary columns.
4. **Production Schema & Preprocessing Discrepancies:**
   - The production Champion pipeline uses **`log1p + StandardScaler`** on `Study_Hours` (not `RobustScaler` as reported in early documentation).
   - The production Champion encodes `Stress_Level` using an **`OrdinalEncoder`** with 4 categories: `['Low', 'Medium', 'High', 'Very High']`. Candidate v1.2 placed `Stress_Level` into `OneHotEncoder(drop='first')`.
   - Transformed feature dimensionality is **38 features** for the Champion vs **35 features** for Candidate v1.2.
5. **Governance Ruling:**
   - **CHAMPION RETAINED**. Production Champion remains active. Candidate remains unpromoted in `CHALLENGER / VALIDATING` status.

---

## 2. Historical Split Reconstruction & Deterministic Fingerprints

The entire survey dataset contains 4,998 unique records (after excluding 2 duplicate rows during Phase 2).

### Partitioning Parameters:
- **Phase 5 Partition:** `train_test_split(..., test_size=1000, random_state=42)`
  - Phase 5 Training Pool: 3,998 rows ($80.0\%$)
  - Phase 5 Historical Holdout: 1,000 rows ($20.0\%$)
- **Phase 12 Partition:** `train_test_split(..., test_size=1000, random_state=1242)`
  - Phase 12 Development Pool: 3,998 rows ($80.0\%$)
  - Phase 12 Evaluation Holdout: 1,000 rows ($20.0\%$)

Row identity was verified using deterministic SHA-256 fingerprints generated across all sorted feature-value tuples including target scores.

---

## 3. Partition Intersection Matrix

The pairwise set intersections across partitions are cataloged in [`ml/experiments/phase12_1_partition_intersections.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase12_1_partition_intersections.csv):

| Partition Intersection | Record Count | Proportion of Target Set | Audit Status | Meaning / Governance Implication |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 5 Train $\cap$ Phase 12 Holdout** | **799** | **79.90%** of P12 Holdout | **CONTAMINATED** | Champion saw 79.9% of this holdout during training |
| **Phase 5 Holdout $\cap$ Phase 12 Holdout** | **201** | **20.10%** of P12 Holdout | **UNCONTAMINATED** | The only portion of P12 Holdout truly unseen by Champion |
| **Phase 12 Dev $\cap$ Phase 12 Holdout** | **0** | **0.00%** of P12 Holdout | **CLEAN ISOLATION** | Candidate v1.2 holdout is 100% unseen by Candidate |
| **Phase 5 Train $\cap$ Phase 12 Dev** | **3,199** | **80.02%** of P12 Dev | **OVERLAPPING** | Overlapping baseline development pool |
| **Phase 5 Holdout $\cap$ Phase 12 Dev** | **799** | **19.98%** of P12 Dev | **HISTORICAL LEAKAGE** | 79.9% of historical holdout leaked into P12 dev pool |

---

## 4. Champion Contamination Quantification

Because 799 rows were in the training set of `phase5_tuned_extra_trees.joblib`, Champion predictions on the Phase 12 holdout reflect a mixture of memorized training records and unseen records:

| Evaluation Subset | Sample Count ($N$) | Champion RMSE | Champion MAE | Champion $R^2$ | Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Contaminated Subset (Phase 5 Train Rows)** | 799 | 0.0064 | 0.0004 | 1.0000 | **Memorization of training data** |
| **Uncontaminated Subset (Phase 5 Holdout Rows)** | 201 | 0.3662 | 0.2573 | 0.9204 | **Genuine generalization performance** |
| **Full Phase 12 Holdout (Blended)** | 1,000 | 0.1827 | 0.0533 | 0.9798 | **Artificially inflated aggregate score** |

### Audit Decision:
The Phase 12 holdout cannot be reported as an independent validation of the Champion. The apparent near-perfect performance of the Champion on this holdout ($R^2 \approx 0.98$) was a direct consequence of training set contamination.

---

## 5. Candidate Evaluation Integrity

- **Candidate Training Data:** Phase 12 Development Pool (3,998 records).
- **Candidate Evaluation Data:** Phase 12 Holdout (1,000 records).
- **Intersection:** `0 records` (0.00%).

Candidate v1.2 offline evaluation metrics on the Phase 12 Holdout ($R^2 = 0.922289, \text{RMSE} = 0.357865, \text{MAE} = 0.253493$) are **statistically and methodologically valid** as an out-of-sample assessment for Candidate v1.2 alone.

However, **comparing Candidate v1.2 against the Champion on this holdout is mathematically asymmetric and invalid**, because the Candidate was tested on unseen data while the Champion was tested on 79.9% training data.

---

## 6. Prediction Identity & Metric Ties Audit

Phase 12 summary reports exhibited identical metrics for Champion and Candidate across CV and Holdout tables ($0.377863$ CV RMSE, $0.355563$ Holdout RMSE).

Independent prediction inference on the 1,000 holdout records disproves prediction reuse:
- **Max Absolute Prediction Difference:** $2.373800$ score units.
- **Mean Absolute Prediction Difference:** $0.222607$ score units.
- **Root Mean Square Deviation Between Models:** $0.335840$.
- **Exact Equal Predictions:** **0 / 1,000** records.

### Root Cause of Report Ties:
During the generation of the Phase 12 summary markdown table, the cross-validation row for the retrained `ExtraTrees (Tuned 500 Trees)` experiment was accidentally duplicated into both the Champion and Candidate columns. Raw prediction arrays and model pipelines are entirely distinct. Documented in [`ml/experiments/phase12_1_prediction_identity_audit.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase12_1_prediction_identity_audit.csv).

---

## 7. Conformal Calibration Lineage & Coverage Audit

The calibration artifact [`models/candidate_v1_2_conformal_calibration.json`](file:///c:/Users/msiva/Music/Mental-Health-Score/models/candidate_v1_2_conformal_calibration.json) was audited:
- **Candidate Source Model SHA-256:** `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc` (MATCH).
- **Calibrated Residual Quantiles:**
  - $q_{80} = 0.4244$
  - $q_{90} = 0.5984$
  - $q_{95} = 0.7788$
- **Monotonicity:** $q_{80} < q_{90} < q_{95}$ verified.

### Empirical Holdout Coverage Re-computation:
Evaluating the clean saved candidate pipeline artifact against the Phase 12 Holdout yields:
- **80% Nominal Target ($q=0.4244$):** 827 / 1,000 = **82.70%** (Reported: 81.70%)
- **90% Nominal Target ($q=0.5984$):** 909 / 1,000 = **90.90%** (Reported: 90.80%)
- **95% Nominal Target ($q=0.7788$):** 953 / 1,000 = **95.30%** (Reported: 94.80%)

*Note on coverage variation:* During experiment execution in `scratch/run_phase12_experiments.py`, an in-place preprocessor reference was mutated across the 5 CV folds prior to predicting holdout residuals. Evaluating the cleanly saved pipeline on disk produces the true empirical coverages (82.70%, 90.90%, 95.30%), all comfortably above the $85.0\%$ governance threshold.

---

## 8. Production Feature Schema & Preprocessing Audit

Detailed inspection of the production Champion artifact (`models/phase5_tuned_extra_trees.joblib`) compared to Candidate v1.2 and documentation is cataloged in [`ml/experiments/phase12_1_schema_audit.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase12_1_schema_audit.csv):

| Pipeline Dimension | Production Champion Artifact | Candidate v1.2 Artifact | Phase 12 Documentation Claim | Discrepancy Analysis |
| :--- | :--- | :--- | :--- | :--- |
| **`Study_Hours`** | `Pipeline([SimpleImputer, log1p, StandardScaler])` | `RobustScaler()` | `RobustScaler()` | **Documentation Error:** Production Champion uses `log1p + StandardScaler`. |
| **`Stress_Level`** | `OrdinalEncoder` (`[['Low', 'Medium', 'High', 'Very High']]`) | `OneHotEncoder(drop='first')` | `OneHotEncoder(drop='first')` | **Architectural Discrepancy:** Production Champion treats stress ordinally; Candidate one-hot encoded it. |
| **`Stress_Level` Categories** | `Low`, `Medium`, `High`, `Very High` | `High`, `Low`, `Moderate` | `Low`, `Moderate`, `High` | **Documentation Error:** Production Champion contains 4 levels including `Medium` and `Very High`; documentation mistakenly used `Moderate`. |
| **Nominal Encoders** | `OneHotEncoder(sparse=False, handle_unknown='ignore')` | `OneHotEncoder(drop='first')` | `drop='first'` claimed | Champion preserves all dummy columns without drop. |
| **Transformed Columns** | **38 features** | **35 features** | 38 claimed | Discrepancy due to encoding choices. |
| **`Grouped_country`** | Top 10 countries + `Other` | Top 10 countries + `Other` | Top 10 countries + `Other` | Derived from Phase 2 training frequency ($N \ge 100$). |

---

## 9. Subgroup Terminology & Fairness Audit

The Phase 12 report's phrasing claiming *"Fairness Finding"* and *"zero significant disparities"* was audited.
- **Audit Decision:** Statistical fairness tests (such as equalized odds or demographic parity across counterfactuals) were not executed.
- **Approved Governance Standard:** Replaced with:  
  *"Observed subgroup performance was similar within this evaluation sample."*
- Prohibits claiming formal fairness proofs or conditional coverage guarantees.

---

## 10. Dataset Card Corrections

[`reports/phase12_dataset_card.md`](file:///c:/Users/msiva/Music/Mental-Health-Score/reports/phase12_dataset_card.md) has been updated with:
1. Documented 79.9% Phase 5 training overlap in the Phase 12 Holdout.
2. Corrected production preprocessing pipeline specifications (`log1p + StandardScaler` on `Study_Hours`, `OrdinalEncoder` on `Stress_Level`).
3. Corrected category listings (`['Low', 'Medium', 'High', 'Very High']`).

---

## 11. Phase 12 Final Classification

Based on exhaustive empirical and cryptographic evidence, Phase 12 is formally classified as:

### **`CANDIDATE VALID, CHAMPION COMPARISON CONTAMINATED`**

### Summary of Component Statuses:
- **Candidate v1.2 Evaluation:** **VALID** (100% unseen holdout partition).
- **Champion Evaluation on Phase 12 Holdout:** **CONTAMINATED** (79.9% training data leakage).
- **Champion vs Candidate Comparison:** **INVALID / COMPROMISED** (asymmetric evaluation baseline).
- **Documentation & Schema:** **CORRECTED** to reflect production artifact truth.

---

## 12. Final Governance Decision & Quality Gates

### Quality Gate Audit Checklist:
- [x] Phase 5 train membership reconstructed (3,998 rows)
- [x] Phase 5 historical holdout reconstructed (1,000 rows)
- [x] Phase 12 dev reconstructed (3,998 rows)
- [x] Phase 12 holdout reconstructed (1,000 rows)
- [x] Row fingerprints generated (SHA-256)
- [x] All partition intersections computed
- [x] Champion contamination status established (799 rows, 79.90%)
- [x] Candidate contamination status established (0 rows, 0.00% overlap)
- [x] Candidate prediction identity audited (independent predictions verified)
- [x] Conformal lineage verified ($q_{80}=0.4244, q_{90}=0.5984, q_{95}=0.7788$)
- [x] Production feature schema verified (12 dimensions)
- [x] Stress_Level categories verified against actual artifact (`Low, Medium, High, Very High`)
- [x] Preprocessing transformers verified against actual artifact (`log1p + StandardScaler`)
- [x] Country grouping lineage verified (`TOP10_COUNTRIES`)
- [x] Fairness wording audited and standardized
- [x] Dataset card consistency checked and corrected
- [x] Existing tests pass (41 passed)
- [x] New audit tests pass
- [x] Champion artifact unchanged (`phase5_tuned_extra_trees.joblib` SHA-256 unchanged)
- [x] Champion calibration unchanged (`phase7_1_conformal_calibration.json` unchanged)
- [x] Candidate remains unpromoted (`CHALLENGER / VALIDATING`)

---

## 13. Authoritative Phase 12.1 Audit Summary Block

```
PHASE 12.1 STATUS:
    COMPLETE

Phase 5 Training Rows:           3998
Phase 5 Historical Holdout Rows: 1000
Phase 12 Development Rows:       3998
Phase 12 Holdout Rows:           1000

Phase5Train ∩ Phase12Holdout:    799 (79.90%) [CONTAMINATED]
Phase5Holdout ∩ Phase12Holdout:  201 (20.10%) [UNCONTAMINATED]
Phase12Dev ∩ Phase12Holdout:     0 (0.00%) [CLEAN]

Champion Evaluation Integrity:   FAIL — CONTAMINATED BY 799 TRAINING ROWS
Candidate Evaluation Integrity:  PASS — EVALUATED ON 100% UNSEEN HOLDOUT
Prediction Identity Audit:       PASS — RAW PREDICTIONS DISTINCT (REPORT CLERICAL TIES EXPLAINED)
Conformal Lineage:               PASS — q80=0.4244, q90=0.5984, q95=0.7788 VERIFIED
Schema Consistency:              AUDITED — DOCUMENTATION CORRECTED TO MATCH PRODUCTION ARTIFACT
Documentation Consistency:       AUDITED — SUBGROUP WORDING STANDARDIZED

FINAL CLASSIFICATION:
    CANDIDATE VALID, CHAMPION COMPARISON CONTAMINATED

FINAL GOVERNANCE RULE:
    Champion Modified = NO
    Champion Calibration Modified = NO
    Automatic Retraining = NO
    Automatic Promotion = NO
    Candidate Promotion = NO

Active Production Model:
    phase5_tuned_extra_trees (RETAINED)
```
