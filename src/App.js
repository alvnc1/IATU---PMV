import React from "react";

import Signup from "./components/Signup";
import Login from "./components/Login";
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

// Configura Firebase
const firebaseConfig = {
  apiKey: "AIzaSyAlAjh3ZFeW-BUdLM4L6_WslJGPywV4lyY",
  authDomain: "iatu-pmv.firebaseapp.com",
  projectId: "iatu-pmv",
  storageBucket: "iatu-pmv.appspot.com",
  messagingSenderId: "149128003789",
  appId: "1:149128003789:web:193f5ed82edebcf7116984",
};

// Inicializa Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);


function openTab(evt, tabName) {
  var i, tabcontent, tablinks;

  // Hide all tab content
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  // Remove the "active" class from all tab links
  tablinks = document.getElementsByClassName("tablink");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].classList.remove("active");
  }

  // Show the selected tab content and add the "active" class to the clicked tab link
  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.classList.add("active");
}

function App() {
  return (
    <div className="App">
      <h1>Bienvenido a IATU</h1>
      <div className="form-wrap">
        <div className="tabs">
          <h3 className="signup-tab">
            <a className="tablink active" onClick={(e) => openTab(e, "signup-tab-content")}>
              Registrarse
            </a>
          </h3>
          <h3 className="login-tab">
            <a className="tablink" onClick={(e) => openTab(e, "login-tab-content")}>
              Iniciar Sesión
            </a>
          </h3>
        </div>
        <div className="tabs-content">
          <Signup auth={auth} />
          <Login auth={auth} />
        </div>
      </div>
      <div class='ripple-background'>
        <div class='circle xxlarge shade1'></div>
        <div class='circle xlarge shade2'></div>
        <div class='circle large shade3'></div>
        <div class='circle mediun shade4'></div>
        <div class='circle small shade5'></div>
      </div>
    </div>
    
  );
}

export default App;
