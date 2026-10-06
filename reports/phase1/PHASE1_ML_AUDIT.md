# Phase 1: Machine Learning Pipeline Audit & Evaluation

**Pipeline Focus:** Preprocessing, Feature Engineering, Model Architecture, Overfitting & Validation  
**Audit Date:** October 2026  
**Auditor:** Antigravity AI Pair Programmer  

---

## 1. Existing Preprocessing Architecture

The existing model utilizes a Scikit-learn `Pipeline` encapsulating a `ColumnTransformer` with 4 separate sub-pipelines:

```text
ColumnTransformer
├── Skewed_Pipeline: ['Study_Hours']
│     └── FunctionTransformer(np.log1p) ──> StandardScaler()
├── Plain_Numeric:   ['Age', 'Avg_Daily_Usage_Hours', 'Daily_Unlocks', 'Physical_Activity_Hours', 'Sleep_Hours_Per_Night']
│     └── StandardScaler()
├── Ordinal:         ['Stress_Level']
│     └── OrdinalEncoder(categories=[['Low', 'Medium', 'High', 'Very High']])
└── Normal:          ['Gender', 'Academic_Level', 'Most_Used_Platform', 'Purpose_Of_Use', 'Grouped_country']
      └── OneHotEncoder(handle_unknown='ignore')
```

### Critical Preprocessing Findings:
1. **Missing Imputers:** The notebook documentation (Cell 50) explicitly states: *"We include a SimpleImputer in every branch even though this dataset has zero missing values right now — it's a safety net."* In reality, **zero imputers exist** in the actual code (Cell 51). If an API request sends a null numerical field, the pipeline will crash with a `ValueError`.
2. **Post-Encoding Dimensionality:** 
   - `Study_Hours` (1) + Plain Numeric (5) + Ordinal (1) = 7 numerical features.
   - Categorical one-hot: `Gender` (2) + `Academic_Level` (3) + `Most_Used_Platform` (12) + `Purpose_Of_Use` (4) + `Grouped_country` (11) = 32 one-hot binary columns.
   - Total transformed features entering the estimator: **38 features** (verified via `rf.n_features_in_ = 38`).
3. **Log Transformation:** `np.log1p` on `Study_Hours` successfully reduced skewness from 0.436 to -0.198, normalizing the distribution for linear estimators.

---

## 2. Train/Test Methodology & Data Leakage Audit

### 2.1 Current Splitting Methodology
* **Implementation:** `train_test_split(X, y, test_size=0.30, random_state=42)`
* **Train Set:** 3,500 samples (70%)
* **Test Set:** 1,500 samples (30%)
* **Stratification:** None (continuous regression target).
* **Documentation Mismatch:** The notebook markdown (Cell 48) claims an 80/20 split (1,000 test rows), but the executable code uses `test_size=0.30` (1,500 test rows).

### 2.2 Data Leakage Audit Matrix

| Operation | Code Stage | Status | Forensic Explanation |
| :--- | :--- | :--- | :--- |
| **Country Frequency Extraction** | Before Split | **CONFIRMED LEAKAGE** | Top 10 countries were identified using `df['Country'].value_counts()` across all 5,000 rows. Test set category frequencies influenced feature definition. |
| **Physical Activity Clipping** | Before Split | **POTENTIAL LEAKAGE** | `clip(lower=0)` applied globally before splitting. Although bounded by constant 0.0, global transformation before split violates strict partition hygiene. |
| **Standard Scaling** | Inside Pipeline | **SAFE** | `StandardScaler()` is correctly fitted only on `X_train` inside `ColumnTransformer.fit()`. |
| **Log Transformation** | Inside Pipeline | **SAFE** | Stateless element-wise `log1p` transformation. |
| **One-Hot Encoding** | Inside Pipeline | **SAFE** | `OneHotEncoder(handle_unknown='ignore')` fitted strictly on `X_train`. Unseen test categories are cleanly ignored. |
| **Target Normalization** | N/A | **SAFE** | Target variable `y` is unscaled and transformed only in raw units. |

