// src/components/Signup.js
import React, { useState } from "react";
import { getAuth, createUserWithEmailAndPassword } from "firebase/auth";

function Signup() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState(""); // Estado para el mensaje de éxito

  const handleUsernameChange = (event) => {
    setUsername(event.target.value);
  };

  const handlePasswordChange = (event) => {
    setPassword(event.target.value);
  };

  const handleEmailChange = (event) => {
    setEmail(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const auth = getAuth();
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      console.log("User registered:", userCredential.user);
      setSuccessMessage("¡Registro exitoso! Puedes iniciar sesión."); // Establecer mensaje de éxito
      setUsername(""); // Limpiar los campos después del registro exitoso
      setPassword("");
      setEmail("");
      setError(""); // Limpiar cualquier mensaje de error anterior
    } catch (error) {
      setError(error.message);
      console.error("Registration error:", error);
      setSuccessMessage(""); // Limpiar mensaje de éxito en caso de error
    }
  };

  return (
    <div id="signup-tab-content" className="tabcontent" style={{ display: "block" }}>
      <form className="signup-form" onSubmit={handleSubmit}>
        <input type="email" className="input" placeholder="Correo Electrónico" value={email} onChange={handleEmailChange} required />
        <input type="text" className="input" placeholder="Nombre de Usuario" value={username} onChange={handleUsernameChange} required />
        <input type="password" className="input" placeholder="Contraseña" value={password} onChange={handlePasswordChange} required />
        <input type="submit" className="button" value="Registrarse" />
      </form>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {successMessage && <p style={{ color: "green" }}>{successMessage}</p>}
      <div className="help-text">
        <p>Al momento de registrarte aceptas los</p>
        <p><a href="#">Términos y Condiciones</a></p>
      </div>
    </div>
  );
}

export default Signup;
