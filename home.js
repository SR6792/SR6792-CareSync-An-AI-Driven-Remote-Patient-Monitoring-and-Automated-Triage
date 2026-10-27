document.addEventListener("DOMContentLoaded", () => {
    const form               = document.getElementById("predictionForm");
    const submitBtn          = document.querySelector(".submit-btn");
    const resultSummary      = document.querySelector(".result-summary");
    const supplementalSummary= document.getElementById("supplementalSummary");
    const riskBadge          = document.getElementById("riskBadge");
    const riskScore          = document.getElementById("riskScore");
    const triageRecommendation = document.getElementById("triageRecommendation");
    const btnPresetLow       = document.getElementById("btnPresetLow");
    const btnPresetHigh      = document.getElementById("btnPresetHigh");
    const modelSelect        = document.getElementById("modelSelect");
    const modelMetricsPill   = document.getElementById("modelMetricsPill");
    const modelUsedLabel     = document.getElementById("modelUsedLabel");
    const comparisonPanel    = document.getElementById("comparisonPanel");
    const comparisonBody     = document.getElementById("comparisonBody");

    // ─── Blood pressure pair validation ────────────────────────
    const systolicBp  = document.getElementById("systolic_bp");
    const diastolicBp = document.getElementById("diastolic_bp");
    [systolicBp, diastolicBp].forEach(field => {
        field.addEventListener("input", () => {
            systolicBp.setCustomValidity("");
            diastolicBp.setCustomValidity("");
            supplementalSummary.hidden = true;
        });
    });
    document.getElementById("total_cholesterol").addEventListener("input", () => {
        supplementalSummary.hidden = true;
    });

    // ─── Gauge setup ───────────────────────────────────────────
    let gaugeInstance = null;
    function initGauge(val = 0) {
        document.getElementById("gauge").innerHTML = "";
        gaugeInstance = new JustGage({
            id: "gauge",
            value: val,
            min: 0, max: 100,
            title: "Stroke Risk (%)",
            label: "Probability %",
            gaugeWidthScale: 0.6,
            counter: true,
            relativeGaugeSize: true,
            valueFontColor: "#f8fafc",
            titleFontColor: "#94a3b8",
            labelFontColor: "#94a3b8",
            levelColors: ["#10b981", "#fbbf24", "#ef4444"],
            levelColorsGradient: false
        });
    }
    initGauge(0);

    // ─── Model metrics from API ─────────────────────────────────
    let allModelMetrics = {};

    async function fetchModelMetrics() {
        try {
            const res = await fetch("/api/models");
            const data = await res.json();
            allModelMetrics = data.models || {};
            updateMetricsPill(modelSelect.value);
            populateComparisonTable();
        } catch (e) {
            modelMetricsPill.textContent = "Metrics unavailable (run train.py)";
        }
    }

    function updateMetricsPill(key) {
        const m = allModelMetrics[key];
        if (m && m.metrics) {
            const mt = m.metrics;
            modelMetricsPill.textContent =
                `Recall: ${mt.recall}% | AUC: ${mt.roc_auc}% | Acc: ${mt.accuracy}% | Train: ${mt.train_time_s}s`;
        } else {
            modelMetricsPill.textContent = "Run train.py to see metrics";
        }
    }

    function populateComparisonTable() {
        comparisonBody.innerHTML = "";
        const keyOrder = ['lr', 'rf', 'xgb'];
        let hasData = false;

        keyOrder.forEach(key => {
            const m = allModelMetrics[key];
            if (!m) return;
            if (!m.loaded) return;
            hasData = true;
            const mt = m.metrics || {};
            const row = document.createElement("tr");
            if (key === modelSelect.value) row.classList.add("active-model-row");
            row.innerHTML = `
                <td><strong>${m.name}</strong></td>
                <td>${mt.accuracy ?? '—'}%</td>
                <td class="${(mt.recall ?? 0) >= 70 ? 'good-recall' : 'poor-recall'}">${mt.recall ?? '—'}%</td>
                <td>${mt.roc_auc ?? '—'}%</td>
                <td>${mt.train_time_s ?? '—'}s</td>
            `;
            comparisonBody.appendChild(row);
        });

        comparisonPanel.hidden = !hasData;
    }

    modelSelect.addEventListener("change", () => {
        updateMetricsPill(modelSelect.value);
        // Update active row highlight
        document.querySelectorAll("#comparisonBody tr").forEach((r, i) => {
            r.classList.remove("active-model-row");
        });
        populateComparisonTable();
    });

    fetchModelMetrics();

    // ─── Preset profiles ────────────────────────────────────────
    const highRiskProfile = {
        age: 78, gender: "Male", hypertension: "1", heart_disease: "1",
        ever_married: "Yes", work_type: "Self-employed", Residence_type: "Rural",
        avg_glucose_level: 178, bmi: 32.0, smoking_status: "smokes",
        total_cholesterol: 250, systolic_bp: 155, diastolic_bp: 98
    };

    const lowRiskProfile = {
        age: 25, gender: "Female", hypertension: "0", heart_disease: "0",
        ever_married: "No", work_type: "Private", Residence_type: "Urban",
        avg_glucose_level: 85, bmi: 22.0, smoking_status: "never smoked",
        total_cholesterol: 160, systolic_bp: 115, diastolic_bp: 75
    };

    function populateForm(profile) {
        Object.keys(profile).forEach(key => {
            const field = document.getElementById(key);
            if (field) field.value = profile[key];
        });
    }

    btnPresetLow.addEventListener("click",  () => populateForm(lowRiskProfile));
    btnPresetHigh.addEventListener("click", () => populateForm(highRiskProfile));

    // ─── Form submission ─────────────────────────────────────────
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        // BP pair validation
        systolicBp.setCustomValidity("");
        diastolicBp.setCustomValidity("");
        if (Boolean(systolicBp.value) !== Boolean(diastolicBp.value)) {
            const incompleteField = systolicBp.value ? diastolicBp : systolicBp;
            incompleteField.setCustomValidity("Enter both blood pressure values, or leave both blank.");
            incompleteField.reportValidity();
            return;
        }

        const selectedModel = modelSelect.value;

        const payload = {
            model: selectedModel,
            age:               parseFloat(document.getElementById("age").value),
            gender:            document.getElementById("gender").value,
            hypertension:      parseInt(document.getElementById("hypertension").value),
            heart_disease:     parseInt(document.getElementById("heart_disease").value),
            ever_married:      document.getElementById("ever_married").value,
            work_type:         document.getElementById("work_type").value,
            Residence_type:    document.getElementById("Residence_type").value,
            avg_glucose_level: parseFloat(document.getElementById("avg_glucose_level").value),
            bmi:               parseFloat(document.getElementById("bmi").value),
            smoking_status:    document.getElementById("smoking_status").value,
        };

        submitBtn.disabled = true;
        submitBtn.innerText = "Analyzing Stroke Risk…";

        try {
            const response = await fetch("/api/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                alert(data.error || "Prediction failed. Please check inputs.");
                return;
            }

            const riskVal        = data.stroke_risk_percentage ?? 0;
            const riskLevel      = data.risk_level || (riskVal >= 50.0 ? "High risk" : "Low risk");
            const probabilityLabel = data.probability_label || `${riskVal}% stroke risk`;
            const recommendation = data.recommendation || "Patient risk evaluation complete.";
            const modelUsed      = data.model_used || "AI Model";

            // Update gauge
            initGauge(riskVal);

            // Update labels
            riskScore.innerText       = probabilityLabel;
            resultSummary.innerText   = `${modelUsed} calculated stroke risk at ${riskVal}%.`;
            triageRecommendation.innerText = recommendation;
            modelUsedLabel.innerText  = `Powered by: ${modelUsed}`;

            // Supplemental details
            const supplementalDetails = [];
            const cholesterol = document.getElementById("total_cholesterol").value;
            if (cholesterol) supplementalDetails.push(`Total cholesterol: ${cholesterol} mg/dL`);
            if (systolicBp.value && diastolicBp.value)
                supplementalDetails.push(`Blood pressure: ${systolicBp.value}/${diastolicBp.value} mmHg`);
            supplementalSummary.innerText = supplementalDetails.length
                ? `Additional details: ${supplementalDetails.join(" · ")}`
                : "";
            supplementalSummary.hidden = supplementalDetails.length === 0;

            // Update risk badge
            riskBadge.className = "risk-badge";
            if (riskVal >= 50.0) {
                riskBadge.classList.add("high");
                riskBadge.innerText = "🚨 High Risk";
            } else {
                riskBadge.classList.add("low");
                riskBadge.innerText = "✅ Low Risk";
            }

        } catch (err) {
            console.error("Prediction Error:", err);
            alert("Error connecting to server: " + err.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = "Analyze Stroke Risk";
        }
    });
});
