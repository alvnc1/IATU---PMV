// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAIxxVbhOzi7VY8fbhRFlMNvOuEgzHRTFM",
  authDomain: "iatu-2b7a5.firebaseapp.com",
  projectId: "iatu-2b7a5",
  storageBucket: "iatu-2b7a5.appspot.com",
  messagingSenderId: "86398412636",
  appId: "1:86398412636:web:cc12ff1808600f04098399",
  measurementId: "G-Y2S9WWDXB0"
};

// Initialize Firebase
const appFirebase = initializeApp(firebaseConfig);
const analytics = getAnalytics(appFirebase);
export default appFirebase;