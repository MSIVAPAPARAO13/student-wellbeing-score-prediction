# Phase 13A — Model-Driven UI Integrity Hardening & Authoritative Metadata Report

**Project:** Student Mental Health / Wellbeing Score Prediction  
**Authoritative Source:** `https://github.com/MSIVAPAPARAO13/student-wellbeing-score-prediction` (`main` branch)  
**Base Commit:** `a18f844e4d350b87b7ffcb45477be9665bcbfae0`  
**Phase Status:** **Phase 13 remains ACTIVE / IN PROGRESS** | **Phase 14 NOT STARTED**

---

## 1. Executive Summary

This report documents the completion of **Phase 13A: Model-Driven UI Integrity Hardening and Authoritative Backend Metadata Synchronization**.

The primary objective was to eliminate all hardcoded model values, demo fixtures, client-side score binning, and metadata duplication across the frontend and backend architectures:
1. **Frontend Hardening:** Removed the "Load Benchmark Sample" feature, all hardcoded student profiles, client-side score categories (`Lower Score`, `Moderate Score`, `Higher Score`, `Balanced Baseline`, `Resilient Habits`, `Elevated Daily Strain`), and static interval numbers (`6.07`, `6.67`, `7.26`, `1.1884`).
2. **Authoritative Backend Runtime Metadata:** Refactored `ModelService` in `app/model_service.py` to become the single authoritative source of runtime metadata (`model_version`, `model_family`, `model_hash`, `model_hash_verified`, `uncertainty_method`, `calibration_hash`), eliminating duplicated literals across `/health`, `/predict`, and `/explain`.
3. **Safe Explanation Initialization:** Eliminated the fallback `base_value = 6.23` in `app/explanation_service.py`, requiring `base_value` to derive strictly from runtime `TreeExplainer.expected_value`.
4. **Smoke Test Improvement:** Replaced hardcoded magic numbers in `tests/test_smoke_production.py` with dynamic width derivation mathematically computed from the authoritative conformal calibration artifact (`2 * q90`).
5. **Phase 13A Integrity Tests:** Expanded `tests/test_phase13a_ui_integrity.py` to 11 comprehensive automated tests asserting UI integrity, country grouping logic, metadata consistency, and dynamic multi-profile sensitivity.
6. **Walkthrough Documentation:** Authored a complete, human-readable walkthrough file (`WALKTHROUGH.md`) covering all 17 interview and architecture dimensions.

---

## 2. Files Inspected & Files Modified

### Files Inspected
- `README.md`
- `index.html`
- `style.css`
- `script.js`
- `main.py`
- `app/main.py`
- `app/configuration.py`
- `app/schemas.py`
- `app/model_service.py`
- `app/explanation_service.py`
- `app/governance.py`
- `app/monitoring.py`
- `models/phase5_metadata.json`
- `models/model_registry.json`
- `models/candidate_v1_2_metadata.json`
- `models/phase7_1_conformal_calibration.json`
- `models/candidate_v1_2_conformal_calibration.json`
- `tests/test_api.py`
- `tests/test_smoke_production.py`
- `tests/test_phase13_real_world_validation.py`
- `reports/PHASE13_REAL_WORLD_PRODUCTION_VALIDATION.md`
- `reports/PHASE12_3_CANDIDATE_VALIDATION_GATE.md`

### Files Modified
- `app/configuration.py`: Added `REGISTRY_PATH` to configuration settings.
- `app/model_service.py`: Added authoritative properties (`model_version`, `model_family`, `model_hash`, `model_hash_verified`, `uncertainty_method`, `calibration_hash`, `calibration_artifact`), verified calibration source hash against loaded model hash, removed hardcoded return literals in `predict()`, and explicitly documented country grouping behavior.
- `app/explanation_service.py`: Removed fallback `self.base_value: float = 6.23`, set initial state to `None`, dynamically initialized `base_value` from `TreeExplainer.expected_value`, and used `model_service.model_version` in `ExplanationResponse`.
- `app/main.py`: Refactored `/health` to expose actual runtime properties from `model_service`.
- `index.html`: Removed "Load Benchmark Sample" button and static sample placeholders; reset default visual track displays to `—`.
- `script.js`: Removed `demoSampleBtn` listener and sample dictionaries; mapped all card fields, intervals, metadata, and SHAP attributions directly from `/predict`, `/explain`, and `/health` responses; cleared views on error without fallback predictions.
- `style.css`: Cleaned up styling for interval tracks, explanation factors, and error states.
- `tests/test_smoke_production.py`: Removed hardcoded `1.1884` validation constant; derives expected interval width dynamically from `models/phase7_1_conformal_calibration.json` ($2 \times q_{90}$).
- `tests/test_phase13a_ui_integrity.py`: Created and expanded to 11 unit tests covering frontend integrity, dynamic metadata, country grouping, and two-profile divergence.
- `README.md`: Updated test counts to reflect the current 104 passing tests and accurate schema documentation.
- `WALKTHROUGH.md`: Created comprehensive human-readable project walkthrough.

---

## 3. Backend Metadata Changes

Previously, metadata strings were duplicated independently:
- `/health` hardcoded `"phase5_tuned_extra_trees"` and `"5-fold OOF conformal"`
- `/predict` used `self.conformal_data.get("method", "5-fold OOF conformal")` and hardcoded `"phase5_tuned_extra_trees"`
- `/explain` hardcoded `"phase5_tuned_extra_trees"`
- `ExplanationService` initialized with fallback `self.base_value = 6.23`

