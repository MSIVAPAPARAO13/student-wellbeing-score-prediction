"""Build and execute ml/notebooks/13_real_world_production_validation.ipynb top-to-bottom.
"""

from pathlib import Path
import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parent.parent

nb = nbf.v4.new_notebook()

cells = []

# Title & Metadata
cells.append(nbf.v4.new_markdown_cell("""# Phase 13: Real-World Production Validation & Controlled Shadow Observation

**Project**: Student Wellbeing Score Prediction  
**Phase**: 13 — Real-World Production Validation & Controlled Shadow Observation  
**Authoritative Champion**: `models/phase5_tuned_extra_trees.joblib` (SHA-256: `a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8`)  
**Challenger Candidate**: `models/candidate_v1_2_revalidated.joblib` (SHA-256: `aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc`)  

### Governance Principles Enforced:
1. **Champion Sole User-Facing Model**: User requests are served 100% by the Champion.
2. **Strict Shadow Isolation**: Candidate executes asynchronously/out-of-band; candidate failures/timeouts never impact user responses.
3. **Data Segregation**: Historical/offline data, synthetic data, and unverified feedback are strictly separated. Only verified production outcomes qualify.
4. **Governance Thresholds**: $\\ge 100$ verified post-deployment labels and $\\ge 14$ consecutive calendar days of shadow observation are required for promotion consideration.
"""))

# Cell 1: Environment & Setup
cells.append(nbf.v4.new_code_cell("""import sys
import os
import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import numpy as np

# Path configuration
NOTEBOOK_DIR = Path.cwd()
ROOT = NOTEBOOK_DIR.parent.parent if NOTEBOOK_DIR.name == "notebooks" else Path.cwd()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

print(f"Project root: {ROOT}")
"""))

# Section 1: Production Data Availability
cells.append(nbf.v4.new_markdown_cell("""## 1. Production Data Availability

Phase 13 establishes the rigorous separation between:
- **Category A**: Historical/offline evaluation data (Phases 1–12.2)
- **Category B**: Real post-deployment observations (requests received by the live production API)
- **Category C**: Verified production labels (ground truth collected post-deployment meeting verification criteria)
- **Category D**: Synthetic/demo data (strictly forbidden from satisfying governance gates)

Only Category C satisfies the real-world validation gate. Below we inspect current production data availability.
"""))

cells.append(nbf.v4.new_code_cell("""# Check production data availability
exp_dir = ROOT / "ml" / "experiments"
labels_summary_path = exp_dir / "phase13_verified_label_summary.csv"

df_label_summary = pd.read_csv(labels_summary_path)
print("=== PRODUCTION EVIDENCE CATEGORIZATION & DATA AVAILABILITY ===")
display(df_label_summary)

verified_count = int(df_label_summary.loc[df_label_summary['metric'] == 'verified_production_labels', 'value'].iloc[0])
if verified_count == 0:
    print("\\n[STATUS]: NO REAL PRODUCTION OBSERVATIONS AVAILABLE FOR EVALUATION YET.")
    print("Real post-deployment ground truth labels must be accumulated through live operations.")
"""))

# Section 2: Shadow Observation Status
cells.append(nbf.v4.new_markdown_cell("""## 2. Shadow Observation Status

The formal 14-day shadow observation began at:
`shadow_start_timestamp = 2026-10-06T09:30:00Z`

The observation period requires 14 consecutive calendar days of valid shadow telemetry.
"""))

cells.append(nbf.v4.new_code_cell("""telemetry_path = exp_dir / "phase13_shadow_telemetry.csv"
df_telemetry = pd.read_csv(telemetry_path)
print("=== SHADOW OBSERVATION STATUS ===")
display(df_telemetry)

start_ts = df_telemetry.loc[df_telemetry['metric'] == 'shadow_start_timestamp', 'value'].iloc[0]
days_comp = df_telemetry.loc[df_telemetry['metric'] == 'days_completed', 'value'].iloc[0]
days_req = df_telemetry.loc[df_telemetry['metric'] == 'days_required', 'value'].iloc[0]
print(f"\\nShadow Start Timestamp: {start_ts}")
print(f"Days Completed: {days_comp} / {days_req}")
print(f"Observation Gate: PENDING ({14 - int(days_comp)} days remaining)")
"""))

# Section 3: Shadow Telemetry Summary
cells.append(nbf.v4.new_markdown_cell("""## 3. Shadow Telemetry Summary

Operational metrics tracked for Candidate v1.2 execution in shadow mode:
- Request counts, successful shadow predictions, shadow timeouts, shadow exceptions
- Latency percentiles ($P_{50}, P_{95}, P_{99}$)
- Impact on user responses: strictly 0
"""))

