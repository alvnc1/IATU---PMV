import React, { useEffect, useState } from "react";
import Sidebar from "./sidebar"; 
import Container from "react-bootstrap/Container";
import Table from "react-bootstrap/Table";
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import { MdDelete } from "react-icons/md";
import { collection, getDocs, deleteDoc, doc, getDoc } from 'firebase/firestore';
import { db } from "./firebase";
import { useNavigate } from 'react-router-dom';
import { useParams } from 'react-router-dom';

function ProjectPage() {
  const { id } = useParams();
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [sortOrder, setSortOrder] = useState('asc');
  const [testStatus, setTestStatus] = useState({});
  const [projectName, setProjectName] = useState(''); 
  const navigate = useNavigate();

  const getProjectDetails = async () => {
    try {
      const projectDoc = await getDoc(doc(db, 'proyectos', id));
      if (projectDoc.exists()) {
        setProjectName(projectDoc.data().nombreProyecto);
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

  useEffect(() => {
    getProjectDetails(); 
    getTasks();
  }, []);

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <Container fluid style={{ marginLeft: '230px', padding: '20px', minHeight: '100vh', overflowY: 'auto', overflowX: 'hidden' }}>
        <div className="d-flex justify-content-between align-items-center">
          <h2 style={{ textAlign: "left", margin: 0 }}>Proyecto {projectName}</h2>
        </div>
        <div style={{ marginTop: '20px' }}>
          <Table striped bordered hover responsive className="rounded-table">
            <thead>
              <tr>
                <th>File name</th>
                <th>Uploaded</th>
                <th>Status</th>
                <th>Download</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task.id}>
                  <td className="text-truncate">{task.nombreTarea}</td>
                  <td>{new Date(task.fechaCreacion).toLocaleDateString()}</td>
                  <td>-</td>
                  <td>
                    <Button variant="outline-primary" className="me-2">PDF</Button>
                    <Button variant="outline-primary">Other</Button>
                  </td>
                  <td>
                    <Button 
                      variant="danger" 
                      onClick={() => deleteTask(task.id)} 
                      className="delete-button"
                    >
                      <MdDelete size={20} />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      </Container>

      {selectedTask && (
        <Modal show={showModal} onHide={handleCloseModal}>
          <Modal.Header closeButton>
            <Modal.Title>{selectedTask.nombreTarea}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <h5>Uploaded Files</h5>
            <div>
              {selectedTask.files && selectedTask.files.length > 0 ? (
                selectedTask.files.map((file) => (
                  <div key={file.id} style={{ marginBottom: '10px' }}>
                    <a href={file.url} target="_blank" rel="noopener noreferrer">{file.name}</a>
                  </div>
                ))
              ) : (
                <p>No files uploaded for this task.</p>
              )}
            </div>
          </Modal.Body>
        </Modal>
      )}
      <style>
        {`
          .rounded-table {
            border-radius: 10px;
            overflow: hidden;
          }

          .rounded-table th:first-child, 
          .rounded-table td:first-child {
            border-left: none;
          }

          .rounded-table th:last-child, 
          .rounded-table td:last-child {
            border-right: none;
          }

          .rounded-table th:first-child {
            border-top-left-radius: 10px;
          }

          .rounded-table th:last-child {
            border-top-right-radius: 10px;
          }

          .rounded-table tr:last-child td:first-child {
            border-bottom-left-radius: 10px;
          }

          .rounded-table tr:last-child td:last-child {
            border-bottom-right-radius: 10px;
          }

          .delete-button {
            background-color: transparent;
            border: none;
            padding: 0;
            margin: 0;
            cursor: pointer;
            color: red;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 30px;
            height: 30px;
            transition: background-color 0.3s ease;
          }

          .delete-button:hover {
            background-color: #f8d7da;
            border-radius: 50%;
          }
        `}
      </style>
    </div>
  );
}

export default ProjectPage;