### Unified Architecture
`ModelService` now acts as the single authoritative source of truth:
- `model_version`: Derived authoritatively from `models/model_registry.json` (champion entry) or model metadata.
- `model_family`: Derived from conformal artifact or model registry champion.
- `model_hash`: Computed via SHA-256 upon model file read and cryptographically verified against `settings.MODEL_EXPECTED_HASH`.
- `model_hash_verified`: Boolean flag verifying exact match.
- `uncertainty_method`: Extracted directly from `conformal_data["method"]` (`"5-Fold Cross-Conformal / Out-Of-Fold Residual Calibration"`).
- `calibration_hash`: Computed via SHA-256 on `models/phase7_1_conformal_calibration.json`.
- `calibration_artifact`: Active conformal file name.

---

## 4. Frontend Model-Driven Changes

1. **Removal of Benchmark Button:** `<button id="demo-sample-btn">` was removed from `index.html`. Users must enter actual survey attributes.
2. **Removal of Hardcoded Numbers:** Placeholder texts for scores, lower bounds, upper bounds, and widths were converted to neutral `—` markers until an actual API response arrives.
3. **Removal of Client-Side Categorization:** Deleted all `if score < 4 ...` branching and removed the `#score-status-badge` element (`Moderate Score`, `Resilient Habits`, etc.).
4. **Dynamic Health Status:** `checkApiHealth()` queries `GET /health` and updates the connection badge using `data.model_version`.
5. **Dynamic Predictions & Intervals:** Visual track markers (`leftPercent`, `rightPercent`, `estimatePercent`) and bounds are computed from `data.prediction_interval.lower`, `upper`, and `width`.
6. **Dynamic TreeSHAP Explanations:** Feature contributions, values, SHAP impact values, and expected base value $E[Y]$ are populated dynamically from `POST /explain`.
7. **Zero Fallback on Error:** If `/predict` or `/explain` returns an error, `clearResultDisplay()` resets previous cards, preventing stale or fabricated numbers from being presented.

---

## 5. Country Handling Behavior

The production preprocessing pipeline expects `Grouped_country` to match one of the top 10 categories identified during EDA:
- Australia, Canada, France, Germany, India, Mexico, Other, Turkey, UK, USA.

### Implemented Rule
- If the trimmed input matches one of the top 10 categories exactly (e.g. `"USA"`), it is retained.
- If the input is non-standard (e.g. `"United States"` or `"Brazil"`), it is mapped to `"Other"`.
- A dedicated regression test (`test_country_grouping_explicit_behavior`) verifies this exact mapping.

---

## 6. Live API & Two-Profile Verification

Live verification was executed against the local service (`http://127.0.0.1:8000`):

### 1. `GET /health`
```json
{
  "status": "ok",
  "model_loaded": true,
  "uncertainty_loaded": true,
  "model_version": "phase5_tuned_extra_trees",
  "uncertainty_method": "5-Fold Cross-Conformal / Out-Of-Fold Residual Calibration",
  "model_hash_verified": true
}
```

### 2. Multi-Profile Divergence (Observed Verification Evidence)
*(Note: The following values were observed during the Phase 13A local verification run and serve as empirical evidence of dynamic model-driven divergence, NOT as guaranteed future outputs).*
- **Profile A (Low Usage / Low Stress / Regular Habits):**
  - Inputs: Age 20, Usage 2.0h, Unlocks 45, Sleep 8.5h, Study 6.0h, Physical Activity 3.0h, Stress Low.
  - Estimated Wellbeing Score: **8.03 / 10**
  - 90% Prediction Interval: **[7.43, 8.62]** (Width: 1.1884)
  - Top Positive Contributors: `Avg_Daily_Usage_Hours` (+0.4375), `Stress_Level` (+0.4271)
- **Profile B (High Usage / Very High Stress / Poor Sleep):**
  - Inputs: Age 23, Usage 10.0h, Unlocks 250, Sleep 4.0h, Study 1.0h, Physical Activity 0.0h, Stress Very High.
  - Estimated Wellbeing Score: **5.04 / 10**
  - 90% Prediction Interval: **[4.45, 5.63]** (Width: 1.1884)
  - Top Negative Contributors: `Stress_Level` (-0.2993), `Avg_Daily_Usage_Hours` (-0.2528)

**Verification Outcome:** Point predictions ($8.03 \neq 5.04$) and local SHAP factor directions dynamically diverge based exclusively on model inference.

---

## 7. Artifact Integrity Verification

Model artifact SHA-256 hashes were computed before and after all changes:

| Artifact | Expected Signature | Computed Signature | Match Status |
| :--- | :--- | :--- | :---: |
| **Champion Model** | `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8` | `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8` | **EXACT MATCH** |
| **Candidate Model** | `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc` | `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc` | **EXACT MATCH** |

No model weights, pipelines, calibration thresholds, or registry lifecycle policies were altered.

---

## 8. Final Pytest Results

```text
pytest -q
........................................................................ [ 69%]
................................                                         [100%]
104 passed, 10 warnings in 53.20s
```

- **Passed:** 104
- **Failed:** 0
- **Skipped:** 0
- **Warnings:** 10 (FastAPI/Starlette deprecation warnings)
- **Execution Time:** 53.20s

---

## 9. Governance & Phase Status

- **Implementation Status:** **COMPLETE**
- **Phase 13:** **ACTIVE / IN PROGRESS**
  - Champion: **ACTIVE PRODUCTION**
  - Candidate: **SHADOW / VALIDATING**
  - Shadow window completed: **0 / 14 days at current documented observation state**
  - Verified production labels: **0 / 100**
  - Promotion status: **BLOCKED**
  - Human approval: **PENDING**
  - Automatic retraining: **DISABLED**
  - Automatic promotion: **DISABLED**
- **Phase 14:** **NOT STARTED**
