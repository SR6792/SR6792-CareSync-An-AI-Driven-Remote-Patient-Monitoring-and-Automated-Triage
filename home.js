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

    // Preset data handlers
    const lowRiskProfile = {
        age: 67, sex: "1", cp: "0", trtbps: 160, chol: 286, fbs: "0",
        restecg: "0", thalachh: 108, exng: "1", oldpeak: 1.5, slp: "1", caa: "3", thall: "2"
    };

    const highRiskProfile = {
        age: 63, sex: "1", cp: "3", trtbps: 145, chol: 233, fbs: "1",
        restecg: "0", thalachh: 150, exng: "0", oldpeak: 2.3, slp: "0", caa: "0", thall: "1"
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
            sex: parseFloat(document.getElementById("sex").value),
            cp: parseFloat(document.getElementById("cp").value),
            trtbps: parseFloat(document.getElementById("trtbps").value),
            chol: parseFloat(document.getElementById("chol").value),
            fbs: parseFloat(document.getElementById("fbs").value),
            restecg: parseFloat(document.getElementById("restecg").value),
            thalachh: parseFloat(document.getElementById("thalachh").value),
            exng: parseFloat(document.getElementById("exng").value),
            oldpeak: parseFloat(document.getElementById("oldpeak").value),
            slp: parseFloat(document.getElementById("slp").value),
            caa: parseFloat(document.getElementById("caa").value),
            thall: parseFloat(document.getElementById("thall").value)
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
