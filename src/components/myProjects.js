import React, { useEffect, useState } from "react";
import NavBar from "./navBar";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Button from 'react-bootstrap/Button';
import Card from 'react-bootstrap/Card';
import Modal from 'react-bootstrap/Modal';
import { MdDelete } from "react-icons/md";
import { collection, getDocs, deleteDoc, doc } from 'firebase/firestore';
import { db } from "./firebase";
import TestRunner from './testRunner';
import CriteriaPDFGenerator from './CriteriaPDFGenerator';
import './MyProjects.css'; // Importa el archivo CSS para estilos adicionales
import { useNavigate } from 'react-router-dom'; 

function MyProjects() {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [sortOrder, setSortOrder] = useState('asc');
  const [testStatus, setTestStatus] = useState({});
  const navigate = useNavigate();

  const getProjects = async () => {
    const projectsCollection = collection(db, 'proyectos');
    const snapshot = await getDocs(projectsCollection);
    const projectsList = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    projectsList.sort((a, b) => {
      if (sortOrder === 'asc') {
        return new Date(a.fechaCreacion) - new Date(b.fechaCreacion);
      } else {
        return new Date(b.fechaCreacion) - new Date(a.fechaCreacion);
      }
    });
    setProjects(projectsList);
    const initialTestStatus = {};
    projectsList.forEach(project => {
      initialTestStatus[project.id] = false;
    });
    setTestStatus(initialTestStatus);
  };

  const deleteProject = async (projectId) => {
    try {
      await deleteDoc(doc(db, 'proyectos', projectId));
      getProjects();
      alert('Proyecto eliminado correctamente');
    } catch (error) {
      console.error('Error al eliminar el proyecto: ', error);
      alert('Hubo un error al eliminar el proyecto');
    }
  };

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

  const handleTestRun = (projectId) => {
    setTestStatus(prevStatus => ({
      ...prevStatus,
      [projectId]: true
    }));
  };

  useEffect(() => {
    getProjects();
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
        </div>
        <div style={{ marginTop: '20px' }}>
          <Row>
            {projects.map((project) => (
              <Col key={project.id} xs={12} sm={6} md={4} lg={3} className="mb-4">
                <Card className="project-card">
                  <Card.Img variant="top" src={require("./images/logo.png")} alt="Project Image" />
                  <Card.Body className="text-center">
                    <Card.Title>{project.nombreProyecto}</Card.Title>
                    <Card.Title>{project.descripcionProyecto}</Card.Title>
                    <Button variant="primary" onClick={() => navigate(`/project/${project.id}`)}>View Project</Button>
                  </Card.Body>
                </Card>
              </Col>
            ))}
            <Col xs={12} sm={6} md={4} lg={3} className="mb-4">
              <Card className="h-100 d-flex justify-content-center align-items-center">
                <Button href='./newproject' variant="outline-primary" className="w-100 h-100">
                  + Nuevo Proyecto
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
              <Button variant="light" className="neutral-btn mb-2"><TestRunner project={selectedProject} /></Button>
              <Button variant="light" className="neutral-btn mb-2" disabled={!testStatus[selectedProject.id]}><CriteriaPDFGenerator project={selectedProject} /></Button>
              <Button variant="danger" className="neutral-btn danger-btn" onClick={() => deleteProject(selectedProject.id)}> <MdDelete /> Eliminar Proyecto</Button>
            </div>
          </Modal.Body>
        </Modal>
      )}
    </div>
  );
}

export default MyProjects;
