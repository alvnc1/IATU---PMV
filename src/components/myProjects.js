import React, { useEffect, useState } from "react";
import NavBar from "./navBar";
import "../myProjects.module.css";
import Container from "react-bootstrap/Container";
import Table from "react-bootstrap/Table";
import Button from 'react-bootstrap/Button';
import { MdDelete } from "react-icons/md";
import { collection, getDocs, deleteDoc, doc } from 'firebase/firestore';
import { db } from "./firebase";
import TestRunner from './testRunner';
import CriteriaPDFGenerator from './CriteriaPDFGenerator'; 

function MyProjects() {
  const [projects, setProjects] = useState([]);
  const [sortOrder, setSortOrder] = useState('asc');
  const [testStatus, setTestStatus] = useState({}); // Nuevo estado para el estado de las pruebas

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
          <Button href='./newproject' style={{ height: '50px', padding: '12px', fontSize: '14px' }} variant="primary"> Nuevo Proyecto</Button>
        </div>
        <div style={{ marginTop: '20px' }}>
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>Nombre del Proyecto</th>
                <th>Usuario Seleccionado</th>
                <th>Descripción de la Prueba</th>
                <th>Sitio Web</th>
                <th style={{ cursor: 'pointer' }} onClick={handleSortByDate}>Fecha de creación</th>
                <th style={{ textAlign: "center" }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {projects.map(project => (
                <React.Fragment key={project.id}>
                  <tr>
                    <td>{project.nombreProyecto}</td>
                    <td>{getUserInfo(project.selectedOption)}</td>
                    <td>{project.inputValue}</td>
                    <td>{project.webLink}</td>
                    <td>{new Date(project.fechaCreacion).toLocaleDateString()}</td>
                    <td style={{ textAlign: "center" }}>
                      <div className="d-flex justify-content-between">
                        <TestRunner project={project} onTestRun={() => handleTestRun(project.id)} />
                        <CriteriaPDFGenerator project={project} disabled={!testStatus[project.id]} />
                        <Button variant="danger" style={{ fontSize: '10px', padding: '2px 5px' }} onClick={() => deleteProject(project.id)}> <MdDelete />Eliminar Proyecto</Button>
                      </div>
                    </td>
                  </tr>
                </React.Fragment>
              ))}
            </tbody>
          </Table>
        </div>
      </Container>
    </div>
  );
}

export default MyProjects;
