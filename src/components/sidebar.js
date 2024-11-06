import React, { useEffect, useState } from 'react';
import { Nav, Modal, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { MdAddBox, MdAccountCircle, MdApps } from "react-icons/md";
import { auth, db } from "./firebase";
import { doc, getDoc } from "firebase/firestore";
import './css/Sidebar.css';

import logo from './images/logo_white.png';

function Sidebar() {
  const [userDetails, setUserDetails] = useState(null);
  const [showLogoutModal, setShowLogoutModal] = useState(false); // Estado para controlar la visibilidad del modal

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

  const handleLogout = async () => {
    try {
      await auth.signOut();
      window.location.href = "/login";
      console.log("Cierre exitoso de sesión!");
    } catch (error) {
      console.error("Error logging out:", error.message);
    }
  };

  // Funciones para controlar el modal de cierre de sesión
  const openLogoutModal = () => setShowLogoutModal(true);
  const closeLogoutModal = () => setShowLogoutModal(false);

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <Link to="/projects">
          <img src={logo} alt="Logo" className="sidebar-logo" />
        </Link>
      </div>
      <div className="sidebar-divider"></div>
      <Nav className="flex-column">
        <Nav.Item>
          <Link to="/newproject" className="nav-link">
            <MdAddBox className="sidebar-icon" /> Nuevo Proyecto
          </Link>
        </Nav.Item>
      </Nav>

      <div className="sidebar-bottom">
        <div className="sidebar-divider"></div>
        <Nav className="flex-column">
          <Nav.Item>
            <Link to="/projects" className="nav-link">
              <MdApps className="sidebar-icon" /> Proyectos
            </Link>
          </Nav.Item>
          <Nav.Item>
            <div className="nav-link" onClick={openLogoutModal} style={{ cursor: 'pointer' }}>
              <MdAccountCircle className="sidebar-icon" /> {userDetails ? `${userDetails.firstName} ${userDetails.lastName}` : 'Mi Cuenta'}
            </div>
          </Nav.Item>
        </Nav>
      </div>

      {/* Modal de confirmación de cierre de sesión */}
      <Modal show={showLogoutModal} onHide={closeLogoutModal} centered>
        <Modal.Header closeButton>
          <Modal.Title>Confirmar cierre de sesión</Modal.Title>
        </Modal.Header>
        <Modal.Body>¿Estás seguro de que quieres cerrar sesión?</Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={closeLogoutModal}>
            Cancelar
          </Button>
          <Button variant="danger" onClick={handleLogout}>
            Cerrar sesión
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default Sidebar;
