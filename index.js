const btn1 = document.querySelector(".register_btn");

const email1 = document.querySelector(".email1");
const pass1 = document.querySelector(".pass1");

const btn2 = document.querySelector(".login_btn");
//to register
if(btn1){
    btn1.addEventListener("click",async ()=>{
        const inp1 = email1.value.trim();
        const inp2 = pass1.value.trim();
        if(!inp1||!inp2){
            alert("Enter both data");
            return ; 
        }
        try{
            const resp = await fetch('/register',{
                method:'POST',
                headers:{
                    'Content-Type':'application/json'
                },
                body:JSON.stringify({email1:inp1,password1:inp2})
            });
            const data = await resp.json();
            if(!resp.ok){
                alert(data.msg||"Registration Failed");
                return ;
            }
            window.location.href="home.html";
            email1.value = "";
            pass1.value = "";
        }
        catch(e){
            throw new Error(e.message);
        }
        //on clicking register btn if succesful goes to my homepage
    });
}
//to login
if(btn2){
    btn2.addEventListener('click',async()=>{
        const inp4 = email1.value.trim();
        const inp5 = pass1.value.trim();
        if(!inp4 || !inp5){
            alert("Fill all the details");
            return;
        }
        try{
            const resp = await fetch('/login',{
                method:'POST',
                headers:{
                    'Content-Type' : 'application/json'
                },
                body: JSON.stringify({ email2: inp4, pass1: inp5 })
                //so both email2 and pass1 snt to backend
                //so when u use app.post and res.json({email2:email}) and so on
            });

            const data = await resp.json();

            if(!resp.ok){
                alert(data.msg || "Login Failed");
                return;
            }

            alert("Successfully Logged in");
            window.location.href = 'home.html';
            email1.value = "";
            pass1.value = "";
        }
        catch(e){
            throw new Error(e.message);
        }
        
    });
}