---

## 3. Models Evaluated in Baseline

Three distinct models were developed in the exploratory notebook:

### Model 1: Ordinary Least Squares Linear Regression
* **Pipeline:** Preprocessor + `LinearRegression()`
* **Parameters:** Default settings (fit_intercept=True)
* **Purpose:** Minimal baseline to verify linear separability.

### Model 2: Default Random Forest Regressor
* **Pipeline:** Preprocessor + `RandomForestRegressor(random_state=42)`
* **Parameters:** `n_estimators=100`, `max_depth=None`, `min_samples_split=2`, `min_samples_leaf=1`, `bootstrap=True`
* **Artifact:** This is the exact model serialized into `Mental_Health_Model.pkl`.

### Model 3: Tuned Random Forest Regressor
* **Pipeline:** Preprocessor + `RandomForestRegressor(random_state=42)` via `RandomizedSearchCV`
* **Search Budget:** 15 iterations, 5-fold cross-validation on `X_train`, scoring = $R^2$.
* **Best Parameters Discovered:**
  - `n_estimators`: 200
  - `max_depth`: 15
  - `min_samples_split`: 5
  - `min_samples_leaf`: 2
* **Note:** Although tuned to reduce overfitting, this model was **not** serialized for deployment in `main.py`.

---

## 4. Overfitting Analysis

The default Random Forest exhibits **severe overfitting**:

```text
Model: Random Forest Regressor (Default)
Train R²: 0.980907
Test R²:  0.878017
Gap:      0.102890 (10.29% drop in explained variance)

Cross-Validation 5-Fold R² on Train Set:
Fold 1: 0.8652
Fold 2: 0.8329
Fold 3: 0.8517
Fold 4: 0.8411
Fold 5: 0.8543
Mean CV R²: 0.8490 (Std: 0.0119)
```

### Why is the Model Overfitting?
1. **Unconstrained Tree Depth:** `max_depth=None` allows trees to grow until all leaves are pure or contain less than 2 samples.
2. **Minimal Leaf Size:** `min_samples_leaf=1` permits leaves representing a single noisy training sample.
3. **Artifact Size Inflation:** The unpruned ensemble contains 100 deep trees requiring **25.7 MB** of serialized disk space.

---

## 5. Statistical Reliability of Current Evaluation

1. **Single Test Set Vulnerability:** The project evaluated final models against a single 30% test split (`random_state=42`). No out-of-fold cross-validation test scores are reported.
2. **Tuned Model Comparison:** On the single holdout set, the tuned model scored $R^2 = 0.8650$ compared to $R^2 = 0.8776$ for the default unpruned model. Because the author optimized against a single test partition, the higher test variance of the default model was mistaken for superior performance.
3. **Absence of Uncertainty Bounds:** Predictions are output as point estimates (e.g., 6.19) with no prediction intervals, standard errors, or confidence bands.

---

## 6. Recommended V2 Modeling Strategy

1. **Multi-Algorithm Benchmark:**
   - Linear regularized: Ridge, ElasticNet
   - Gradient Boosting: LightGBM, XGBoost, CatBoost
   - Non-linear ensemble: Pruned Random Forest
2. **Evaluation Protocol:**
   - 80/20 train/test split fixed at project initiation.
   - 5-Fold Cross-Validation on the 80% train partition for model selection.
   - Single final evaluation of the winning model on the 20% untouched holdout test set.
3. **Explainability Architecture:**
   - Integrate TreeSHAP (`shap.TreeExplainer`) to compute exact Shapley values.
   - Generate global feature importances and local per-student waterfall plots.
4. **Uncertainty Quantification:**
   - Implement conformal prediction (e.g. via MAPIE) to produce calibrated 90% prediction intervals $[y_{min}, y_{max}]$ alongside point scores.
