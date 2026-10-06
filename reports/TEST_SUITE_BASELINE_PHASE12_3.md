# TEST SUITE BASELINE FOR PHASE 12.3

**Project:** Student Mental Health / Student Wellbeing Score Prediction  
**Date:** October 6, 2026  
**Phase:** 12.3 — Candidate Validation Gate & Shadow-Readiness  
**Authoritative Remote:** `https://github.com/MSIVAPAPARAO13/student-wellbeing-score-prediction.git`  
**Target Branch:** `main`

---

## 1. Test Execution Baseline

| Parameter | Value | Status |
| :--- | :--- | :---: |
| **Pytest Command** | `pytest -q` (and `pytest --collect-only -q`) | **VERIFIED** |
| **Collection Count** | **64 tests** | **VERIFIED** |
| **Executed Count** | **64 tests** | **VERIFIED** |
| **Passed** | **64 passed** | **VERIFIED** |
| **Failed** | **0 failed** | **VERIFIED** |
| **Skipped** | **0 skipped** | **VERIFIED** |
| **Execution Duration** | **22.21 seconds** | **STABLE** |

---

## 2. Test Module Breakdown

| Test File | Test Count | Module Scope |
| :--- | :---: | :--- |
| `tests/test_api.py` | 14 | FastAPI routing, input validation (422), interval calculation, TreeSHAP explanation endpoint |
| `tests/test_audit_12_1.py` | 11 | Phase 12.1 cryptographic fingerprint determinism, partition lineage, holdout contamination rates, schema consistency |
| `tests/test_governance.py` | 11 | Central model registry integrity, feedback validation, shadow challenger isolation, anti-auto-retraining policies |
| `tests/test_monitoring.py` | 11 | Statistical drift detection (PSI, KS-test, TVD), Prometheus metrics exposition, interval width monitoring |
| `tests/test_phase12_2_clean_evaluation.py` | 14 | Symmetrical evaluation assertions on the 201 clean common holdout records, model & calibration artifact immutability |
| `tests/test_revalidation.py` | 6 | Candidate v1.2 model artifact integrity, conformal monotonicity, registry promotion blocks |
| `tests/test_smoke_production.py` | 1 | Production health check and model loading smoke test |
| **Total Discovered & Executed** | **64** | **100% Passed (0 Failures, 0 Skipped)** |

---

## 3. Explanation of Historical Discrepancy (50 vs 64 Tests)

A discrepancy previously existed between historical documentation:
- **Phase 12.2 report:** Cited **64 passed, 0 failed**.
- **Repository migration report:** Cited **50 passed, 0 failed**.

### Root Cause Analysis & Reconciliation:
1. **Repository Migration Scope Boundary:** During the initial migration of the codebase to the authoritative repository (`MSIVAPAPARAO13/student-wellbeing-score-prediction`), the task mandate strictly specified freezing the migration scope through completed Phase 12.1 work prior to verifying the new remote (`Phase 12.2 will be performed AFTER the new repository has been verified`).
2. **Phase 12.2 Test Module Isolation:** Consequently, during the migration commit, the Phase 12.2 test module (`tests/test_phase12_2_clean_evaluation.py`, containing exactly **14 tests**) was set aside so that the repository strictly reflected Phase 12.1, resulting in:
   $$\text{Discovered Tests during Migration} = 64 - 14 = \mathbf{50\text{ tests}}$$
3. **Restoration of Phase 12.2 Completion Artifacts:** With Phase 12.1 and Phase 12.2 confirmed complete, all Phase 12.2 artifacts (reports, notebooks, experiment data, and `tests/test_phase12_2_clean_evaluation.py`) are restored into the repository.
4. **Current Authoritative Baseline:** Test collection discovers all 6 modules and 64 tests:
   $$\mathbf{50\text{ base tests}} + \mathbf{14\text{ Phase 12.2 tests}} = \mathbf{64\text{ tests total (all passing)}}.$$

This establishes **64 passed tests** as the authoritative pre-Phase 12.3 test baseline.