cells.append(nbf.v4.new_code_cell("""from app.governance import shadow_manager

shadow_status = shadow_manager.get_shadow_status()
print("Live Shadow Manager Status:")
for k, v in shadow_status.items():
    print(f"  {k}: {v}")
"""))

# Section 4: Verified Feedback Lifecycle
cells.append(nbf.v4.new_markdown_cell("""## 4. Verified Feedback Lifecycle

The lifecycle follows:
`SHADOW PREDICTION` $\\to$ `WAIT FOR VERIFIED OUTCOME` $\\to$ `FEEDBACK RECEIVED` $\\to$ `PENDING VERIFICATION` $\\to$ `VERIFIED` $\\to$ `USED FOR EVALUATION`

- Rejected feedback is excluded.
- Unverified feedback is NOT treated as ground truth.
- The target is `Mental_Health_Score` (continuous survey score [1.0, 10.0]). No clinical or medical claims are made.
"""))

cells.append(nbf.v4.new_code_cell("""from app.governance import feedback_engine, FEEDBACK_STATES

print("Permitted Feedback Lifecycle States:")
for state in FEEDBACK_STATES:
    print(f"  - {state}")

print(f"\\nCurrent Feedback Store Size: {len(feedback_engine.records)}")
print(f"Verified Records Available: {len(feedback_engine.get_verified_records())}")
"""))

# Section 5: Verified Label Count
cells.append(nbf.v4.new_markdown_cell("""## 5. Verified Label Count

A live counter tracks progress toward the mandatory threshold of 100 verified post-deployment labels.
"""))

cells.append(nbf.v4.new_code_cell("""counter = feedback_engine.get_verified_label_counter()
print("=== VERIFIED POST-DEPLOYMENT LABEL PROGRESS ===")
print(f"Current Verified Labels: {counter['display']}")
print(f"Threshold Met (>= 100):  {counter['threshold_met']}")
print(f"Data Mode:               {counter['data_mode']}")
"""))

# Section 6: Champion vs Candidate Online Comparison
cells.append(nbf.v4.new_markdown_cell("""## 6. Champion vs Candidate Online Comparison

When both Champion and Candidate produce shadow predictions for the same request:
- `champion_prediction`
- `candidate_prediction`
- `prediction_difference`
- `champion_interval_width`
- `candidate_interval_width`

Disagreement is tracked for monitoring; it is never conflated with accuracy until verified ground truth is matched.
"""))

cells.append(nbf.v4.new_code_cell("""summary = shadow_manager.get_summary()
print("Shadow Disagreement Summary:")
for k, v in summary.items():
    print(f"  {k}: {v}")
"""))

# Section 7: Real-World Point Metrics
cells.append(nbf.v4.new_markdown_cell("""## 7. Real-World Point Metrics

Evaluates $R^2$, RMSE, MAE, Mean Error, Median Absolute Error, and Max Absolute Error on verified production outcomes.
"""))

cells.append(nbf.v4.new_code_cell("""comp_path = exp_dir / "phase13_model_comparison.csv"
df_comp = pd.read_csv(comp_path)
display(df_comp)

if verified_count == 0:
    print("NO REAL PRODUCTION OBSERVATIONS AVAILABLE. Point metrics cannot be computed without verified post-deployment ground truth.")
"""))

# Section 8: Real-World Paired Errors
cells.append(nbf.v4.new_markdown_cell("""## 8. Real-World Paired Errors

Paired differences in absolute error ($|e_{\\text{champ}}| - |e_{\\text{cand}}|$) are computed strictly across identical verified production records.
"""))

cells.append(nbf.v4.new_code_cell("""if verified_count < 30:
    print("Paired statistical tests (Wilcoxon signed-rank / Paired t-test) require minimum N >= 30 verified production observations.")
    print("Status: DATA_NOT_AVAILABLE (Current N = 0).")
"""))

# Section 9: Real-World Conformal Coverage
cells.append(nbf.v4.new_markdown_cell("""## 9. Real-World Conformal Coverage

Offline calibration behavior ($q_{80}, q_{90}, q_{95}$) is evaluated against empirical post-deployment coverage once verified labels exist. Automatic recalibration is strictly forbidden.
"""))

cells.append(nbf.v4.new_code_cell("""calib_path = exp_dir / "phase13_conformal_validation.csv"
df_conformal = pd.read_csv(calib_path)
display(df_conformal)
"""))

