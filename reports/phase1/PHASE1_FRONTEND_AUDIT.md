# Phase 1: Frontend User Interface Audit

**Interface Type:** Single Page Web Application  
**Technology Stack:** Vanilla HTML5, Vanilla CSS3 (Custom Properties), Vanilla ES6 JavaScript  
**Assets Audited:** `index.html`, `style.css`, `script.js`  
**Audit Date:** October 2026  
**Auditor:** Antigravity AI Pair Programmer  

---

## 1. Visual & Architectural Overview

The current frontend is an editorial, dark-themed single-page application titled **"Mental Health Signal — Student Wellness Analytics"**.

### Visual Elements & Design Strengths:
1. **Typography:** Uses Google Fonts (`Fraunces` serif display for titles, `Inter` for functional controls, `JetBrains Mono` for readouts and metadata).
2. **Noise Texture:** Incorporates a subtle `.noise-overlay` layered over a deep navy background (`#0D151D`), conveying a premium editorial feel.
3. **SVG Radial Gauge:** Implements a dynamic SVG arc (`M 30 140 A 100 100 0 0 1 210 140`) with tick marks and a 3-stop gradient (`#D9534F` red $\to$ `#E3B341` yellow $\to$ `#4C9A78` green).
4. **Non-Diagnostic Disclaimer:** Features explicit disclaimer copy: *"Built for informational purposes only — this is not a clinical assessment. If you're struggling, please talk to someone you trust."*

---

## 2. Component Hierarchy & Flow

```text
index.html
├── Header (<header class="site-header">)
│     ├── Eyebrow: "Student Wellness Analytics"
│     ├── Title: "Mental Health Signal"
│     └── Subtitle: Contextual framing
├── Main Layout (<main class="layout">)
│     ├── Form Panel (<section class="panel form-panel">)
│     │     ├── Group 01: Profile (Age, Gender, Country)
│     │     ├── Group 02: Digital Habits (Academic level, Platform, Purpose, Screen time, Unlocks)
│     │     ├── Group 03: Lifestyle & Stress (Study hours, Exercise, Sleep, Perceived stress)
│     │     └── Submit Button with CSS Loading Spinner
│     └── Result Panel (<aside class="panel result-panel">)
│           ├── State Idle: Inactive gauge track & prompt
│           ├── State Loading: Pulsing ring animation
│           ├── State Result: Animated filled gauge, score readout (0.0 - 10.0), signal band, advice
│           └── State Error: Error icon, server detail message, retry button
└── Footer (<footer class="site-footer">)
      └── Ethical / non-diagnostic disclaimer
```

---

## 3. UI State Management & API Client

### 3.1 State Transitions
The script manages 4 mutually exclusive states via the `showState(name)` function:
* `'idle'`: Default view on initial page load.
* `'loading'`: Triggered upon form submission; disables submit button and starts spinner.
* `'result'`: Displays predicted score, animates gauge stroke-dashoffset, and outputs band text.
* `'error'`: Displays connection failures or unprocessable entity messages.

### 3.2 Signal Band Mapping Logic
In `script.js`, scores are segmented into three qualitative categories:
* **Score $< 4.0$:** `"Signal: strained"` (*"Your responses suggest elevated strain right now. Small shifts in sleep or screen time can go a long way."*)
* **$4.0 \le \text{Score} < 7.0$:** `"Signal: balanced"` (*"Your rhythm looks fairly steady, with some room to recover and reset."*)
* **Score $\ge 7.0$:** `"Signal: strong"` (*"Your habits point to a well-supported, resilient baseline. Keep it up."*)

### 3.3 Server Error Handling (`applyServerValidationErrors`)
The frontend contains an advanced validation mapper:
* When FastAPI returns HTTP 422 with a structured Pydantic `detail` list, the frontend parses the `loc` path (e.g. `['body', 'age']`), locates the matching DOM element, and injects inline error text under that specific input.

---

## 4. Frontend Vulnerabilities & Defects Identified

| Defect / Limitation | Severity | Impact | Verified Behavior |
| :--- | :--- | :--- | :--- |
| **Hardcoded Remote URL** | **High** | Offline / Local failure | Commit `e1261e5` replaced `http://127.0.0.1:2200` with `https://mansik-santulan-score.onrender.com`. Because Render instances spin down, local testing failed until patched with dynamic host resolution. |
| **Lack of Explainability** | **Medium** | Black-box output | The UI displays only a final aggregate score (e.g. 6.19) with no breakdown of which habits (screen time vs sleep vs stress) drove the score up or down. |
| **Monolithic DOM Scripting** | **Medium** | Low maintainability | All DOM querying and mutation is handled directly across 305 lines in `script.js`. Scaling to multi-feature analytics requires modern component-based state. |
| **Accessibility (WAI-ARIA)** | **Low** | Assistive tech barrier | Segmented buttons for `stress_level` use `<button>` elements inside a `<div>` without `role="radiogroup"` or `aria-checked` attributes. |

---

## 5. Migration Recommendation (Target: React + Bootstrap)

As required by project guidelines, plain HTML/CSS/JavaScript should migrate to **React + Bootstrap** in Phase 9.

### Why React + Bootstrap?
1. **Component Modularity:** Encapsulates the assessment form, gauge visualizer, SHAP explanation waterfall, and what-if simulation sliders into testable components.
2. **Predictable State Management:** React hooks (`useState`, `useReducer`) eliminate direct DOM manipulations and race conditions during async model calls.
3. **Responsive Grid & Accessibility:** Bootstrap 5 provides out-of-the-box WAI-ARIA compliance, accessibility attributes, and responsive breakpoint grids.
4. **Rich Data Visualization:** React easily integrates with charting libraries (Chart.js / Recharts) for rendering local SHAP habit contributions.
5. **No Tailwind CSS:** Adheres strictly to the requirement forbidding Tailwind in favor of modern Bootstrap + custom scoped CSS tokens.
