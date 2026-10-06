# Phase 2: Data Quality & Cleaning Audit Report

**Dataset:** `Student Social Media And Mental Health Impact.csv`  
**Raw Location:** `ml/data/raw/Student Social Media And Mental Health Impact.csv`  
**Execution Context:** `ml/notebooks/02_data_quality_eda.ipynb`  
**Date:** October 2026  
**Auditor:** Antigravity AI Pair Programmer  

---

## 1. Raw Dataset Integrity & Preservation

* **Raw File Path:** [`ml/data/raw/Student Social Media And Mental Health Impact.csv`](file:///c:/Users/msiva/Music/Mental-Health-Score/ml/data/raw/Student%20Social%20Media%20And%20Mental%20Health%20Impact.csv)
* **SHA-256 Hash:** `1BB518B237ACD5BD4FF4E71056ECD81769C3C49B077A872943C56BA26CCC12B5`
* **Raw Dimensions:** 5,000 rows × 13 columns (403,997 bytes).
* **Preservation Status:** **100% UNTOUCHED**. All deduplication, filtering, and corrections were executed in-memory to generate an isolated clean dataset for modeling. The raw source CSV was not overwritten.

---

## 2. Duplicate Record Identification & Resolution

* **Raw Record Count:** 5,000
* **Duplicate Detection Method:** `raw_df.duplicated(keep=False)`
* **Identified Duplicate Pairs (2 rows / 4 records total):**
  1. **Row 2405** (Duplicate of Row 886): Age: 19, Female, Other, Undergraduate, Instagram, Entertainment, Usage: 4.8h, Unlocks: 153, Study: 2.1h, Physical: 1.8h, Sleep: 6.2h, Stress: High, Score: 4.1.
  2. **Row 2463** (Duplicate of Row 1870): Age: 21, Male, Other, Undergraduate, TikTok, Entertainment, Usage: 5.2h, Unlocks: 180, Study: 3.0h, Physical: 1.6h, Sleep: 7.0h, Stress: Low, Score: 7.5.
* **Cleaning Action:** `df_clean = raw_df.drop_duplicates(keep='first').copy()`
* **Rows Removed:** 2
* **Post-Deduplication Record Count:** **4,998 rows**

---

## 3. Invalid Value Correction: Physical Activity Hours

* **Identified Defect:** 10 records contained negative durations in `Physical_Activity_Hours`.
* **Observed Negative Values:** `[-0.1, -0.1, -0.3, -0.1, -0.2, -0.1, -0.4, -0.3, -0.2, -0.2]`
* **Root Cause Diagnosis:** Negative exercise duration is physically impossible. This represents manual data-entry errors, sensor bias, or floating-point generation artifacts.
* **Justified Correction:** `df_clean['Physical_Activity_Hours'] = df_clean['Physical_Activity_Hours'].clip(lower=0.0)`.
  - Flooring negative values to `0.0` preserves all other valid attributes for those 10 students (age, stress level, sleep, score) without discarding informative survey responses.
* **Verification:** Post-correction minimum `Physical_Activity_Hours` is exactly `0.0`. Zero records remain negative.

---

## 4. Comprehensive Domain & Range Validation

| Feature Name | Type | Inferred Domain | Observed Range | Validation Status | Detailed Finding |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Age` | Numerical | Collegiate young adults (18–30) | 18 – 24 | **VALID** | Strictly bounded collegiate cohort. Mean = 20.82 yrs. |
| `Gender` | Categorical | Binary nominal | Male (52.7%), Female (47.3%) | **VALID** | Balanced distribution. 0 nulls. |
| `Country` | Categorical | Global sovereign nations | 111 unique categories | **VALID** | High cardinality; managed via leakage-safe grouping. |
| `Academic_Level` | Categorical | Academic tier | Undergrad (72.6%), Grad (18.4%), High School (9.0%) | **VALID** | Consistent with age range. |
| `Most_Used_Platform` | Categorical | Social media services | 12 distinct platforms | **VALID** | Instagram (22.6%) and TikTok (18.4%) dominate. |
| `Purpose_Of_Use` | Categorical | Usage driver | Entertainment (51.0%), Education (21.9%), etc. | **VALID** | 4 clean nominal classes. |
| `Avg_Daily_Usage_Hours` | Numerical | Daily screen hours ($0 \le h \le 24$) | 1.0 – 8.8 hrs | **VALID** | Normal distribution. Mean = 5.08 hrs/day. |
| `Daily_Unlocks` | Numerical | Count of unlocks ($\ge 0$) | 62 – 273 unlocks | **VALID** | Normal distribution. Mean = 171.4 unlocks/day. |
| `Study_Hours` | Numerical | Daily study hours ($0 \le h \le 24$) | 0.3 – 8.3 hrs | **VALID** | Mild right-skew (+0.436); normalized via `log1p`. |
| `Physical_Activity_Hours`| Numerical | Daily exercise ($0 \le h \le 24$) | -0.4 – 4.1 hrs (Raw) $\to$ 0.0 – 4.1 hrs (Clean) | **FIXED** | 10 negative records corrected to 0.0. |
| `Sleep_Hours_Per_Night` | Numerical | Nightly sleep ($0 \le h \le 24$) | 3.6 – 9.9 hrs | **VALID** | Bell-shaped curve. Mean = 6.63 hrs/night. |
| `Stress_Level` | Categorical | Perceived stress scale | Low (12.9%), Medium (25.9%), High (28.8%), Very High (32.4%) | **VALID** | Ordinal relationship confirmed via score correlation. |
| `Mental_Health_Score` | Numerical | Target score ($0 \le s \le 10$) | 3.6 – 9.4 | **VALID** | Near-normal continuous distribution (Mean = 6.23, Std = 1.28). |

---

## 5. Statistical Outlier Audit (Tukey 1.5×IQR)

| Feature | Q1 | Q3 | IQR | Lower Bound (Q1 - 1.5×IQR) | Upper Bound (Q3 + 1.5×IQR) | Outliers Count | Policy Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `Age` | 19.00 | 22.00 | 3.00 | 14.50 | 26.50 | 0 | No action needed. |
| `Avg_Daily_Usage_Hours` | 3.80 | 6.30 | 2.50 | 0.05 | 10.05 | 0 | No action needed. |
| `Daily_Unlocks` | 140.00 | 204.00 | 64.00 | 44.00 | 300.00 | 0 | No action needed. |
| `Study_Hours` | 1.50 | 4.20 | 2.70 | -2.55 | 8.25 | 2 | **RETAINED** (8.3 hrs is high but physically possible during exam prep). |
| `Physical_Activity_Hours`| 1.30 | 2.20 | 0.90 | -0.05 | 3.55 | 22 | **RETAINED** (Values up to 4.1 hrs represent collegiate student athletes; valid observations). |
| `Sleep_Hours_Per_Night` | 5.60 | 7.50 | 1.90 | 2.75 | 10.35 | 0 | No action needed. |
| `Mental_Health_Score` | 5.10 | 7.10 | 2.00 | 2.10 | 10.10 | 0 | No action needed. |

> **Outlier Policy Rule:** Statistical outliers do not automatically represent corrupt data. The 2 study hour outliers (8.3h) and 22 physical activity outliers ($>3.55$h) represent valid real-world behavioral tails. Deleting them would artificially reduce demographic variance. They were intentionally preserved.

---

## 6. Clean Dataset In-Memory Specification

```text
==================================================
CLEAN DATASET INGESTION SUMMARY
==================================================
Raw Records Ingested:        5,000
Duplicate Records Dropped:   2 (Indices 2405, 2463)
Invalid Values Corrected:    10 (Physical_Activity_Hours < 0 -> 0.0)
Final Clean Records:         4,998
Total Features:              12 predictors + 1 continuous target
Total Missing Values:        0 (100.0% Complete)
Modeling Partition:          80% Train (3,998) / 20% Test (1,000)
==================================================
```