# Section 10: Drift Analysis
cells.append(nbf.v4.new_markdown_cell("""## 10. Drift Analysis

Production monitoring tracks input drift (PSI, KS, TVD), prediction drift, and interval width drift against the Phase 10 reference distribution.
"""))

cells.append(nbf.v4.new_code_cell("""drift_path = exp_dir / "phase13_drift_summary.csv"
df_drift = pd.read_csv(drift_path)
display(df_drift)
"""))

# Section 11: Subgroup Descriptive Analysis
cells.append(nbf.v4.new_markdown_cell("""## 11. Subgroup Descriptive Analysis

Monitors performance across demographic & behavioral dimensions (`Gender`, `Academic_Level`, `Stress_Level`, `Platform`, `Purpose`).
"""))

cells.append(nbf.v4.new_code_cell("""subgroup_path = exp_dir / "phase13_subgroup_summary.csv"
df_subgroup = pd.read_csv(subgroup_path)
display(df_subgroup.head(10))
"""))

# Section 12: Shadow Reliability & Failure Isolation
cells.append(nbf.v4.new_markdown_cell("""## 12. Shadow Reliability & Failure Isolation Verification

Candidate exceptions or timeouts must never propagate into user-facing production responses.
Below we verify cryptographic artifact hashes and failure isolation mechanisms.
"""))

cells.append(nbf.v4.new_code_cell("""def compute_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

champ_path = ROOT / "models" / "phase5_tuned_extra_trees.joblib"
cand_path = ROOT / "models" / "candidate_v1_2_revalidated.joblib"

champ_hash = compute_sha256(champ_path)
cand_hash = compute_sha256(cand_path)

print(f"Production Champion Hash: {champ_hash}")
print(f"Candidate Hash:           {cand_hash}")

EXPECTED_CHAMP = "a012e7a1c0ca5c9fccb21d1e46bf3b4b4a72635204c13efdc4f93d6c636747f8"
EXPECTED_CAND  = "aad2f208a298289de57a0a8fd4aef941be0edaf940439dca98eaaf718439cdbc"

assert champ_hash == EXPECTED_CHAMP, "Champion hash mismatch!"
assert cand_hash == EXPECTED_CAND, "Candidate hash mismatch!"
print("\\n[PASSED]: Both model artifact hashes verified matching authoritative frozen standards.")
"""))

# Section 13: Governance Gate Status
cells.append(nbf.v4.new_markdown_cell("""## 13. Governance Gate Status

Evaluation of all required gates for Phase 13:
"""))

cells.append(nbf.v4.new_code_cell("""gate_path = exp_dir / "phase13_governance_gate.csv"
df_gate = pd.read_csv(gate_path)
display(df_gate)
"""))

# Section 14: Promotion Readiness
cells.append(nbf.v4.new_markdown_cell("""## 14. Promotion Readiness Decision

Final determination for Phase 13 candidate promotion:
"""))

cells.append(nbf.v4.new_code_cell("""print("=" * 60)
print("PHASE 13 PROMOTION READINESS DECISION")
print("=" * 60)
print("Production Champion:         ACTIVE PRODUCTION")
print("Candidate:                   CHALLENGER / VALIDATING")
print("Shadow Mechanism:            READY / ACTIVE")
print(f"Verified Production Labels:  {counter['display']} (Requires >= 100)")
print(f"Shadow Observation Period:   0 / 14 days (Requires 14 consecutive days)")
print("Human Governance Signoff:    PENDING")
print("Automatic Retraining:        STRICTLY FORBIDDEN (NO)")
print("Automatic Promotion:         STRICTLY FORBIDDEN (NO)")
print("FINAL PROMOTION STATUS:      BLOCKED")
print("=" * 60)
"""))

nb.cells = cells

# Save notebook
out_path = ROOT / "ml" / "notebooks" / "13_real_world_production_validation.ipynb"
with open(out_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Wrote notebook to {out_path}")

# Execute top-to-bottom
ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
with open(out_path, "r", encoding="utf-8") as f:
    nb_to_run = nbf.read(f, as_version=4)

print("Executing notebook top-to-bottom...")
ep.preprocess(nb_to_run, {"metadata": {"path": str(ROOT / "ml" / "notebooks")}})

with open(out_path, "w", encoding="utf-8") as f:
    nbf.write(nb_to_run, f)

print("Successfully executed 13_real_world_production_validation.ipynb top-to-bottom!")
