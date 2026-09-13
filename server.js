//first insert all packages
const cors = require("cors");
const mongoose = require("mongoose");
const express = require("express");
const path = require("path");
const app = express();
const PORT = process.env.PORT || 2000;
const { spawn } = require('child_process');

app.use(cors());
app.use(express.json());

// Serve static frontend files from current directory
app.use(express.static(__dirname)); 

// Explicitly send index.html for root path
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "index.html"));
});

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
//ML PART
app.post('/api/predict', (req, res) => {
  const { age, bmi } = req.body;

  if (age === undefined || bmi === undefined) {
    return res.status(400).json({ error: "Please provide both age and bmi." });
  }

  // Execute predict.py with age and bmi as CLI arguments
  const pythonProcess = spawn('python', ['predict.py', age, bmi]);

  let resultData = '';
  let errorData = '';

  pythonProcess.stdout.on('data', (data) => {
    resultData += data.toString();
  });

  pythonProcess.stderr.on('data', (data) => {
    errorData += data.toString();
  });

  pythonProcess.on('close', (code) => {
    if (code !== 0) {
      console.error(`Python error: ${errorData}`);
      return res.status(500).json({ error: "Prediction process failed" });
    }

    try {
      const response = JSON.parse(resultData);
      return res.status(200).json(response);
    } catch (err) {
      return res.status(500).json({ error: "Failed to parse prediction output" });
    }
  });
});
app.listen(PORT,() => {
    console.log(`Server is listening on http://localhost:${PORT}`);
});

connectToMongo();
