import React, { useEffect, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";
import "../node_modules/bootstrap/dist/css/bootstrap.min.css";

import Login from "./components/Login";
import SignUp from "./components/register";

import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { auth } from "./components/firebase";
import MyProjects from "./components/myProjects";
import NewProject from "./components/newProject";
import ProjectPage from './components/pageProject';
import NewTask from './components/newTask';
import Sidebar from "./components/sidebar";


function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((user) => {
      setUser(user);
    });
    return () => unsubscribe();
  }, []);

  return (
    <Router>
      <div className="App">
        <ConditionalWrapper>
          <Routes>
            <Route path="/" element={user ? <Navigate to="/projects" /> : <Login />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<SignUp />} />
            <Route path="/projects" element={<MyProjects />} />
            <Route path="/newproject" element={<NewProject />} />
            <Route path="/project/:id" element={<ProjectPage />} />
            <Route path="/newTask/:id" element={<NewTask />} />
            <Route path="/sidebar" element={<Sidebar />} />
          </Routes>
          <ToastContainer />
        </ConditionalWrapper>
      </div>
    </Router>
  );
}

function ConditionalWrapper({ children }) {
  const location = useLocation();
  const isAuthRoute = location.pathname === "/login" || location.pathname === "/register";

  return isAuthRoute ? (
    <div className="auth-wrapper">
      <div className="auth-inner">
        {children}
      </div>
    </div>
  ) : (
    <>{children}</>
  );
}

export default App;
