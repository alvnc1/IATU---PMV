import React, { useEffect, useState } from "react";
import Sidebar from "./sidebar"; 
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Dropdown from 'react-bootstrap/Dropdown';
import { MdDelete, MdAccessTime, MdMoreVert, MdShare } from "react-icons/md"; 
import { collection, getDocs, deleteDoc, doc, query, where } from 'firebase/firestore';
import { db } from "./firebase";
import { getAuth, onAuthStateChanged } from "firebase/auth";  // Importamos Firebase Auth y onAuthStateChanged
import './css/MyProjects.css';
import { useNavigate } from 'react-router-dom';

function MyProjects() {
  const [projects, setProjects] = useState([]);
  const [sortOrder, setSortOrder] = useState('asc');
  const [loading, setLoading] = useState(true);  // Nuevo estado para manejar la carga de la autenticación
  const navigate = useNavigate();
  const auth = getAuth();  // Inicializamos Firebase Auth

  const getProjects = async (userId) => {
    try {
      // Filtrar proyectos por el UID del usuario autenticado
      const projectsCollection = query(collection(db, 'proyectos'), where('userId', '==', userId));
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
      setLoading(false);  // Finalizamos el estado de carga
    } catch (error) {
      console.error('Error al obtener proyectos: ', error);
      setLoading(false);  // Finalizamos el estado de carga
    }
  };

  const deleteProject = async (projectId) => {
    try {
      await deleteDoc(doc(db, 'proyectos', projectId));
      const user = auth.currentUser;
      if (user) {
        getProjects(user.uid);  // Recargar proyectos después de eliminar
      }
      alert('Proyecto eliminado correctamente');
    } catch (error) {
      console.error('Error al eliminar el proyecto: ', error);
      alert('Hubo un error al eliminar el proyecto');
    }
  };

  const shareProject = (projectId) => {
    alert(`Compartir proyecto con ID: ${projectId}`);
    // Aquí agregar la funcionalidad de compartir
  };

  useEffect(() => {
    // Utilizamos onAuthStateChanged para manejar el estado de autenticación del usuario
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        getProjects(user.uid);  // Si el usuario está autenticado, cargamos los proyectos
      } else {
        setLoading(false);  // Si no hay usuario, dejamos de cargar
        console.log("No hay usuario autenticado.");
      }
    });

    // Cleanup para desuscribirse del listener de onAuthStateChanged cuando se desmonta el componente
    return () => unsubscribe();
  }, [sortOrder]);  // Añadimos sortOrder como dependencia para permitir el reordenamiento

  if (loading) {
    return <div id="loader">
    <div class="spinner"></div>
  </div>;  // Mensaje de carga mientras se obtienen los proyectos o se verifica la autenticación
  }

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div style={{ marginLeft: '250px', width: '100%' }}>
        <Container fluid style={{ padding: '20px', backgroundColor: '#f8f9fa' }}>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h2 className="project-header">Mis Proyectos</h2>
          </div>
          <Row>
            {projects.length > 0 ? (
              projects.map((project) => (
                <Col key={project.id} xs={12} sm={6} md={4} lg={3} className="mb-4">
                  <div 
                    className="project-tile" 
                    onClick={() => navigate(`/project/${project.id}`)}
                  >
                    <div className="d-flex justify-content-between align-items-start">
                      <div>
                        <h5 style={{ fontWeight: 'bold', marginBottom: '5px' }}>{project.nombreProyecto}</h5>
                        <p style={{ fontSize: '14px', color: '#555', marginBottom: '10px' }}>{project.descripcionProyecto}</p>
                      </div>
                      <Dropdown onClick={(e) => e.stopPropagation()}>
                        <Dropdown.Toggle as="div" className="p-2" style={{ cursor: 'pointer' }}>
                          <MdMoreVert size={24} />
                        </Dropdown.Toggle>
                        <Dropdown.Menu align="end">
                          <Dropdown.Item onClick={() => shareProject(project.id)}>
                            <MdShare style={{ marginRight: '5px' }} />
                            Compartir
                          </Dropdown.Item>
                          <Dropdown.Item onClick={() => deleteProject(project.id)}>
                            <MdDelete style={{ marginRight: '5px' }} />
                            Eliminar
                          </Dropdown.Item>
                        </Dropdown.Menu>
                      </Dropdown>
                    </div>
                    <div className="d-flex align-items-center mb-2">
                      <MdAccessTime style={{ marginRight: '5px', color: '#888' }} />
                      <small className="text-muted">Last updated: {new Date(project.fechaCreacion).toLocaleDateString()}</small>
                    </div>
                  </div>
                </Col>
              ))
            ) : (
              <p></p>
            )}
          </Row>
        </Container>
      </div>
    </div>
  );
}

export default MyProjects;
