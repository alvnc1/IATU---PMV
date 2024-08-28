import React, { useEffect, useState } from 'react';
import { Nav } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { MdAddBox, MdAccountCircle, MdApps } from "react-icons/md";
import { auth, db } from "./firebase";
import { doc, getDoc } from "firebase/firestore";
import './css/Sidebar.css'; // Archivo CSS para estilos adicionales

function Sidebar() {
  const [userDetails, setUserDetails] = useState(null);

  const fetchUserData = async () => {
    auth.onAuthStateChanged(async (user) => {
      if (user) {
        const docRef = doc(db, "Users", user.uid);
        const docSnap = await getDoc(docRef);
        if (docSnap.exists()) {
          setUserDetails(docSnap.data());
        } else {
          console.log("User document does not exist");
        }
      } else {
        console.log("User is not logged in");
      }
    });
  };

  useEffect(() => {
    fetchUserData();
  }, []);

  async function handleLogout() {
    try {
      await auth.signOut();
      window.location.href = "/login";
      console.log("Cierre exitoso de sesión!");
    } catch (error) {
      console.error("Error logging out:", error.message);
    }
  }

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h4>IATU</h4>
      </div>
      <div className="sidebar-divider"></div>
      <Nav className="flex-column">
        <Nav.Item>
          <Link to="/newproject" className="nav-link">
            <MdAddBox className="sidebar-icon" /> Nuevo Proyecto
          </Link>
        </Nav.Item>
      </Nav>

      {/* Separamos el contenido principal del contenido que va al fondo */}
      <div className="sidebar-bottom">
        <div className="sidebar-divider"></div>
        <Nav className="flex-column">
          <Nav.Item>
            <Link to="/projects" className="nav-link">
              <MdApps className="sidebar-icon" /> Proyectos
            </Link>
          </Nav.Item>
          <Nav.Item>
            <div className="nav-link" onClick={handleLogout} style={{ cursor: 'pointer' }}>
              <MdAccountCircle className="sidebar-icon" /> {userDetails ? `${userDetails.firstName} ${userDetails.lastName}` : 'Mi Cuenta'}
            </div>
          </Nav.Item>
        </Nav>
      </div>
    </div>
  );
}

export default Sidebar;
