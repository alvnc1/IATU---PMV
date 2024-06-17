// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAlAjh3ZFeW-BUdLM4L6_WslJGPywV4lyY",
  authDomain: "iatu-pmv.firebaseapp.com",
  projectId: "iatu-pmv",
  storageBucket: "iatu-pmv.appspot.com",
  messagingSenderId: "149128003789",
  appId: "1:149128003789:web:193f5ed82edebcf7116984",
  measurementId: "G-S2WLPZST4E"
};

// Initialize Firebase
const appFirebase = initializeApp(firebaseConfig);
const analytics = getAnalytics(appFirebase);
export default appFirebase;