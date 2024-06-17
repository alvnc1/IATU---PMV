// src/components/Login.js
import React, { useState } from "react";
import { getAuth, signInWithEmailAndPassword } from "firebase/auth";

function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState(""); // Estado para el mensaje de éxito

  const handleUsernameChange = (event) => {
    setUsername(event.target.value);
  };

  const handlePasswordChange = (event) => {
    setPassword(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const auth = getAuth();
    try {
      const userCredential = await signInWithEmailAndPassword(auth, username, password);
      console.log("User logged in:", userCredential.user);
      setSuccessMessage("¡Inicio de sesión exitoso!"); // Establecer mensaje de éxito
      setUsername(""); // Limpiar los campos después del inicio de sesión exitoso
      setPassword("");
      setError(""); // Limpiar cualquier mensaje de error anterior
    } catch (error) {
      setError(error.message);
      console.error("Login error:", error);
      setSuccessMessage(""); // Limpiar mensaje de éxito en caso de error
    }
  };

  return (
    <div id="login-tab-content" className="tabcontent">
      <form className="login-form" onSubmit={handleSubmit}>
        <input type="text" className="input" placeholder="Correo Electrónico" value={username} onChange={handleUsernameChange} required />
        <input type="password" className="input" placeholder="Contraseña" value={password} onChange={handlePasswordChange} required />
        <input type="submit" className="button" value="Iniciar Sesión" />
      </form>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {successMessage && <p style={{ color: "green" }}>{successMessage}</p>}
      <div className="help-text">
        <p><a href="#">Cambiar Contraseña</a></p>
      </div>
    </div>
  );
}

export default Login;
