// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import {getAuth} from "firebase/auth";
import {getFirestore} from "firebase/firestore";
import { getStorage } from "firebase/storage";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAlAjh3ZFeW-BUdLM4L6_WslJGPywV4lyY",
  authDomain: "iatu-pmv.firebaseapp.com",
  databaseURL: "https://iatu-pmv-default-rtdb.firebaseio.com",
  projectId: "iatu-pmv",
  storageBucket: "iatu-pmv.appspot.com",
  messagingSenderId: "149128003789",
  appId: "1:149128003789:web:193f5ed82edebcf7116984",
  measurementId: "G-S2WLPZST4E"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

export const auth=getAuth();
export const db=getFirestore(app);
export const storage = getStorage(app);
export default app;
