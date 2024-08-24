import React, { useEffect, useState } from "react";
import NavBar from "./navBar"; 
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Button from 'react-bootstrap/Button';
import Card from 'react-bootstrap/Card';
import Modal from 'react-bootstrap/Modal';
import { MdDelete } from "react-icons/md";
import { collection, getDocs, deleteDoc, doc, getDoc } from 'firebase/firestore';
import { db } from "./firebase";
import TestRunner from './testRunner';
import CriteriaPDFGenerator from './CriteriaPDFGenerator'; 
import ImageFeedbackGenerator from './ImageFeedbackGenerator'; 
import './MyProjects.css'; 
import { useNavigate } from 'react-router-dom';
import { useParams } from 'react-router-dom';

function ProjectPage() {
  const { id } = useParams();
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [sortOrder, setSortOrder] = useState('asc');
  const [testStatus, setTestStatus] = useState({});
  const [projectName, setProjectName] = useState(''); // Nuevo estado para el nombre del proyecto
  const navigate = useNavigate();

  const getProjectDetails = async () => {
    try {
      const projectDoc = await getDoc(doc(db, 'proyectos', id));
      if (projectDoc.exists()) {
        setProjectName(projectDoc.data().nombreProyecto); // Asigna el nombre del proyecto al estado
      } else {
        console.log("El documento no existe.");
      }
    } catch (error) {
      console.error("Error al obtener el proyecto: ", error);
    }
  };

  const getTasks = async () => {
    const tasksCollection = collection(db, 'proyectos', id, 'tasks');
    const snapshot = await getDocs(tasksCollection);
    const tasksList = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    tasksList.sort((a, b) => {
      if (sortOrder === 'asc') {
        return new Date(a.fechaCreacion) - new Date(b.fechaCreacion);
      } else {
        return new Date(b.fechaCreacion) - new Date(a.fechaCreacion);
      }
    });
    setTasks(tasksList);
    const initialTestStatus = {};
    tasksList.forEach(task => {
      initialTestStatus[task.id] = false;
    });
    setTestStatus(initialTestStatus);
  };

  const deleteTask = async (taskId) => {
    try {
      await deleteDoc(doc(db, 'proyectos', id, 'tasks', taskId));
      getTasks();
      alert('Tarea eliminada correctamente');
    } catch (error) {
      console.error('Error al eliminar la tarea: ', error);
      alert('Hubo un error al eliminar la tarea');
    }
  };

  const handleShowModal = (task) => {
    setSelectedTask(task);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setSelectedTask(null);
    setShowModal(false);
  };

  const handleTestRun = async (taskId) => {
    try {
      await new Promise(resolve => setTimeout(resolve, 2000));
      setTestStatus(prevStatus => ({
        ...prevStatus,
        [taskId]: true
      }));
    } catch (error) {
      console.error('Error al ejecutar la prueba: ', error);
      alert('Hubo un error al ejecutar la prueba');
    }
  };

  useEffect(() => {
    getProjectDetails(); 
    getTasks();
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
          <h2 style={{ textAlign: "left", margin: 0 }}>Proyecto: {projectName}</h2>
        </div>
        <div style={{ marginTop: '20px' }}>
          <Row>
            {tasks.map((task) => (
              <Col key={task.id} xs={12} sm={6} md={4} lg={3} className="mb-4">
                <Card className="project-card">
                <Card.Img variant="top" src={require("./images/bk.png")} alt="Project Image" />
                  <Card.Body className="text-center">
                    <Card.Title>{task.nombreTarea}</Card.Title>
                    <div className="d-flex justify-content-center">
                      <Button variant="primary" className="mb-2 feed-btn" onClick={() => handleShowModal(task)}>Ver Tarea</Button>
                      <Button variant="danger" className="danger-btn mb-2" onClick={() => deleteTask(task.id)}>
                        <MdDelete size={24} />
                      </Button>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            ))}
            <Col xs={12} sm={6} md={4} lg={3} className="mb-4">
              <Card className="h-100 d-flex justify-content-center align-items-center">
                <Button href={`/newtask/${id}`} variant="outline-primary" className="w-100 h-100">
                  + Nueva Tarea
                </Button>
              </Card>
            </Col>
          </Row>
        </div>
      </Container>

      {selectedTask && (
        <Modal show={showModal} onHide={handleCloseModal}>
          <Modal.Header closeButton>
            <Modal.Title>{selectedTask.nombreTarea}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <h5>Archivos Subidos</h5>
            <div>
              {selectedTask.files && selectedTask.files.length > 0 ? (
                selectedTask.files.map((file) => (
                  <div key={file.id} style={{ marginBottom: '10px' }}>
                    <a href={file.url} target="_blank" rel="noopener noreferrer">{file.name}</a>
                  </div>
                ))
              ) : (
                <p>No se han subido archivos para esta tarea.</p>
              )}
            </div>
            <div className="d-flex flex-column align-items-stretch">
              {selectedTask.imageUrl && (
                <>
                  <img src={selectedTask.imageUrl} alt="Task Image" style={{ width: '100%', marginBottom: '10px' }} />
                  <ImageFeedbackGenerator imageUrl={selectedTask.imageUrl} />
                </>
              )}
              {!selectedTask.imageUrl && (
                <>
                  <Button
                    variant="light"
                    className="neutral-btn mb-2"
                    onClick={() => handleTestRun(selectedTask.id)}
                    disabled={testStatus[selectedTask.id]}
                  >
                    <TestRunner task={selectedTask} onTestRun={() => handleTestRun(selectedTask.id)} />
                  </Button>
                  <Button variant="light" className="feed-btn mb-2" disabled={!testStatus[selectedTask.id]}>
                    <CriteriaPDFGenerator task={selectedTask} />
                  </Button>
                </>
              )}
            </div>
          </Modal.Body>
        </Modal>
      )}
    </div>
  );
}

export default ProjectPage;
