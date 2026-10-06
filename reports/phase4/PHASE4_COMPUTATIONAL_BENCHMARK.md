# PHASE 4 — COMPUTATIONAL BENCHMARK & SYSTEM PROFILING REPORT

**Project:** Student Mental Health / Wellbeing Score Prediction  
**Phase:** 4 — Multi-Model Benchmarking & Evidence-Based Model Selection  
**Date:** October 2026  
**Artifact Referenced:** [`ml/experiments/phase4_model_benchmark_results.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/experiments/phase4_model_benchmark_results.csv)  
**Visualization:** [`ml/evaluation/phase4_model_size_comparison.png`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/evaluation/phase4_model_size_comparison.png)

---

## 1. Executive Summary

Model selection for production applications requires balancing predictive performance against computational constraints: training latency, batch inference throughput, single-record response time, and artifact disk/memory footprint.

Phase 4 evaluated all 11 model candidates across three computational metrics:
1. **Fit / Training Time (seconds):** Total time to fit the entire pipeline (preprocessing + estimator) on 3,998 training samples.
2. **Inference Latency (milliseconds):** Time taken to generate predictions for a 1,000-sample test batch (`X_test`), averaged over standardized runs.
3. **Serialized Pipeline Size (Kilobytes):** Total file size of the fitted scikit-learn/joblib pipeline saved to disk.

---

## 2. Benchmark Results Table

| Model | Family | Fit Time (s) | Inference Time (ms / 1k items) | Latency per Sample (μs) | Artifact Size (KB) | Compressed Size (MB) |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Extra Trees** | Tree Ensemble | 7.40 s | 34.43 ms | 34.4 μs | 9,946.3 KB | ~9.71 MB |
| **Random Forest (Baseline)** | Tree Ensemble | 7.66 s | 30.54 ms | 30.5 μs | 5,504.6 KB | ~5.38 MB |
| **XGBoost** | Advanced Boosting | 1.40 s | 16.96 ms | 17.0 μs | 125.9 KB | ~0.12 MB |
| **HistGradientBoosting** | Boosting Ensemble | 1.36 s | 19.33 ms | 19.3 μs | 145.4 KB | ~0.14 MB |
| **LightGBM** | Advanced Boosting | **0.83 s** | 18.59 ms | 18.6 μs | 105.0 KB | ~0.10 MB |
| **CatBoost** | Advanced Boosting | 1.62 s | **11.66 ms** | **11.7 μs** | **45.5 KB** | **~0.04 MB** |
| **Gradient Boosting** | Boosting Ensemble | 2.10 s | 9.81 ms | 9.8 μs | 44.0 KB | ~0.04 MB |
| **Ridge (α=1.0)** | Linear Model | 0.20 s | 13.78 ms | 13.8 μs | 2.9 KB | <0.01 MB |
| **Linear Regression** | Linear Model | 0.18 s | 8.45 ms | 8.5 μs | 3.2 KB | <0.01 MB |
| **ElasticNet** | Linear Model | 0.24 s | 8.61 ms | 8.6 μs | 2.7 KB | <0.01 MB |
| **Dummy (Mean)** | Statistical Baseline | 0.19 s | 8.16 ms | 8.2 μs | 2.5 KB | <0.01 MB |

---

## 3. In-Depth Comparative Analysis

### 3.1 Training Efficiency
- **Fastest Overall:** Ordinary Least Squares (0.18 s) and Ridge (0.20 s).
- **Fastest Non-Linear:** **LightGBM** trained in **0.83 seconds**, nearly 9x faster than Random Forest (7.66 s) and Extra Trees (7.40 s). HistGradientBoosting (1.36 s), XGBoost (1.40 s), and CatBoost (1.62 s) also exhibited fast training speeds.
- **Tree Ensembles:** Extra Trees (7.40 s) and Random Forest (7.66 s) required the most compute during training due to constructing 100 deep, unpruned decision trees across 28 transformed input dimensions. However, 7.4 seconds is completely manageable for scheduled re-training pipelines.

### 3.2 Inference Latency & SLA Viability
- **Fastest Boosting Inference:** **CatBoost** achieved **11.66 ms** for 1,000 predictions, followed by XGBoost at **16.96 ms** and LightGBM at **18.59 ms**.
- **Extra Trees Inference:** Required **34.43 ms** for 1,000 items. On a per-sample basis:
  $$\text{Latency per sample} = \frac{34.43 \text{ ms}}{1000} \approx 0.0344 \text{ ms} = 34.4 \ \mu\text{s}$$
- **FastAPI / REST API SLA Assessment:**
  A typical interactive web service SLA targets $P_{99} < 50 \text{ ms}$ for the entire request-response cycle. At 0.034 ms per prediction, the model computation consumes less than **0.1%** of a typical 50 ms budget. Network transit and JSON serialization dominate latency, making Extra Trees safe for production deployment.

### 3.3 Artifact Size & Memory Footprint
- **GBDT Compression Efficiency:**
  - CatBoost: **45.5 KB**
  - LightGBM: **105.0 KB**
  - XGBoost: **125.9 KB**
  The boosted trees achieve small artifact sizes because they constrain depth (e.g. depth 6 for XGBoost) and rely on sequential additive corrections rather than deep individual trees.
- **Ensemble Tree Footprint:**
  - Random Forest: **5,504.6 KB (~5.5 MB)**
  - Extra Trees: **9,946.3 KB (~9.7 MB)**
  Because Extra Trees grows 100 deep trees with random split thresholds, the number of leaf nodes and internal split values is larger, yielding a ~9.7 MB serialized artifact.
- **Production Feasibility:**
  In modern containerized deployments (Docker, Kubernetes, AWS Lambda, Cloud Run), a 9.7 MB joblib payload is negligible. AWS Lambda allows up to 250 MB unzipped layers, and container images routinely accommodate hundreds of megabytes.

---

## 4. Multi-Criteria Trade-Off Evaluation

To evaluate architectural candidates holistically, models were scored across three dimensions:

| Criterion | Weight | Extra Trees | XGBoost | CatBoost | Random Forest |
|---|:---:|:---:|:---:|:---:|:---:|
| **Predictive Accuracy (CV R² & RMSE)** | 50% | **10 / 10** (0.9054) | 8.5 / 10 (0.8629) | 7.5 / 10 (0.8347) | 8.5 / 10 (0.8648) |
| **Inference Latency (<50 ms SLA)** | 25% | **9.0 / 10** (34.4 ms) | 9.8 / 10 (17.0 ms) | 10 / 10 (11.7 ms) | 9.2 / 10 (30.5 ms) |
| **Artifact Footprint (<50 MB)** | 25% | **8.5 / 10** (9.7 MB) | 9.8 / 10 (0.12 MB) | 10 / 10 (0.04 MB) | 9.0 / 10 (5.4 MB) |
| **Weighted Composite Score** | 100% | **9.38 / 10** | **9.15 / 10** | **8.75 / 10** | **8.80 / 10** |

### Decision Summary:
Extra Trees achieves the highest composite score (**9.38 / 10**). The 16.4% reduction in prediction error (RMSE dropping from 0.4641 to 0.3881) decisively outweighs the minor artifact size delta (9.7 MB vs. 0.12 MB).

---

## 5. Benchmarking Environment Specifications
- **Operating System:** Windows 11 Enterprise (x64)
- **CPU:** Multi-core x86_64 Processor (`n_jobs=-1` threading enabled)
- **Python Runtime:** Python 3.13.13
- **Primary Package Versions:**
  - `scikit-learn`: 1.6.1
  - `xgboost`: 3.4.1
  - `lightgbm`: 4.7.0
  - `catboost`: 1.2.10
  - `joblib`: 1.5.3
  - `numpy`: 2.2.3
  - `pandas`: 2.2.3
