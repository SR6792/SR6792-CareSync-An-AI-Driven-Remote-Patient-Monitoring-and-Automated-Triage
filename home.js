const btn1 = document.querySelector(".btn1");
const age = document.querySelector(".age");
const bmi = document.querySelector(".bmi");
const result1  = document.querySelector('.p1');
const graph = document.querySelector(".bar");
btn1.addEventListener('click',async()=>{
    const inp1 = age.value.trim();
    const inp2 = bmi.value.trim();
    graph.innerText="";
    if(!inp1||!inp2){
        alert("Enter both data");
        return ; 
    }
    btn1.disabled = true;
    btn1.innerText = 'Calculating'
    try{
        const resp = await fetch('/api/predict',{
            method:'POST',
            headers:{
                'Content-Type':'application/json'
            },
            body:JSON.stringify({age:inp1,bmi:inp2})
        });
        const data = await resp.json();
        if(!resp.ok){
            alert(data.msg||"Prediction Failed");
            return ;
        }
        // Add an alert or update a DOM element here:
        result1.innerText = `There is ${data.stroke_risk_percentage}% chance of stoke`;
        // (Conceptual example)
        var g = new JustGage({
        id: "gauge", // ID of your container
        value: data.stroke_risk_percentage,   // Your calculated value
        min: 0,
        max: 100,
        title: "Severity Gauge"
        });
        age.value = "";
        bmi.value = "";
    }
    catch(e){
        throw new Error(e.message);
    }
    finally{
        btn1.disabled = false;
        btn1.innerText = "Submit";
    }
})