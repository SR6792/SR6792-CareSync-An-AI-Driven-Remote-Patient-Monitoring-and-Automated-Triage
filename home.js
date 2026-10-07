document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("predictionForm");
    const submitBtn = document.querySelector(".submit-btn");
    const resultSummary = document.querySelector(".result-summary");
    const riskBadge = document.getElementById("riskBadge");
    const riskScore = document.getElementById("riskScore");
    const triageRecommendation = document.getElementById("triageRecommendation");
    const btnPresetLow = document.getElementById("btnPresetLow");
    const btnPresetHigh = document.getElementById("btnPresetHigh");

    let gaugeInstance = null;

    // Initialize JustGage Gauge
    function initGauge(val = 0) {
        document.getElementById("gauge").innerHTML = "";
        gaugeInstance = new JustGage({
            id: "gauge",
            value: val,
            min: 0,
            max: 100,
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

    // Preset data handlers for real Kaggle Stroke Dataset
    const lowRiskProfile = {
        age: 35, gender: "Female", hypertension: "0", heart_disease: "0",
        ever_married: "No", work_type: "Private", Residence_type: "Urban",
        avg_glucose_level: 85.2, bmi: 22.5, smoking_status: "never smoked"
    };

    const highRiskProfile = {
        age: 79, gender: "Female", hypertension: "1", heart_disease: "0",
        ever_married: "Yes", work_type: "Self-employed", Residence_type: "Rural",
        avg_glucose_level: 174.12, bmi: 24.0, smoking_status: "never smoked"
    };

    function populateForm(profile) {
        Object.keys(profile).forEach(key => {
            const field = document.getElementById(key);
            if (field) {
                field.value = profile[key];
            }
        });
    }

    btnPresetLow.addEventListener("click", () => {
        populateForm(lowRiskProfile);
    });

    btnPresetHigh.addEventListener("click", () => {
        populateForm(highRiskProfile);
    });

    // Form Submission
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const payload = {
            age: parseFloat(document.getElementById("age").value),
            gender: document.getElementById("gender").value,
            hypertension: parseInt(document.getElementById("hypertension").value),
            heart_disease: parseInt(document.getElementById("heart_disease").value),
            ever_married: document.getElementById("ever_married").value,
            work_type: document.getElementById("work_type").value,
            Residence_type: document.getElementById("Residence_type").value,
            avg_glucose_level: parseFloat(document.getElementById("avg_glucose_level").value),
            bmi: parseFloat(document.getElementById("bmi").value),
            smoking_status: document.getElementById("smoking_status").value
        };

        submitBtn.disabled = true;
        submitBtn.innerText = "Analyzing Stroke Risk...";

        try {
            const response = await fetch("/api/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                alert(data.error || data.msg || "Prediction failed. Please check inputs.");
                return;
            }

            const riskVal = data.stroke_risk_percentage ?? 0;
            // Qualitative risk-group label: 50% cutoff
            const riskLevel = data.risk_level || (riskVal >= 50.0 ? "High risk" : "Low risk");
            const probabilityLabel = data.probability_label || `${riskVal}% stroke risk`;
            const recommendation = data.recommendation || "Patient risk evaluation complete.";

            // Update Gauge
            initGauge(riskVal);

            // Update UI elements (both raw probability and qualitative risk-group label)
            riskScore.innerText = probabilityLabel;
            resultSummary.innerText = `Statistical probability of stroke risk calculated at ${riskVal}%.`;
            triageRecommendation.innerText = recommendation;

            // Update Badge class based on 50% threshold
            riskBadge.className = "risk-badge";
            if (riskVal >= 50.0) {
                riskBadge.classList.add("high");
                riskBadge.innerText = "🚨 High risk";
            } else {
                riskBadge.classList.add("low");
                riskBadge.innerText = "✅ Low risk";
            }

        } catch (err) {
            console.error("Prediction Error:", err);
            alert("Error connecting to server for prediction: " + err.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = "Analyze Stroke Risk";
        }
    });
});

