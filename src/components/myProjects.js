import React, { useEffect, useState } from "react";
import NavBar from "./navBar";
import "../login-register.css";
import Container from "react-bootstrap/Container";
import Table from "react-bootstrap/Table";
import Button from 'react-bootstrap/Button';
import { IoMdPlayCircle } from "react-icons/io";
import { MdDelete } from "react-icons/md";
import { collection, getDocs, deleteDoc, doc } from 'firebase/firestore';
import { db } from "./firebase";

function MyProjects() {
  const [projects, setProjects] = useState([]);
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
  
  const handleSortByDate = () => {
    if (sortOrder === 'asc') {
      setSortOrder('desc');
    } else {
      setSortOrder('asc');
    }
  };
  
  useEffect(() => {
    getProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

  return (
    <div>
      <NavBar />

      <Container
        style={{
          marginTop: "20px",
          backgroundColor: "white",
          borderRadius: "10px",
          padding: "20px",
          width: "90%", // Ancho del contenedor interno
          maxWidth: "1200px", // Ancho máximo del contenedor interno
          height: "80vh", // Altura del contenedor interno
          overflowY: "auto", // Scroll vertical si es necesario
          boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)", // Sombra ligera
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
                <th style={{ cursor: 'pointer' }} onClick={handleSortByDate}>Fecha de creación</th>
                <th style={{ textAlign: "center" }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {projects.map(project => (
                <tr key={project.id}>
                  <td>{project.nombreProyecto}</td>
                  <td>{getUserInfo(project.selectedOption)}</td>
                  <td>{project.inputValue}</td>
                  <td>{new Date(project.fechaCreacion).toLocaleDateString()}</td>
                  <td style={{ textAlign: "center" }}>
                    <div className="d-flex justify-content-between">
                      <Button variant="success" style={{ fontSize: '10px', padding: '2px 5px' }} onClick={() => window.location.href = `/project/${project.id}`}> <IoMdPlayCircle /> Ejecutar Prueba</Button>
                      <Button variant="danger" style={{ fontSize: '10px', padding: '2px 5px' }} onClick={() => deleteProject(project.id)}> <MdDelete />Eliminar Proyecto</Button>
                      
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      </Container>
    </div>
  );
}

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

export default MyProjects;
