# Phase 2: Data Leakage Elimination & Pipeline Isolation Report

**Focus:** Preventing Pre-Split Contamination in Category Mapping and Preprocessing  
**Execution Context:** `ml/notebooks/02_data_quality_eda.ipynb`  
**Date:** October 2026  
**Auditor:** Antigravity AI Pair Programmer  

---

## 1. The Phase 1 Data Leakage Flaw

In the original exploratory notebook (`ML_Project.ipynb`), the following code was executed before `train_test_split`:

```python
# FLAW IN PHASE 1: Executed globally across all 5,000 rows
top_countries = df['Country'].value_counts().index[:10].tolist()
df['Grouped_country'] = df['Country'].apply(group_countries)

# SPLIT HAPPENED AFTERWARDS:
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30, random_state=42)
```

### Why This Constituted Confirmed Leakage:
1. **Test Set Category Influences:** The selection of which countries were preserved as distinct one-hot features depended on test-set frequencies.
2. **Frequency Rank Shifts:** If a country had high frequency in the test partition but low frequency in the train partition, it was artificially retained as a distinct category based on unseen test data.
3. **Flawed Production Simulation:** In production, future student requests are unknown. A model must project unseen categories into a default bin (`"Other"`) based strictly on historical training support.

---

## 2. Phase 2 Leakage-Safe Architecture

In Phase 2, the pipeline enforces **strict temporal and statistical isolation**:

```text
[Clean Dataset (4,998 rows)]
              │
              ▼
[80/20 Train/Test Split (random_state=42)]
              │
      ┌───────┴────────────────────────┐
      ▼                                ▼
[Train Partition: 3,998 rows]   [Holdout Test Partition: 1,000 rows]
      │                                │
      ▼                                │ (Untouched & Isolated)
[Fit Top-10 Country Mapping]           │
      │                                │
      ▼                                ▼
[Apply Mapping to Train]        [Project SAME Mapping onto Test]
      │                                │
      ▼                                ▼
[Fit ColumnTransformer]         [Transform Test via Frozen Pipeline]
      │                                │
      ▼                                ▼
[5-Fold CV on Train]            [Single Final Holdout Evaluation]
```

---

## 3. Empirical Verification of Country Grouping

### 3.1 Top-10 Categories Learned Strictly on Training Partition (`train_df`):
Total training samples: 3,998.

| Rank | Learned Country | Training Frequency | Train Percentage | Mapping Action |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Other** (Pre-existing) | 1,513 | 37.84% | Retained as `"Other"` base bucket |
| **2** | **India** | 303 | 7.58% | Distinct Category |
| **3** | **USA** | 280 | 7.00% | Distinct Category |
| **4** | **Canada** | 184 | 4.60% | Distinct Category |
| **5** | **Australia** | 155 | 3.88% | Distinct Category |
| **6** | **UK** | 150 | 3.75% | Distinct Category |
| **7** | **Germany** | 109 | 2.73% | Distinct Category |
| **8** | **Mexico** | 75 | 1.88% | Distinct Category |
| **9** | **France** | 74 | 1.85% | Distinct Category |
| **10**| **Turkey** | 74 | 1.85% | Distinct Category |
| 11 | Spain (Cutoff) | 73 | 1.83% | Mapped to `"Other"` |
| 12 | Japan (Cutoff) | 63 | 1.58% | Mapped to `"Other"` |

### 3.2 Projection onto Test Partition (`test_df`):
Total test samples: 1,000.
* **Records matching Train Top-10:** 729 / 1,000 (72.90%).
* **Non-top-10 records mapped to "Other":** 271 / 1,000 (27.10%).
* **Pre-existing "Other" records in test:** 367 / 1,000.
* **Total "Other" in test set post-mapping:** $367 + 271 = 638 \text{ records } (63.80\%)$.
* **Result:** The distribution between train (64.88% "Other") and test (63.80% "Other") is virtually identical, proving stable projection without leakage.

---

## 4. Leakage Prevention Audit Matrix

| Pipeline Component | Operation | Fitted On | Applied To | Leakage Status | Evidence / Verification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Country Grouping** | Frequency extraction | `train_df['Country']` | `train_df`, `test_df` | **LEAKAGE-FREE** | Top-10 list computed strictly on 3,998 training records. |
| **Skew Transformation** | `np.log1p` | Stateless function | `X_train`, `X_test` | **LEAKAGE-FREE** | Element-wise mathematical operator; zero learned parameters. |
| **Numeric Imputation** | `SimpleImputer(strategy='median')`| `X_train` | `X_train`, `X_test` | **LEAKAGE-FREE** | Median statistics computed strictly from `X_train`. |
| **Standard Scaling** | `StandardScaler()` | `X_train` | `X_train`, `X_test` | **LEAKAGE-FREE** | Means ($\mu$) and standard deviations ($\sigma$) fitted strictly on `X_train`. |
| **Ordinal Encoding** | `OrdinalEncoder(categories=...)` | Static order definition | `X_train`, `X_test` | **LEAKAGE-FREE** | Pre-specified domain hierarchy `['Low', 'Medium', 'High', 'Very High']`. |
| **One-Hot Encoding** | `OneHotEncoder(handle_unknown='ignore')` | `X_train` | `X_train`, `X_test` | **LEAKAGE-FREE** | Fitted only on `X_train`. Unseen test categories project cleanly to zero-vectors. |
| **Cross-Validation** | 5-Fold KFold | `X_train` folds | Internal validation folds | **LEAKAGE-FREE** | Test partition was completely omitted from CV fold generation. |
| **Target Variable** | Raw score scaling | None | None | **LEAKAGE-FREE** | Target $y$ remains unscaled in original domain units (0–10). |

---

## 5. Conclusion

By shifting the train/test split to the very beginning of the modeling pipeline and embedding all statistical mappings strictly within the training fold, **all forms of data leakage identified in Phase 1 have been completely eliminated**.
