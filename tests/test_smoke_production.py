"""Production Smoke and Regression Verification Script.

Can be run locally or against target URL:
    python tests/test_smoke_production.py --url http://127.0.0.1:8000
"""

import sys
import argparse
import requests
import joblib
import pandas as pd
from pathlib import Path

# Deterministic test payload with verified feature schema
SMOKE_PAYLOAD = {
    "Age": 21,
    "Gender": "Female",
    "Academic_Level": "Undergraduate",
    "Country": "India",
    "Avg_Daily_Usage_Hours": 4.5,
    "Most_Used_Platform": "Instagram",
    "Daily_Unlocks": 140,
    "Sleep_Hours_Per_Night": 7.0,
    "Study_Hours": 3.0,
    "Physical_Activity_Hours": 1.5,
    "Stress_Level": "Medium",
    "Purpose_Of_Use": "Education",
    "coverage": 0.90
}

def run_smoke_tests(base_url: str):
    print(f"=== INITIATING PRODUCTION SMOKE TESTS AGAINST: {base_url} ===")
    session = requests.Session()
    session.headers.update({"User-Agent": "ProductionSmokeTest/1.0"})

    # 1. Test /health
    print("\n1. Testing GET /health ...")
    r_health = session.get(f"{base_url}/health", timeout=10)
    assert r_health.status_code == 200, f"Health check failed: {r_health.status_code} - {r_health.text}"
    health_data = r_health.json()
    assert health_data["status"] == "ok", "Status must be ok"
    assert health_data["model_loaded"] is True, "model_loaded must be true"
    assert health_data["uncertainty_loaded"] is True, "uncertainty_loaded must be true"
    assert health_data["model_hash_verified"] is True, "model_hash_verified must be true"
    print(f"   [PASSED] Health status: {health_data['status']} | Model: {health_data['model_version']}")

    # 2. Test /predict
    print("\n2. Testing POST /predict ...")
    r_predict = session.post(f"{base_url}/predict", json=SMOKE_PAYLOAD, timeout=10)
    assert r_predict.status_code == 200, f"Predict failed: {r_predict.status_code} - {r_predict.text}"
    pred_data = r_predict.json()
    assert "estimated_wellbeing_score" in pred_data
    score = pred_data["estimated_wellbeing_score"]
    pi = pred_data["prediction_interval"]
    assert pi["nominal_coverage"] == 0.90
    assert pi["lower"] <= score <= pi["upper"], f"Ordering violated: {pi['lower']} <= {score} <= {pi['upper']}"
    assert pi["lower"] < pi["upper"], "Degenerate interval bounds"
    assert abs(pi["width"] - 1.1884) < 1e-2, f"Expected width 1.1884, got {pi['width']}"
    assert "disclaimer" in pred_data
    assert "clinical" in pred_data["disclaimer"].lower()
    print(f"   [PASSED] Score: {score} | 90% PI: [{pi['lower']}, {pi['upper']}] | Width: {pi['width']}")

    # 3. Direct Model Regression Check
    print("\n3. Testing Local Pipeline vs Serving Equivalence ...")
    model_path = Path(__file__).resolve().parent.parent / "models" / "phase5_tuned_extra_trees.joblib"
    if model_path.exists():
        direct_pipe = joblib.load(model_path)
        input_row = pd.DataFrame([{
            "Study_Hours": SMOKE_PAYLOAD["Study_Hours"],
            "Age": SMOKE_PAYLOAD["Age"],
            "Avg_Daily_Usage_Hours": SMOKE_PAYLOAD["Avg_Daily_Usage_Hours"],
            "Daily_Unlocks": SMOKE_PAYLOAD["Daily_Unlocks"],
            "Physical_Activity_Hours": SMOKE_PAYLOAD["Physical_Activity_Hours"],
            "Sleep_Hours_Per_Night": SMOKE_PAYLOAD["Sleep_Hours_Per_Night"],
            "Stress_Level": SMOKE_PAYLOAD["Stress_Level"],
            "Gender": SMOKE_PAYLOAD["Gender"],
            "Academic_Level": SMOKE_PAYLOAD["Academic_Level"],
            "Most_Used_Platform": SMOKE_PAYLOAD["Most_Used_Platform"],
            "Purpose_Of_Use": SMOKE_PAYLOAD["Purpose_Of_Use"],
            "Grouped_country": SMOKE_PAYLOAD["Country"]
        }])
        local_raw = float(direct_pipe.predict(input_row)[0])
        diff = abs(score - round(local_raw, 2))
        assert diff <= 0.01, f"Prediction drift detected: API={score}, Local={local_raw}"
        print(f"   [PASSED] Direct local model prediction: {local_raw:.4f} (API match delta: {diff:.4f})")

    # 4. Test /explain
    print("\n4. Testing POST /explain ...")
    r_explain = session.post(f"{base_url}/explain", json=SMOKE_PAYLOAD, timeout=20)
    assert r_explain.status_code == 200, f"Explain failed: {r_explain.status_code} - {r_explain.text}"
    exp_data = r_explain.json()
    assert "estimated_wellbeing_score" in exp_data
    assert "base_value" in exp_data
    assert len(exp_data["feature_contributions"]) == 12, "Must aggregate to 12 original features"
    print(f"   [PASSED] Base value: {exp_data['base_value']} | Top factors identified: {len(exp_data['positive_contributors'])} positive, {len(exp_data['negative_contributors'])} negative")

    # 5. Test Documentation
    print("\n5. Testing GET /docs ...")
    r_docs = session.get(f"{base_url}/docs", timeout=10)
    assert r_docs.status_code == 200
    print("   [PASSED] OpenAPI Swagger docs reachable.")

    print("\n=== ALL PRODUCTION SMOKE TESTS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run production smoke tests against target API")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Target API URL")
    args = parser.parse_args()
    run_smoke_tests(args.url.rstrip("/"))
