import React, { useEffect, useState } from "react";
import Sidebar from "./sidebar"; 
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Dropdown from 'react-bootstrap/Dropdown';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import { MdDelete, MdAccessTime, MdMoreVert, MdShare, MdPeople, MdAccountCircle } from "react-icons/md"; 
import { collection, getDocs, deleteDoc, doc, query, where, or, updateDoc, arrayUnion } from 'firebase/firestore';
import { db } from "./firebase";
import { getAuth, onAuthStateChanged } from "firebase/auth";
import './css/MyProjects.css';
import { useNavigate } from 'react-router-dom';

function MyProjects() {
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [sortOrder, setSortOrder] = useState('asc');
  const [loading, setLoading] = useState(true);
  const [showShareModal, setShowShareModal] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false); // Estado para el modal de confirmación de eliminación
  const [usersWithAccess, setUsersWithAccess] = useState([]);
  const [usersWithoutAccess, setUsersWithoutAccess] = useState([]);
  const [hoveredUser, setHoveredUser] = useState(null);

  const navigate = useNavigate();
  const auth = getAuth();

  const getProjects = async (userId) => {
    try {
      const projectsCollection = query(
        collection(db, 'proyectos'),
        or(
          where('userId', '==', userId),
          where('sharedWith', 'array-contains', userId)
        )
      );

      const snapshot = await getDocs(projectsCollection);
      const projectsList = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));

      projectsList.sort((a, b) => {
        return sortOrder === 'asc'
          ? new Date(a.fechaCreacion) - new Date(b.fechaCreacion)
          : new Date(b.fechaCreacion) - new Date(a.fechaCreacion);
      });

      setProjects(projectsList);
      setLoading(false);
    } catch (error) {
      console.error('Error al obtener proyectos: ', error);
      setLoading(false);
    }
  };

  const getUsers = async (userId) => {
    try {
      const usersCollection = collection(db, 'Users');
      const snapshot = await getDocs(usersCollection);
      const usersList = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));

      const filteredUsers = usersList.filter(user => user.id !== userId);

      setUsers(filteredUsers);
    } catch (error) {
      console.error('Error al obtener usuarios: ', error);
    }
  };

  const handleDeleteProject = (projectId) => {
    setSelectedProject(projectId);
    setShowDeleteModal(true); // Mostrar modal de confirmación de eliminación
  };

  const confirmDeleteProject = async () => {
    try {
      await deleteDoc(doc(db, 'proyectos', selectedProject));
      const user = auth.currentUser;
      if (user) {
        getProjects(user.uid);
      }
    } catch (error) {
      console.error('Error al eliminar el proyecto: ', error);
      alert('Hubo un error al eliminar el proyecto');
    }
    setShowDeleteModal(false); // Ocultar el modal después de la eliminación
    setSelectedProject(null); // Limpiar el proyecto seleccionado
  };

  const handleShareProject = (project) => {
    setSelectedProject(project);

    const owner = users.find(user => user.id === project.userId);
    const withAccess = users.filter(user => project.sharedWith?.includes(user.id));

    if (owner && !withAccess.some(user => user.id === owner.id)) {
      withAccess.unshift(owner);
    }

    const withoutAccess = users.filter(
      user => !project.sharedWith?.includes(user.id) && user.id !== project.userId
    );

    setUsersWithAccess(withAccess);
    setUsersWithoutAccess(withoutAccess);

    setShowShareModal(true);
  };

  const shareProjectWithUser = async (userId) => {
    try {
      if (!selectedProject) return;

      const projectRef = doc(db, 'proyectos', selectedProject.id);

      await updateDoc(projectRef, {
        sharedWith: arrayUnion(userId)
      });

      console.log(`Proyecto ${selectedProject.nombreProyecto} compartido con el usuario ID: ${userId}`);

      const user = auth.currentUser;
      if (user) {
        await getProjects(user.uid);
      }

      setShowShareModal(false);
    } catch (error) {
      console.error('Error al compartir el proyecto: ', error);
      alert('Hubo un error al compartir el proyecto');
    }
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        getProjects(user.uid);
        getUsers(user.uid);
      } else {
        setLoading(false);
        console.log("No hay usuario autenticado.");
      }
    });
    return () => unsubscribe();
  }, [sortOrder]);

  if (loading) {
    return (
      <div id="loader">
        <div className="spinner"></div>
      </div>
    );
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
                  <div className="project-tile" onClick={() => navigate(`/project/${project.id}`)}>
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
                          <Dropdown.Item onClick={() => handleShareProject(project)}>
                            <MdShare style={{ marginRight: '5px' }} />
                            Compartir
                          </Dropdown.Item>
                          <Dropdown.Item onClick={() => handleDeleteProject(project.id)}>
                            <MdDelete style={{ marginRight: '5px' }} />
                            Eliminar
                          </Dropdown.Item>
                        </Dropdown.Menu>
                      </Dropdown>
                    </div>
                    <div className="d-flex align-items-center mb-2">
                      <MdAccessTime style={{ marginRight: '5px', color: '#888' }} />
                      <small className="text-muted">
                        Última actualización: {new Date(project.fechaCreacion).toLocaleDateString()}
                      </small>
                    </div>
                    {project.sharedWith && project.sharedWith.length > 0 && (
                      <div className="d-flex align-items-center mb-2">
                        <MdPeople style={{ marginRight: '5px', color: '#888' }} />
                        <small className="text-muted">Trabajo en equipo</small>
                      </div>
                    )}
                  </div>
                </Col>
              ))
            ) : (
              <p>No hay proyectos disponibles.</p>
            )}
          </Row>
        </Container>
      </div>

      {/* Modal de Confirmación de Eliminación */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirmación de Eliminación</Modal.Title>
        </Modal.Header>
        <Modal.Body>¿Estás seguro de que deseas eliminar este proyecto? Esta acción no se puede deshacer.</Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancelar
          </Button>
          <Button variant="danger" onClick={confirmDeleteProject}>
            Eliminar
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Modal de Compartir Proyecto */}
      <Modal show={showShareModal} onHide={() => setShowShareModal(false)} className="share-modal">
        <Modal.Header closeButton>
          <Modal.Title>Comparte tu proyecto con otros</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <h5>Usuarios con acceso:</h5>
          <div className="user-list">
            {usersWithAccess.length > 0 ? (
              usersWithAccess.map((user) => (
                <div className="user-item" key={user.id}>
                  <div className="d-flex align-items-center">
                    <MdAccountCircle size={20} style={{ marginRight: '8px', color: '#555' }} />
                    <span className="user-email">{user.email}</span>
                  </div>
                </div>
              ))
            ) : (
              <p>No hay usuarios con acceso.</p>
            )}
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowShareModal(false)}>
            Cancelar
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default MyProjects;
