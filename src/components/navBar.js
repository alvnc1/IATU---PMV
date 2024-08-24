import React, { useEffect, useState } from "react";
import { auth, db } from "./firebase";
import { doc, getDoc } from "firebase/firestore";
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import '../login-register.css';

function NavBar() {
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
    <div>
    {userDetails ? (
      <>
    <Navbar collapseOnSelect expand="lg" className="bg-body-tertiary">
      <Container>
        <Navbar.Brand href="/projects">
          <img
            src={require('./images/logo-removebg.png')}
            alt="IATU Logo"
            style={{ height: '40px', width: 'auto' }} // Ajusta el tamaño de la imagen según sea necesario
          />
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="responsive-navbar-nav" />
        <Navbar.Collapse id="responsive-navbar-nav">
          <Nav className="me-auto">
          </Nav>
          <Nav>
          <NavDropdown title={userDetails.firstName + ' ' + userDetails.lastName } id="collapsible-nav-dropdown">
              <NavDropdown.Item onClick={handleLogout}> Cerrar Sesión</NavDropdown.Item>
          </NavDropdown>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
    </>
    ) : (
        <Navbar collapseOnSelect expand="lg" className="bg-body-tertiary">
        <Container>
          <Navbar.Brand href="/projects">
            <img
              src={require('./images/logo.png')}
              alt="IATU Logo"
              style={{ height: '40px', width: 'auto' }} // Ajusta el tamaño de la imagen según sea necesario
            />
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="responsive-navbar-nav" />
          <Navbar.Collapse id="responsive-navbar-nav">
            <Nav className="me-auto">
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>
    )}
    </div>
  );
}

export default NavBar;
