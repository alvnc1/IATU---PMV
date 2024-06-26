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
import { useParams } from 'react-router-dom';

function ProjectPage() {
  const { id } = useParams();
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [sortOrder, setSortOrder] = useState('asc');
  const [testStatus, setTestStatus] = useState({});
  const navigate = useNavigate();

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

  const handleShowModal = (task) => {
    setSelectedTask(task);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setSelectedTask(null);
    setShowModal(false);
  };

  const handleTestRun = (taskId) => {
    setTestStatus(prevStatus => ({
      ...prevStatus,
      [taskId]: true
    }));
  };

  useEffect(() => {
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
          <h2 style={{ textAlign: "left", margin: 0 }}>Proyecto {id}</h2>
        </div>
        <div style={{ marginTop: '20px' }}>
          <Row>
            {tasks.map((task) => (
              <Col key={task.id} xs={12} sm={6} md={4} lg={3} className="mb-4">
                <Card className="project-card">
                  <Card.Img variant="top" src={require("./images/logo.png")} alt="Task Image" />
                  <Card.Body className="text-center">
                    <Card.Title>{task.nombreTarea}</Card.Title>
                    <Button variant="primary" onClick={() => handleShowModal(task)}>Ver Tarea</Button>
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
            <p><strong>Usuario:</strong> {getUserInfo(selectedTask.selectedOption)}</p>
            <p><strong>Descripción:</strong> {selectedTask.inputValue}</p>
            <div className="d-flex flex-column align-items-stretch">
              <Button variant="light" className="neutral-btn mb-2"><TestRunner task={selectedTask} /></Button>
              <Button variant="light" className="neutral-btn mb-2" disabled={!testStatus[selectedTask.id]}><CriteriaPDFGenerator task={selectedTask} /></Button>
              <Button variant="danger" className="danger-btn" onClick={() => deleteTask(selectedTask.id)}> <MdDelete /> Eliminar Tarea</Button>
            </div>
          </Modal.Body>
        </Modal>
      )}
    </div>
  );
}

export default ProjectPage;
