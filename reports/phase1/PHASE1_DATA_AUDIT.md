# Phase 1: Comprehensive Data Audit Report

**Dataset:** `Student Social Media And Mental Health Impact.csv`  
**Location:** Repository root  
**Audit Date:** October 2026  
**Verification Method:** Empirical code execution via Python 3.13 / Pandas 3.0.5  

---

## 1. Dataset Dimensions & Overview

* **Total Records (Rows):** 5,000
* **Total Fields (Columns):** 13
* **Primary Key / Index:** Implicit integer index (0 to 4,999)
* **Dataset Target:** `Mental_Health_Score` (Continuous float, scale 0.0 – 10.0)
* **Feature Count:** 12 predictors (6 numerical, 6 categorical)

---

## 2. Column Schema & Data Types

| Column Name | Raw Pandas Dtype | Inferred Logical Type | Domain / Range | Missing Values | Cardinality |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Age` | `int64` | Discrete Numerical | 18 – 24 years | 0 (0.0%) | 7 |
| `Gender` | `object` / `str` | Nominal Categorical | Male, Female | 0 (0.0%) | 2 |
| `Country` | `object` / `str` | Nominal Categorical | 111 sovereign nations / 'Other' | 0 (0.0%) | 111 |
| `Academic_Level` | `object` / `str` | Ordinal / Categorical | High School, Undergraduate, Graduate | 0 (0.0%) | 3 |
| `Most_Used_Platform` | `object` / `str` | Nominal Categorical | 12 social media platforms | 0 (0.0%) | 12 |
| `Purpose_Of_Use` | `object` / `str` | Nominal Categorical | Entertainment, Education, Networking, News | 0 (0.0%) | 4 |
| `Avg_Daily_Usage_Hours` | `float64` | Continuous Numerical | 1.0 – 8.8 hours | 0 (0.0%) | 79 |
| `Daily_Unlocks` | `int64` | Discrete Numerical | 62 – 273 unlocks | 0 (0.0%) | 212 |
| `Study_Hours` | `float64` | Continuous Numerical | 0.3 – 8.3 hours | 0 (0.0%) | 81 |
| `Physical_Activity_Hours`| `float64` | Continuous Numerical | -0.4 – 4.1 hours (10 negative values) | 0 (0.0%) | 46 |
| `Sleep_Hours_Per_Night` | `float64` | Continuous Numerical | 3.6 – 9.9 hours | 0 (0.0%) | 64 |
| `Stress_Level` | `object` / `str` | Ordinal Categorical | Low, Medium, High, Very High | 0 (0.0%) | 4 |
| `Mental_Health_Score` | `float64` | Target (Continuous) | 3.6 – 9.4 score points | 0 (0.0%) | 59 |

---

## 3. Data Quality Findings & Anomalies

### 3.1 Missing Values
* **Zero null/NaN entries** exist across any column in the raw dataset.
* Every single record contains 100% complete fields.

### 3.2 Duplicate Records
* **Empirical Verification:** Exactly **2 duplicate rows** exist in the raw dataset.
  - Row 2405 is an exact duplicate of Row 886 (Age: 19, Female, Stress: High, Score: 4.1).
  - Row 2463 is an exact duplicate of Row 1870 (Age: 21, Male, Stress: Low, Score: 7.5).
* **Discrepancy Note:** Markdown cell 8 in the notebook claimed *"Zero duplicate rows. Nothing to remove here"*, yet cell 10 executed `df.duplicated().sum()` which returned `2`. In cell 36, `df = df.drop_duplicates()` was executed, which removed these 2 rows (leaving 4,998 records). However, our model inspection proved that the serialized artifact was trained on the un-deduplicated 5,000-row dataset.

### 3.3 Invalid & Impossible Values
* **Physical Activity Hours Anomaly:** Exactly **10 records** contain negative physical activity hours, ranging from `-0.1` to `-0.4`.
  - Values identified: `[-0.1, -0.1, -0.3, -0.1, -0.2, -0.1, -0.4, -0.3, -0.2, -0.2]`.
  - Negative duration is physically impossible. This represents data entry/sensor error or synthetic generation artifacts.
* **All Other Numerical Ranges are Valid:**
  - `Age` is restricted strictly to young adults (18 to 24).
  - `Daily_Usage` max is 8.8 hours ($\le 24$).
  - `Sleep_Hours` ranges from 3.6 to 9.9 hours ($\le 24$).
  - `Daily_Unlocks` minimum is 62, maximum is 273.
  - `Mental_Health_Score` spans 3.6 to 9.4 (within the 0 to 10 range).

---

## 4. Numerical Distributions & Outlier Analysis

Summary statistics computed across all 5,000 raw samples:

| Feature | Mean | Std Dev | Min | 25% | Median (50%) | 75% | Max | Skewness | Kurtosis | IQR Outliers (1.5 IQR) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Age** | 20.82 | 1.74 | 18.0 | 19.0 | 21.0 | 22.0 | 24.0 | +0.155 | -0.913 | 0 |
| **Avg_Daily_Usage_Hours** | 5.08 | 1.65 | 1.0 | 3.8 | 5.0 | 6.3 | 8.8 | +0.006 | -0.768 | 0 |
| **Daily_Unlocks** | 171.45 | 42.86 | 62.0 | 140.0 | 171.0 | 204.0 | 273.0 | +0.002 | -0.709 | 0 |
| **Study_Hours** | 3.01 | 1.64 | 0.3 | 1.5 | 2.8 | 4.2 | 8.3 | +0.436 | -0.727 | 2 records ($> 8.25$) |
| **Physical_Activity_Hours** | 1.75 | 0.67 | -0.4 | 1.3 | 1.7 | 2.2 | 4.1 | +0.040 | -0.226 | 22 records ($< -0.05$ or $> 3.55$) |
| **Sleep_Hours_Per_Night** | 6.63 | 1.22 | 3.6 | 5.6 | 6.6 | 7.5 | 9.9 | +0.124 | -0.879 | 0 |
| **Mental_Health_Score (Target)** | 6.23 | 1.28 | 3.6 | 5.1 | 6.1 | 7.1 | 9.4 | +0.207 | -0.803 | 0 |

### Key Observations:
1. **Target Normality:** The target variable `Mental_Health_Score` follows a near-Gaussian distribution centered at mean 6.23 with standard deviation 1.28 and minimal skewness (0.207). It has no extreme outliers.
2. **Device Usage Variables:** Both `Avg_Daily_Usage_Hours` and `Daily_Unlocks` exhibit nearly perfect symmetric distributions (skewness $< 0.01$).
3. **Study Hours Skew:** `Study_Hours` exhibits positive right-skew (0.436), prompting the existing notebook's decision to apply `np.log1p`.

---

## 5. Categorical Distributions & Cardinality Audit

### 5.1 Gender Distribution
* **Male:** 2,635 (52.70%)
* **Female:** 2,365 (47.30%)
* Balanced representation; no missing or unspecified genders.

### 5.2 Academic Level
* **Undergraduate:** 3,632 (72.64%)
* **Graduate:** 918 (18.36%)
* **High School:** 450 (9.00%)
* Strong undergraduate concentration reflecting collegiate demographic bias.

### 5.3 Most Used Platform
| Platform | Count | Percentage |
| :--- | :--- | :--- |
| **Instagram** | 1,130 | 22.60% |
| **TikTok** | 918 | 18.36% |
| **Facebook** | 719 | 14.38% |
| **LinkedIn** | 523 | 10.46% |
| **YouTube** | 491 | 9.82% |
| **Twitter** | 462 | 9.24% |
| **Snapchat** | 420 | 8.40% |
| **WhatsApp** | 175 | 3.50% |
| **LINE** | 50 | 1.00% |
| **VKontakte** | 40 | 0.80% |
| **KakaoTalk** | 36 | 0.72% |
| **WeChat** | 36 | 0.72% |

### 5.4 Primary Purpose of Use
* **Entertainment:** 2,552 (51.04%)
* **Education:** 1,094 (21.88%)
* **Networking:** 793 (15.86%)
* **News:** 561 (11.22%)

### 5.5 Stress Level (Ordinal Target Predictor)
* **Very High:** 1,621 (32.42%)
* **High:** 1,440 (28.80%)
* **Medium:** 1,295 (25.90%)
* **Low:** 644 (12.88%)
* Clear ordinal step-down relationship with mental health score (confirmed via EDA boxplot).

---

## 6. Country Grouping & High-Cardinality Analysis

The `Country` feature contains **111 unique categories**.

### Frequency of Top 15 Countries:
1. **Other (pre-existing in raw dataset):** 1,880 (37.60%)
2. **India:** 389 (7.78%)
3. **USA:** 355 (7.10%)
4. **Canada:** 230 (4.60%)
5. **Australia:** 198 (3.96%)
6. **UK:** 185 (3.70%)
7. **Germany:** 136 (2.72%)
8. **Mexico:** 94 (1.88%)
9. **Turkey:** 94 (1.88%)
10. **France:** 87 (1.74%)
11. Spain: 83 (1.66%)
12. Ireland: 81 (1.62%)
13. Japan: 77 (1.54%)
14. Denmark: 77 (1.54%)
15. Switzerland: 73 (1.46%)

### The Grouping Mechanism:
* The existing pipeline selects the top 10 most frequent countries:
  `['Other', 'India', 'USA', 'Canada', 'Australia', 'UK', 'Germany', 'Mexico', 'Turkey', 'France']` (representing 3,648 records, 72.96%).
* All remaining 101 countries (1,352 records, 27.04%) are mapped into `'Other'`.
* **Total records in 'Other' after grouping:**
  $$1,880 \text{ (pre-existing)} + 1,351 \text{ (aggregated)} = 3,231 \text{ records } (64.62\%)$$
* **Data Leakage Risk:** This top-10 list was derived globally from the entire 5,000-row dataset before splitting. In V2, frequent categories must be discovered strictly within the training fold.

---

## 7. Audit of Existing Cleaning Rules

| Existing Cleaning Rule | Code Implementation | Rows Affected | Justified? | Recommendation for V2 |
| :--- | :--- | :--- | :--- | :--- |
| **Deduplication** | `df = df.drop_duplicates()` | 2 rows | **YES** | Retain in V2 data ingestion. Ensure split occurs *after* deduplication. |
| **Physical Activity Floor** | `df['Physical_Activity_Hours'].clip(lower=0)` | 10 rows | **YES** | Negative hours are physical impossibilities. Retain floor clipping at 0.0 or replace with a domain-aware scikit-learn transformer. |
| **Country Consolidation** | `apply(group_countries)` | 1,352 rows mapped to 'Other' | **PARTIALLY** | The 111-category cardinality requires reduction, but 64.6% of data falling into 'Other' destroys geographical variance. Replace with Scikit-learn `OneHotEncoder(min_frequency=...)` or Target Encoding fitted strictly on train set. |

---

## 8. Recommended V2 Data Pipeline

```text
[Raw Survey Data]
       │
       ▼
[Schema Validation: Validate types, nulls, bounds]
       │
       ▼
[Deduplication: drop_duplicates(keep='first')]  --> (4,998 clean rows)
       │
       ▼
[Data Sanitization: clip(Physical_Activity_Hours, lower=0)]
       │
       ▼
[TRAIN / TEST SPLIT: 80% Train (3,998) / 20% Holdout (1,000), random_state=42]
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
[Train Fold]                    [Untouched Holdout Test Fold]
       │                                 │
[Fit Preprocessing Pipeline]             │
  - Discover Frequent Countries          │
  - Fit Scalers & Encoders               │
       │                                 │
       ▼                                 ▼
[Transform Train Data]          [Transform Test Data via Frozen Pipeline]
```
