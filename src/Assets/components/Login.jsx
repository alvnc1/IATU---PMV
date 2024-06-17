import react, {useState} from 'react'
import appFirebase from '../../credentials'
import {getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword} from 'firebase/auth'
import firebase from 'firebase/compat/app'

const auth = getAuth(appFirebase)

const Login = () => {

    const [registrando, setRegistrando] = useState(false)

    const functAutentication = async(e) =>{
        e.PreventDefault();
        const correo = e.target.email.value;
        const contrasena = e.target.password.value;
        if (registrando){
            await createUserWithEmailAndPassword(auth, correo, contrasena)
        }
        else{
            try {
                await signInWithEmailAndPassword(auth, correo, password)                
            } catch (error) {
                alert("El correo/contrasena no funciona")
            }
        }
    }

    return (
        <div className='container'>
            <form onSubmit={functAutentication}>
                <input type="text" placeholder='email' id="email"/>
                <input type="text" placeholder='contrasena' id="pass"/>
                <button>{registrando ? "Registrate" : "Inicia Sesion"}</button>
            </form>
            <h4>{registrando ? "Si ya tienes cuenta" : "No tienes cuenta"}<button onClick={() => setRegistrando(!registrando)}>{registrando ? "Inicia Sesion": "Registrate"}</button></h4>
        </div>
    )
}

export default Login