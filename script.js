(() => {
  "use strict";

  // ---------------------------------------------------------
  // 1. DYNAMIC API BASE RESOLUTION
  // Resolves locally or via current origin.
  // ---------------------------------------------------------
  const API_BASE = window.__API_BASE__ || (
    (window.location.protocol === "file:")
      ? "http://127.0.0.1:8000"
      : window.location.origin
  );

  // DOM Elements
  const form = document.getElementById("predict-form");
  const submitBtn = document.getElementById("submit-btn");
  const formResetBtn = document.getElementById("form-reset-btn");
  const resetResultBtn = document.getElementById("reset-result-btn");
  const errorRetryBtn = document.getElementById("error-retry-btn");

  const stateIdle = document.getElementById("state-idle");
  const stateLoading = document.getElementById("state-loading");
  const stateResult = document.getElementById("state-result");
  const stateError = document.getElementById("state-error");

  const apiStatusPill = document.getElementById("api-status-pill");
  const apiStatusText = document.getElementById("api-status-text");

  const scoreNumberEl = document.getElementById("score-number");
  const interpretationTextEl = document.getElementById("interpretation-text");

  const uncertaintyCoverageTagEl = document.getElementById("uncertainty-coverage-tag");
  const intervalHighlightEl = document.getElementById("interval-highlight");
  const intervalPointMarkerEl = document.getElementById("interval-point-marker");
  const boundLabelLowerEl = document.getElementById("bound-label-lower");
  const boundLabelEstimateEl = document.getElementById("bound-label-estimate");
  const boundLabelUpperEl = document.getElementById("bound-label-upper");

  const metricIntervalRangeEl = document.getElementById("metric-interval-range");
  const metricIntervalWidthEl = document.getElementById("metric-interval-width");
  const metricModelNameEl = document.getElementById("metric-model-name");
  const metricUncertaintyMethodEl = document.getElementById("metric-uncertainty-method");

  const explainBtn = document.getElementById("explain-btn");
  const explainBtnLabel = document.getElementById("explain-btn-label");
  const explainSpinner = document.getElementById("explain-spinner");
  const factorsWrapper = document.getElementById("factors-wrapper");
  const shapSummaryMetaEl = document.getElementById("shap-summary-meta");
  const positiveFactorsList = document.getElementById("positive-factors-list");
  const negativeFactorsList = document.getElementById("negative-factors-list");

  const errorHeadingEl = document.getElementById("error-heading");
  const errorDetailEl = document.getElementById("error-detail");

  const segGroup = document.getElementById("stress_level_group");
  const stressHiddenInput = document.getElementById("stress_level");

  let lastSubmittedPayload = null;

  // ---------------------------------------------------------
  // 2. VERIFIED HEALTH CHECK ON INITIALIZATION
  // Derives status strictly from actual /health response.
  // ---------------------------------------------------------
  async function checkApiHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`, { method: "GET" });
      if (!res.ok) {
        throw new Error(`Health check returned HTTP ${res.status}`);
      }
      const data = await res.json();
      if (data.status === "ok" && data.model_loaded && data.uncertainty_loaded) {
        apiStatusPill.className = "status-pill online";
        apiStatusText.textContent = `Connected: ${data.model_version || "Model"} (Ready)`;
      } else {
        apiStatusPill.className = "status-pill offline";
        apiStatusText.textContent = "Service Degradation (Model unready)";
      }
    } catch (err) {
      apiStatusPill.className = "status-pill offline";
      apiStatusText.textContent = "API Disconnected (Run uvicorn)";
    }
  }
  checkApiHealth();

  // ---------------------------------------------------------
  // 3. SEGMENTED STRESS LEVEL SELECTOR
  // ---------------------------------------------------------
  segGroup.querySelectorAll(".seg-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      segGroup.querySelectorAll(".seg-btn").forEach((b) => {
        b.classList.remove("active");
        b.setAttribute("aria-checked", "false");
      });
      btn.classList.add("active");
      btn.setAttribute("aria-checked", "true");
      stressHiddenInput.value = btn.dataset.value;
      clearFieldError(stressHiddenInput);
    });
  });

  function setStressValue(val) {
    stressHiddenInput.value = val;
    segGroup.querySelectorAll(".seg-btn").forEach((b) => {
      const isActive = b.dataset.value === val;
      b.classList.toggle("active", isActive);
      b.setAttribute("aria-checked", isActive ? "true" : "false");
    });
  }

  // ---------------------------------------------------------
  // 4. FIELD ERROR HELPERS
  // ---------------------------------------------------------
  function fieldWrapper(input) {
    return input ? input.closest(".field") : null;
  }

  function setFieldError(input, message) {
    const wrap = fieldWrapper(input);
    if (!wrap) return;
    wrap.classList.add("field-error");
    const msgEl = wrap.querySelector(".error-msg");
    if (msgEl) msgEl.textContent = message;
  }

  function clearFieldError(input) {
    const wrap = fieldWrapper(input);
    if (!wrap) return;
    wrap.classList.remove("field-error");
    const msgEl = wrap.querySelector(".error-msg");
    if (msgEl) msgEl.textContent = "";
  }

  function clearAllErrors() {
    form.querySelectorAll(".field").forEach((f) => f.classList.remove("field-error"));
    form.querySelectorAll(".error-msg").forEach((m) => (m.textContent = ""));
  }

  form.querySelectorAll("input, select").forEach((el) => {
    el.addEventListener("input", () => clearFieldError(el));
    el.addEventListener("change", () => clearFieldError(el));
  });

  // ---------------------------------------------------------
  // 5. CLIENT-SIDE VALIDATION
  // ---------------------------------------------------------
  function validate(payload) {
    const errors = [];

    const numericRules = [
      ["age", 10, 100, "Age must be between 10 and 100 years."],
      ["avg_daily_usage_hours", 0, 24, "Daily screen time must be between 0.0 and 24.0 hours."],
      ["daily_unlocks", 0, 1000, "Daily unlocks must be between 0 and 1000."],
      ["study_hours", 0, 24, "Study hours must be between 0.0 and 24.0 hours."],
      ["physical_activity_hours", 0, 24, "Physical activity must be between 0.0 and 24.0 hours."],
      ["sleep_hours_per_night", 0, 24, "Sleep duration must be between 0.0 and 24.0 hours."],
    ];

    numericRules.forEach(([id, min, max, msg]) => {
      const val = payload[id];
      const input = document.getElementById(id);
      if (val === "" || val === null || Number.isNaN(val)) {
        errors.push([input, "This field is required."]);
      } else if (val < min || val > max) {
        errors.push([input, msg]);
      }
    });

    ["gender", "academic_level", "country", "most_used_platform", "purpose_of_use"].forEach((id) => {
      const input = document.getElementById(id);
      if (!payload[id] || String(payload[id]).trim() === "") {
        errors.push([input, "Please select or enter an option."]);
      }
    });

    if (!payload.stress_level) {
      errors.push([stressHiddenInput, "Please select a stress level."]);
    }

    return errors;
  }

  // ---------------------------------------------------------
  // 6. COLLECT SURVEY PAYLOAD
  // Collects strictly what user entered into the form.
  // ---------------------------------------------------------
  function collectPayload() {
    const fd = new FormData(form);
    return {
      age: fd.get("age") === "" ? NaN : parseInt(fd.get("age"), 10),
      gender: fd.get("gender") || "",
      academic_level: fd.get("academic_level") || "",
      country: (fd.get("country") || "").trim(),
      avg_daily_usage_hours: fd.get("avg_daily_usage_hours") === "" ? NaN : parseFloat(fd.get("avg_daily_usage_hours")),
      most_used_platform: fd.get("most_used_platform") || "",
      daily_unlocks: fd.get("daily_unlocks") === "" ? NaN : parseInt(fd.get("daily_unlocks"), 10),
      purpose_of_use: fd.get("purpose_of_use") || "",
      study_hours: fd.get("study_hours") === "" ? NaN : parseFloat(fd.get("study_hours")),
      physical_activity_hours: fd.get("physical_activity_hours") === "" ? NaN : parseFloat(fd.get("physical_activity_hours")),
      sleep_hours_per_night: fd.get("sleep_hours_per_night") === "" ? NaN : parseFloat(fd.get("sleep_hours_per_night")),
      stress_level: fd.get("stress_level") || "",
      coverage: 0.90
    };
  }

  // ---------------------------------------------------------
  // 7. UI STATE SWITCHING
  // ---------------------------------------------------------
  function showState(name) {
    [stateIdle, stateLoading, stateResult, stateError].forEach((el) => {
      el.hidden = true;
    });
    const target = {
      idle: stateIdle,
      loading: stateLoading,
      result: stateResult,
      error: stateError
    }[name];
    if (target) target.hidden = false;
  }

  function setSubmitting(isSubmitting) {
    submitBtn.disabled = isSubmitting;
    submitBtn.classList.toggle("loading", isSubmitting);
    const label = submitBtn.querySelector(".btn-label");
    if (label) {
      label.textContent = isSubmitting ? "Estimating Score…" : "Predict Wellbeing Score";
    }
  }

  function clearResultDisplay() {
    scoreNumberEl.textContent = "—";
    boundLabelLowerEl.textContent = "Lower: —";
    boundLabelEstimateEl.textContent = "Estimate: —";
    boundLabelUpperEl.textContent = "Upper: —";
    metricIntervalRangeEl.textContent = "—";
    metricIntervalWidthEl.textContent = "—";
    metricModelNameEl.textContent = "—";
    metricUncertaintyMethodEl.textContent = "—";
    uncertaintyCoverageTagEl.textContent = "—";
    interpretationTextEl.textContent = "Model-estimated score based on the submitted survey inputs.";
    factorsWrapper.style.display = "none";
    positiveFactorsList.innerHTML = "";
    negativeFactorsList.innerHTML = "";
  }

  // ---------------------------------------------------------
  // 8. RENDER PREDICTION FROM ACTUAL API RESPONSE
  // Uses strictly model-provided values with zero hardcoded numbers
  // or client-side categorization.
  // ---------------------------------------------------------
  function renderResult(data) {
    // 1. Continuous point estimate from API
    const score = Number(data.estimated_wellbeing_score);
    scoreNumberEl.textContent = score.toFixed(2);

    // 2. Prediction interval from API
    if (data.prediction_interval) {
      const pi = data.prediction_interval;
      const lower = Number(pi.lower);
      const upper = Number(pi.upper);
      const width = Number(pi.width);
      const nominalCoverage = Number(pi.nominal_coverage);

      metricIntervalRangeEl.textContent = `${lower.toFixed(2)} – ${upper.toFixed(2)}`;
      metricIntervalWidthEl.textContent = width.toFixed(4);

      if (!Number.isNaN(nominalCoverage)) {
        uncertaintyCoverageTagEl.textContent = `${Math.round(nominalCoverage * 100)}% Nominal Coverage`;
      } else {
        uncertaintyCoverageTagEl.textContent = "Calibrated Coverage";
      }

      // Interval track positioning within domain [0.0, 10.0]
      const leftPercent = Math.max(0, Math.min(100, (lower / 10.0) * 100));
      const rightPercent = Math.max(0, Math.min(100, (upper / 10.0) * 100));
      const estimatePercent = Math.max(0, Math.min(100, (score / 10.0) * 100));

      intervalHighlightEl.style.left = `${leftPercent}%`;
      intervalHighlightEl.style.width = `${Math.max(2, rightPercent - leftPercent)}%`;
      intervalPointMarkerEl.style.left = `${estimatePercent}%`;

      boundLabelLowerEl.textContent = `Lower: ${lower.toFixed(2)}`;
      boundLabelEstimateEl.textContent = `Estimate: ${score.toFixed(2)}`;
      boundLabelUpperEl.textContent = `Upper: ${upper.toFixed(2)}`;
    } else {
      metricIntervalRangeEl.textContent = "Unavailable";
      metricIntervalWidthEl.textContent = "Unavailable";
      uncertaintyCoverageTagEl.textContent = "Unavailable";
    }

    // 3. Model metadata from API
    metricModelNameEl.textContent = data.model_version || "Model metadata unavailable";
    metricUncertaintyMethodEl.textContent = data.uncertainty_method || "Uncertainty metadata unavailable";

    // 4. Non-clinical neutral disclaimer from API
    interpretationTextEl.textContent = data.disclaimer || "Model-estimated score based on the submitted survey inputs.";

    // 5. Reset explanation factors view
    factorsWrapper.style.display = "none";
    explainBtn.disabled = false;
    explainBtnLabel.textContent = "Explain this prediction";
    explainSpinner.style.display = "none";

    showState("result");
  }

  // ---------------------------------------------------------
  // 9. DYNAMIC TREESHAP EXPLANATION FROM ACTUAL /explain RESPONSE
  // Displays real feature values, SHAP values, base value, and directions.
  // ---------------------------------------------------------
  explainBtn.addEventListener("click", async () => {
    if (!lastSubmittedPayload) return;

    explainBtn.disabled = true;
    explainBtnLabel.textContent = "Computing feature attributions…";
    explainSpinner.style.display = "inline-block";

    try {
      const res = await fetch(`${API_BASE}/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(lastSubmittedPayload)
      });

      if (!res.ok) {
        throw new Error(`Explanation request failed with HTTP ${res.status}`);
      }

      const expData = await res.json();

      positiveFactorsList.innerHTML = "";
      negativeFactorsList.innerHTML = "";

      const baseVal = Number(expData.base_value);
      const predScore = Number(expData.estimated_wellbeing_score);

      if (shapSummaryMetaEl) {
        shapSummaryMetaEl.textContent = `Estimated Score: ${predScore.toFixed(2)} | Expected Baseline Average: ${baseVal.toFixed(2)}`;
      }

      const pos = Array.isArray(expData.positive_contributors) ? expData.positive_contributors : [];
      const neg = Array.isArray(expData.negative_contributors) ? expData.negative_contributors : [];

      if (pos.length === 0) {
        positiveFactorsList.innerHTML = `<div class="factor-item"><span class="factor-name">None observed</span></div>`;
      } else {
        pos.forEach((item) => {
          const el = document.createElement("div");
          el.className = "factor-item";
          const featureName = item.feature.replace(/_/g, " ");
          const valDisplay = item.value !== undefined ? ` (${item.value})` : "";
          const shapVal = Number(item.shap_value);
          el.innerHTML = `
            <span class="factor-name" title="${featureName}${valDisplay}">${featureName}${valDisplay}</span>
            <span class="factor-val">+${shapVal.toFixed(3)}</span>
          `;
          positiveFactorsList.appendChild(el);
        });
      }

      if (neg.length === 0) {
        negativeFactorsList.innerHTML = `<div class="factor-item"><span class="factor-name">None observed</span></div>`;
      } else {
        neg.forEach((item) => {
          const el = document.createElement("div");
          el.className = "factor-item";
          const featureName = item.feature.replace(/_/g, " ");
          const valDisplay = item.value !== undefined ? ` (${item.value})` : "";
          const shapVal = Number(item.shap_value);
          el.innerHTML = `
            <span class="factor-name" title="${featureName}${valDisplay}">${featureName}${valDisplay}</span>
            <span class="factor-val">${shapVal.toFixed(3)}</span>
          `;
          negativeFactorsList.appendChild(el);
        });
      }

      factorsWrapper.style.display = "block";
      explainBtnLabel.textContent = "Explanations Loaded";
    } catch (err) {
      explainBtnLabel.textContent = "Explanation Failed (Retry)";
      factorsWrapper.style.display = "block";
      positiveFactorsList.innerHTML = `<div class="factor-item" style="color:var(--accent-neg);">${err.message || "Failed to load TreeSHAP values."}</div>`;
      negativeFactorsList.innerHTML = "";
    } finally {
      explainSpinner.style.display = "none";
      explainBtn.disabled = false;
    }
  });

  // ---------------------------------------------------------
  // 10. SUBMIT HANDLER & API INTEGRATION
  // ---------------------------------------------------------
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearAllErrors();

    const payload = collectPayload();
    const errors = validate(payload);

    if (errors.length > 0) {
      errors.forEach(([input, msg]) => setFieldError(input, msg));
      errors[0][0]?.focus?.();
      return;
    }

    lastSubmittedPayload = payload;
    setSubmitting(true);
    showState("loading");

    try {
      const res = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.status === 422) {
        clearResultDisplay();
        const body = await res.json().catch(() => null);
        let detailMsg = "The server rejected one or more fields. Please review highlighted inputs.";
        if (body && Array.isArray(body.detail)) {
          body.detail.forEach((err) => {
            const field = Array.isArray(err.loc) ? err.loc[err.loc.length - 1] : (err.field || null);
            const target = field === "stress_level" ? stressHiddenInput : document.getElementById(field);
            if (target) setFieldError(target, err.msg || err.message || "Invalid input.");
          });
        }
        errorHeadingEl.textContent = "Input Validation Error";
        errorDetailEl.textContent = detailMsg;
        showState("error");
        return;
      }

      if (!res.ok) {
        clearResultDisplay();
        let msg = `The server responded with HTTP ${res.status}.`;
        const body = await res.json().catch(() => null);
        if (body && body.detail) msg = body.detail;
        errorHeadingEl.textContent = "Prediction Service Error";
        errorDetailEl.textContent = msg;
        showState("error");
        return;
      }

      const data = await res.json();
      if (typeof data.estimated_wellbeing_score !== "number") {
        clearResultDisplay();
        throw new Error("API response is missing estimated_wellbeing_score.");
      }

      renderResult(data);
    } catch (err) {
      clearResultDisplay();
      errorHeadingEl.textContent = "Cannot Connect to Model API";
      errorDetailEl.textContent = `Could not reach ${API_BASE}. Ensure the FastAPI server is running locally (e.g. 'python main.py') and try again.`;
      showState("error");
    } finally {
      setSubmitting(false);
    }
  });

  // ---------------------------------------------------------
  // 11. RESET HANDLERS
  // ---------------------------------------------------------
  formResetBtn.addEventListener("click", () => {
    form.reset();
    clearAllErrors();
    setStressValue("");
    clearResultDisplay();
    showState("idle");
  });

  resetResultBtn.addEventListener("click", () => {
    clearResultDisplay();
    showState("idle");
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  errorRetryBtn.addEventListener("click", () => {
    showState("idle");
  });

})();
