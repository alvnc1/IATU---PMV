import react, {useState} from 'react'
import appFirebase from '../../credentials'
import {getAuth, signOut} from 'firebase/auth'
import firebase from 'firebase/compat/app'

const auth = getAuth(appFirebase)

const Home = ({correoUsuario}) => {
    return (
        <div>
            <h1>malactm eri un {correoUsuario} <button onClick={() =>signOut(auth)}>LogOut</button></h1>
        </div>
    )
}

export default Home