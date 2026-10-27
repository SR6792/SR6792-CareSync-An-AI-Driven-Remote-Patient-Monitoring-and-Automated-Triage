//first insert all packages
const cors = require("cors");
const mongoose = require("mongoose");
const express = require("express");
const fs = require("fs");
const path = require("path");
const app = express();
const PORT = process.env.PORT || 2000;
const { spawn } = require('child_process');

app.use(cors());
app.use(express.json());

let predictionWorker = null;
let predictionOutput = '';
const predictionRequests = [];

function rejectPendingPredictions(error) {
    while (predictionRequests.length > 0) {
        predictionRequests.shift().reject(error);
    }
}

function startPredictionWorker() {
    if (predictionWorker) {
        return;
    }

    const worker = spawn(process.env.PYTHON_EXECUTABLE || 'python', [
        path.join(__dirname, 'predict.py'),
        '--worker'
    ], { cwd: __dirname });
    predictionWorker = worker;

    worker.stdout.on('data', (chunk) => {
        predictionOutput += chunk.toString();
        let newlineIndex = predictionOutput.indexOf('\n');

        while (newlineIndex !== -1) {
            const line = predictionOutput.slice(0, newlineIndex);
            predictionOutput = predictionOutput.slice(newlineIndex + 1);
            newlineIndex = predictionOutput.indexOf('\n');

            const request = predictionRequests.shift();
            if (!request) {
                console.error('Received an unexpected prediction response.');
                continue;
            }

            try {
                const result = JSON.parse(line);
                if (result.error) {
                    request.reject(new Error(result.error));
                } else {
                    request.resolve(result);
                }
            } catch (error) {
                request.reject(new Error(`Invalid prediction response: ${error.message}`));
            }
        }
    });

    worker.stderr.on('data', (chunk) => {
        console.error(`Prediction worker: ${chunk.toString().trim()}`);
    });

    worker.on('error', (error) => {
        console.error('Could not start prediction worker:', error);
        if (predictionWorker === worker) {
            predictionWorker = null;
            predictionOutput = '';
        }
        rejectPendingPredictions(error);
    });

    worker.on('close', (code, signal) => {
        if (predictionWorker === worker) {
            predictionWorker = null;
            predictionOutput = '';
        }
        if (code !== 0) {
            rejectPendingPredictions(new Error(`Prediction worker exited with code ${code ?? 'unknown'}${signal ? ` (${signal})` : ''}`));
        } else {
            rejectPendingPredictions(new Error('Prediction worker stopped unexpectedly'));
        }
    });
}

function requestPrediction(payload) {
    startPredictionWorker();

    return new Promise((resolve, reject) => {
        predictionRequests.push({ resolve, reject });
        try {
            predictionWorker.stdin.write(`${JSON.stringify(payload)}\n`);
        } catch (error) {
            predictionRequests.pop();
            reject(error);
        }
    });
}

// Launch the modern login screen by default and keep register screen available separately.
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "login.html"));
});

app.get("/login", (req, res) => {
    res.sendFile(path.join(__dirname, "login.html"));
});

app.get("/register", (req, res) => {
    res.sendFile(path.join(__dirname, "index.html"));
});

// Serve static frontend files from current directory
app.use(express.static(__dirname)); 

//make an async function for db
const connectToMongo = async () => {
    try {
        await mongoose.connect("mongodb+srv://sooraj2050in_db_user:yjuUtM8L9A0pIJBc@cluster0.xkhqlbt.mongodb.net/?retryWrites=true&w=majority");
        console.log("We are Connected");
    } catch (error) {
        console.error("MongoDB connection failed:", error.message);
    }
};

//blueprint of db
const login_Details = mongoose.Schema({
    email1:{
        type: String,
        required: true,
        unique: true
    },
    password1:{
        type: String,
        required: true
    }
});

const login = mongoose.model('login', login_Details);


//model is used to Create a database table object based on this structure"
app.post("/register", async (req, res) => {
    try {
        const { email1, password1 } = req.body;
        const existingUser = await login.findOne({ email1 });

        if (existingUser) {
            return res.status(400).json({ msg: "Already Registered" });
        }

        await login.create({ email1, password1 });
        return res.status(200).json({ message: "Registration done" });
    } catch (e) {
        console.error("Registration error:", e);
        return res.status(500).json({ message: "Error" });
    }
});

//for login
app.post("/login",async(req,res)=>{
  try{
        const { email2,pass1 } = req.body;
        const existingUser = await login.findOne({ email1:email2,password1:pass1 });

        if (!existingUser) {
            return res.status(400).json({ message: " User Doesnt Exist" });
        }
        else{
          return res.status(200).json({msg:"Login Completed"})
        }
  }
  catch(e){
    console.log("Login Error");
    res.status(500).json({msg:"Error"});

  }
})
app.post('/api/predict', async (req, res) => {
    try {
        const result = await requestPrediction(req.body || {});
        return res.status(200).json(result);
    } catch (error) {
        console.error('Prediction error:', error);
        return res.status(500).json({
            error: 'Prediction process failed',
            details: error.message
        });
    }
});

app.get('/api/models', (req, res) => {
    try {
        const comparisonPath = path.join(__dirname, 'model_comparison.json');
        const metrics = fs.existsSync(comparisonPath)
            ? JSON.parse(fs.readFileSync(comparisonPath, 'utf8'))
            : {};
        const models = {};

        for (const [key, info] of Object.entries(metrics)) {
            models[key] = {
                name: info.name,
                loaded: Boolean(info.pkl && fs.existsSync(path.join(__dirname, info.pkl))),
                metrics: info
            };
        }

        return res.status(200).json({ models, default: 'lr' });
    } catch (error) {
        console.error('Could not load model information:', error);
        return res.status(500).json({ error: 'Could not load model information.' });
    }
});

startPredictionWorker();

app.listen(PORT,() => {
    console.log(`Server is listening on http://localhost:${PORT}`);
});

connectToMongo();
