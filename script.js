(() => {
  "use strict";

  // ---------------------------------------------------------
  // 1. DYNAMIC API BASE RESOLUTION
  // Strictly resolves locally or via current origin.
  // NEVER references deprecated third-party deployments.
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
  const demoSampleBtn = document.getElementById("demo-sample-btn");
  const resetResultBtn = document.getElementById("reset-result-btn");
  const errorRetryBtn = document.getElementById("error-retry-btn");

  const stateIdle = document.getElementById("state-idle");
  const stateLoading = document.getElementById("state-loading");
  const stateResult = document.getElementById("state-result");
  const stateError = document.getElementById("state-error");

  const apiStatusPill = document.getElementById("api-status-pill");
  const apiStatusText = document.getElementById("api-status-text");

  const scoreNumberEl = document.getElementById("score-number");
  const scoreStatusBadgeEl = document.getElementById("score-status-badge");
  const interpretationTextEl = document.getElementById("interpretation-text");

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
  const positiveFactorsList = document.getElementById("positive-factors-list");
  const negativeFactorsList = document.getElementById("negative-factors-list");

  const errorHeadingEl = document.getElementById("error-heading");
  const errorDetailEl = document.getElementById("error-detail");

  const segGroup = document.getElementById("stress_level_group");
  const stressHiddenInput = document.getElementById("stress_level");

  let lastSubmittedPayload = null;

  // ---------------------------------------------------------
  // 2. HEALTH CHECK ON INITIALIZATION
  // ---------------------------------------------------------
  async function checkApiHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`, { method: "GET" });
      if (res.ok) {
        const data = await res.json();
        apiStatusPill.classList.remove("offline");
        apiStatusPill.classList.add("online");
        apiStatusText.textContent = `Model Ready (${data.model_version || "Phase 5"})`;
      } else {
        throw new Error(`HTTP ${res.status}`);
      }
    } catch (err) {
      apiStatusPill.classList.remove("online");
      apiStatusPill.classList.add("offline");
      apiStatusText.textContent = "API Offline (Run uvicorn)";
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
  // 4. LOAD BENCHMARK DEMO SAMPLE
  // ---------------------------------------------------------
  demoSampleBtn.addEventListener("click", () => {
    clearAllErrors();
    document.getElementById("age").value = "21";
    document.getElementById("gender").value = "Female";
    document.getElementById("academic_level").value = "Undergraduate";
    document.getElementById("country").value = "India";
    document.getElementById("avg_daily_usage_hours").value = "4.5";
    document.getElementById("most_used_platform").value = "Instagram";
    document.getElementById("daily_unlocks").value = "140";
    document.getElementById("purpose_of_use").value = "Education";
    document.getElementById("study_hours").value = "3.0";
    document.getElementById("physical_activity_hours").value = "1.5";
    document.getElementById("sleep_hours_per_night").value = "7.0";
    setStressValue("Medium");

    // Flash button feedback
    demoSampleBtn.style.transform = "scale(0.96)";
    setTimeout(() => { demoSampleBtn.style.transform = ""; }, 150);
  });

  // ---------------------------------------------------------
  // 5. FIELD ERROR HELPERS
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

  // Clear error on input/change
  form.querySelectorAll("input, select").forEach((el) => {
    el.addEventListener("input", () => clearFieldError(el));
    el.addEventListener("change", () => clearFieldError(el));
  });

  // ---------------------------------------------------------
  // 6. CLIENT-SIDE VALIDATION
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
  // 7. PAYLOAD COLLECTION
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
  // 8. UI STATE SWITCHING
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
  }

  // ---------------------------------------------------------
  // 9. RESULT RENDERING & VISUAL UNCERTAINTY
  // ---------------------------------------------------------
  function renderResult(data) {
    const score = (typeof data.estimated_wellbeing_score === "number")
      ? data.estimated_wellbeing_score
      : data.predicted_mental_health_score;

    scoreNumberEl.textContent = score.toFixed(2);

    // Score status badge & non-clinical interpretation
    if (score < 4.0) {
      scoreStatusBadgeEl.textContent = "Lower Score (Elevated Daily Strain)";
      scoreStatusBadgeEl.style.background = "rgba(200, 75, 70, 0.25)";
      scoreStatusBadgeEl.style.borderColor = "rgba(200, 75, 70, 0.45)";
      interpretationTextEl.textContent = `Model-estimated score of ${score.toFixed(2)} / 10. In this dataset, responses reflecting elevated perceived stress, shorter sleep durations, or high daily screen time associate with lower overall wellbeing scores. Note: This interpretation reflects statistical training patterns and is not a clinical assessment.`;
    } else if (score < 7.0) {
      scoreStatusBadgeEl.textContent = "Moderate Score (Balanced Baseline)";
      scoreStatusBadgeEl.style.background = "rgba(255, 255, 255, 0.18)";
      scoreStatusBadgeEl.style.borderColor = "rgba(255, 255, 255, 0.3)";
      interpretationTextEl.textContent = `Model-estimated score of ${score.toFixed(2)} / 10. The reported inputs indicate a moderate equilibrium between academic commitments and daily restorative habits. Note: This interpretation reflects statistical training patterns and is not a clinical assessment.`;
    } else {
      scoreStatusBadgeEl.textContent = "Higher Score (Resilient Habits)";
      scoreStatusBadgeEl.style.background = "rgba(46, 125, 99, 0.3)";
      scoreStatusBadgeEl.style.borderColor = "rgba(46, 125, 99, 0.5)";
      interpretationTextEl.textContent = `Model-estimated score of ${score.toFixed(2)} / 10. The reported habits reflect supportive sleep duration, regular physical activity, and moderate digital media consumption. Note: This interpretation reflects statistical training patterns and is not a clinical assessment.`;
    }

    // Uncertainty interval visualization
    if (data.prediction_interval) {
      const pi = data.prediction_interval;
      const lower = Math.max(0.0, pi.lower);
      const upper = Math.min(10.0, pi.upper);
      const width = pi.width;

      metricIntervalRangeEl.textContent = `${lower.toFixed(2)} – ${upper.toFixed(2)}`;
      metricIntervalWidthEl.textContent = width.toFixed(4);

      // Track positioning on 0..10 domain
      const leftPercent = Math.max(0, Math.min(100, (lower / 10.0) * 100));
      const rightPercent = Math.max(0, Math.min(100, (upper / 10.0) * 100));
      const estimatePercent = Math.max(0, Math.min(100, (score / 10.0) * 100));

      intervalHighlightEl.style.left = `${leftPercent}%`;
      intervalHighlightEl.style.width = `${Math.max(2, rightPercent - leftPercent)}%`;
      intervalPointMarkerEl.style.left = `${estimatePercent}%`;

      boundLabelLowerEl.textContent = `LB: ${lower.toFixed(2)}`;
      boundLabelEstimateEl.textContent = `Est: ${score.toFixed(2)}`;
      boundLabelUpperEl.textContent = `UB: ${upper.toFixed(2)}`;
    }

    metricModelNameEl.textContent = data.model_version ? "Phase 5 Extra Trees" : "Phase 5 Extra Trees";
    metricUncertaintyMethodEl.textContent = "5-Fold Cross-Conformal";

    // Reset explain section
    factorsWrapper.style.display = "none";
    explainBtn.disabled = false;
    explainBtnLabel.textContent = "Explain this prediction";
    explainSpinner.style.display = "none";

    showState("result");
  }

  // ---------------------------------------------------------
  // 10. TREESHAP EXPLANATION HANDLER
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
        throw new Error(`Explanation failed with status ${res.status}`);
      }

      const expData = await res.json();

      positiveFactorsList.innerHTML = "";
      negativeFactorsList.innerHTML = "";

      const pos = expData.positive_contributors || [];
      const neg = expData.negative_contributors || [];

      if (pos.length === 0) {
        positiveFactorsList.innerHTML = `<div class="factor-item"><span class="factor-name">None observed</span></div>`;
      } else {
        pos.slice(0, 5).forEach((item) => {
          const el = document.createElement("div");
          el.className = "factor-item";
          const featureName = item.feature.replace(/_/g, " ");
          el.innerHTML = `
            <span class="factor-name" title="${featureName}">${featureName}</span>
            <span class="factor-val">+${item.shap_value.toFixed(2)}</span>
          `;
          positiveFactorsList.appendChild(el);
        });
      }

      if (neg.length === 0) {
        negativeFactorsList.innerHTML = `<div class="factor-item"><span class="factor-name">None observed</span></div>`;
      } else {
        neg.slice(0, 5).forEach((item) => {
          const el = document.createElement("div");
          el.className = "factor-item";
          const featureName = item.feature.replace(/_/g, " ");
          el.innerHTML = `
            <span class="factor-name" title="${featureName}">${featureName}</span>
            <span class="factor-val">${item.shap_value.toFixed(2)}</span>
          `;
          negativeFactorsList.appendChild(el);
        });
      }

      factorsWrapper.style.display = "block";
      explainBtnLabel.textContent = "Explanations Loaded";
    } catch (err) {
      explainBtnLabel.textContent = "Explanation Failed (Retry)";
      factorsWrapper.style.display = "block";
      positiveFactorsList.innerHTML = `<div class="factor-item" style="color:var(--accent-neg);">Failed to load TreeSHAP values.</div>`;
      negativeFactorsList.innerHTML = "";
    } finally {
      explainSpinner.style.display = "none";
      explainBtn.disabled = false;
    }
  });

  // ---------------------------------------------------------
  // 11. FORM SUBMIT & SERVER INTEGRATION
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
        let msg = `The server responded with HTTP ${res.status}.`;
        const body = await res.json().catch(() => null);
        if (body && body.detail) msg = body.detail;
        errorHeadingEl.textContent = "Prediction Service Error";
        errorDetailEl.textContent = msg;
        showState("error");
        return;
      }

      const data = await res.json();
      if (typeof data.estimated_wellbeing_score !== "number" && typeof data.predicted_mental_health_score !== "number") {
        throw new Error("Malformed prediction response from API.");
      }

      renderResult(data);
    } catch (err) {
      errorHeadingEl.textContent = "Cannot Connect to Model API";
      errorDetailEl.textContent = `Could not reach ${API_BASE}. Ensure the FastAPI server is running locally (e.g. 'python main.py' or 'uvicorn main:app --port 8000') and try again.`;
      showState("error");
    } finally {
      setSubmitting(false);
    }
  });

  // ---------------------------------------------------------
  // 12. RESET HANDLERS
  // ---------------------------------------------------------
  formResetBtn.addEventListener("click", () => {
    form.reset();
    clearAllErrors();
    setStressValue("");
    showState("idle");
  });

  resetResultBtn.addEventListener("click", () => {
    showState("idle");
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  errorRetryBtn.addEventListener("click", () => {
    showState("idle");
  });

})();
