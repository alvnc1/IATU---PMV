// src/components/MyProjects.js
import React, { useEffect, useState } from "react";
import NavBar from "./navBar";
import "../login-register.css";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Button from 'react-bootstrap/Button';
import Card from 'react-bootstrap/Card';
import Modal from 'react-bootstrap/Modal';
import { MdDelete } from "react-icons/md";
import { collection, getDocs, deleteDoc, doc } from 'firebase/firestore';
import { db } from "./firebase";
import TestRunner from './testRunner'; // Importa el componente TestRunner
import CriteriaPDFGenerator from './CriteriaPDFGenerator'; 
import './MyProjects.css'; // Importa el archivo CSS para estilos adicionales

function MyProjects() {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [sortOrder, setSortOrder] = useState('asc');

  // Función para obtener los proyectos desde Firebase
  const getProjects = async () => {
    const projectsCollection = collection(db, 'proyectos');
    const snapshot = await getDocs(projectsCollection);
    const projectsList = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    // Ordenar proyectos por fecha de creación
    projectsList.sort((a, b) => {
      if (sortOrder === 'asc') {
        return new Date(a.fechaCreacion) - new Date(b.fechaCreacion);
      } else {
        return new Date(b.fechaCreacion) - new Date(a.fechaCreacion);
      }
    });
    setProjects(projectsList);
  };

  // Función para eliminar un proyecto
  const deleteProject = async (projectId) => {
    try {
      await deleteDoc(doc(db, 'proyectos', projectId));
      getProjects(); // Actualizar la lista de proyectos después de eliminar
      alert('Proyecto eliminado correctamente');
    } catch (error) {
      console.error('Error al eliminar el proyecto: ', error);
      alert('Hubo un error al eliminar el proyecto');
    }
  };

  // Función para obtener la información del usuario seleccionado
  const getUserInfo = (selectedOption) => {
    if (selectedOption === "opcion1") {
      return "Javier Sánchez, 32 años";
    } else if (selectedOption === "opcion2") {
      return "José Gómez, 68 años";
    } else {
      return "Usuario no especificado";
    }
  };

  const handleSortByDate = () => {
    setSortOrder(prevSortOrder => prevSortOrder === 'asc' ? 'desc' : 'asc');
  };

  const handleShowModal = (project) => {
    setSelectedProject(project);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setSelectedProject(null);
    setShowModal(false);
  };

  useEffect(() => {
    getProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <NavBar />

      <Container
        style={{
          marginTop: "20px",
          backgroundColor: "white",
          borderRadius: "10px",
          padding: "20px",
          width: "90%",
          maxWidth: "1200px",
          height: "80vh",
          overflowY: "auto",
          boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
        }}
      >
        <div className="d-flex justify-content-between align-items-center">
          <h2 style={{ textAlign: "left", margin: 0 }}>Mis Proyectos</h2>
          <Button href='./newproject' style={{ height: '50px', padding: '12px', fontSize: '14px' }} variant="primary"> Nuevo Proyecto</Button>
        </div>
        <div style={{ marginTop: '20px' }}>
          <Row>
            {projects.map((project, index) => (
              <Col key={project.id} xs={12} sm={6} md={4} lg={3} className="mb-4">
                <Card className="project-card">
                  <Card.Img variant="top" src="https://via.placeholder.com/150" alt="Project Image" />
                  <Card.Body className="text-center">
                    <Card.Title>{project.nombreProyecto}</Card.Title>
                    <Button variant="primary" onClick={() => handleShowModal(project)}>View Project</Button>
                  </Card.Body>
                </Card>
              </Col>
            ))}
            <Col xs={12} sm={6} md={4} lg={3} className="mb-4">
              <Card className="h-100 d-flex justify-content-center align-items-center">
                <Button href='./newproject' variant="outline-primary" className="w-100 h-100">
                  + New Project
                </Button>
              </Card>
            </Col>
          </Row>
        </div>
      </Container>

      {selectedProject && (
        <Modal show={showModal} onHide={handleCloseModal}>
          <Modal.Header closeButton>
            <Modal.Title>{selectedProject.nombreProyecto}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <p><strong>Usuario:</strong> {getUserInfo(selectedProject.selectedOption)}</p>
            <p><strong>Descripción:</strong> {selectedProject.inputValue}</p>
            <p><strong>Sitio Web:</strong> <a href={selectedProject.webLink} target="_blank" rel="noopener noreferrer">{selectedProject.webLink}</a></p>
            <p><strong>Fecha de creación:</strong> {new Date(selectedProject.fechaCreacion).toLocaleDateString()}</p>
            <div className="d-flex flex-column align-items-stretch">
              <Button variant="info" className="mb-2"><TestRunner project={selectedProject} /></Button>
              <Button variant="secondary" className="mb-2"><CriteriaPDFGenerator project={selectedProject} /></Button>
              <Button variant="danger" onClick={() => deleteProject(selectedProject.id)}> <MdDelete /> Eliminar Proyecto</Button>
            </div>
          </Modal.Body>
        </Modal>
      )}
    </div>
  );
}

export default MyProjects;
