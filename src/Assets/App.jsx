import { useState } from 'react'

import appFirebase from '../src/credentials'
import {getAuth, onAuthStateChanged} from 'firebase/auth'
const auth = getAuth(appFirebase)

import Login from '../src/components/Login'
import Home from '../src/components/Home'

function App() {
    
    const [usuario, setUsuario] = useState(null)
    onAuthStateChanged(auth, (usuarioFirebase) =>{
        if (usuarioFirebase){
            setUsuario(usuarioFirebase)
        }
        else
        {
            setUsuario(null)
        }
    })

    return (
        <div>
            {usuario ? <Home correousuario = {usuario.email}/> : <Login/>}
        </div>
    )
}

export default App