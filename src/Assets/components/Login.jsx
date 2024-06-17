import react, {useState} from 'react'
import appFirebase from '../../credentials'
import {getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword} from 'firebase/auth'
import firebase from 'firebase/compat/app'

const auth = getAuth(appFirebase)

const Login = () => {

    const [registrando, setRegistrando] = useState(false)

    return (
        <div className='container'>
            <h1>PRUEBA</h1>
            <form>
                <input type="text" placeholder='email'/>
                <input type="text" placeholder='contrasena'/>
                <button>{registrando ? "Registrate" : "Inicia Sesion"}</button>
            </form>
            <h4>{registrando ? "Si ya tienes cuenta" : "No tienes cuenta"}<button onClick={() => setRegistrando(!registrando)}>{registrando ? "Inicia Sesion": "Registrate"}</button></h4>
        </div>
    )
}

export default Login