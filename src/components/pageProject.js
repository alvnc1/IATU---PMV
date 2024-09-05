import React, { useEffect, useState } from "react";
import Sidebar from "./sidebar"; 
import Container from "react-bootstrap/Container";
import Table from "react-bootstrap/Table";
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import { MdDelete, MdPlayArrow, MdAdd } from "react-icons/md";
import { collection, getDocs, deleteDoc, doc, getDoc } from 'firebase/firestore';
import { db } from "./firebase";
import { useNavigate } from 'react-router-dom';
import { useParams } from 'react-router-dom';
import './css/projectPage.css';

function ProjectPage() {
  const { id } = useParams();
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [sortOrder, setSortOrder] = useState('asc');
  const [testStatus, setTestStatus] = useState({});
  const [projectName, setProjectName] = useState(''); 
  const [isLoading, setIsLoading] = useState(false);
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

    const initialStatus = {};
    tasksList.forEach(task => {
      initialStatus[task.id] = testStatus[task.id] || 'Pendiente';
    });
    setTestStatus(initialStatus);
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

  const handleAddTask = () => {
    navigate(`/newTask/${id}`);
  };

  // Función para descargar el PDF
  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = process.env.PUBLIC_URL + '/informe.pdf';  // Ruta al PDF en el directorio 'public'
    link.setAttribute('download', 'informe.pdf');  // Nombre con el que se descargará
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  const handlePlayTask = (taskId) => {
    setIsLoading(true);

    const videoUrl = taskId.files.find(file => file.url).url;
    const urlTarea = taskId.urlTarea;
    const categorias = taskId.categorias;
    console.log(videoUrl);
    console.log(urlTarea);
    console.log(categorias);

    // Verificar que todos los valores están presentes
    if (!videoUrl || !urlTarea || !categorias) {
      setIsLoading(false);
      return alert('Faltan datos para ejecutar el análisis');
    }

    setTestStatus(prevStatus => ({
      ...prevStatus,
      [taskId.id]: 'Ejecutando'
    }));

    fetch('http://localhost:3001/run-python', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ videoUrl, urlTarea, categorias })
    })
    .then(response => response.json())
    .then(data => {
      console.log('Respuesta del servidor:', data);
      //alert('Análisis de video completado');

      setTestStatus(prevStatus => ({
        ...prevStatus,
        [taskId.id]: 'Finalizado'
      }));
    })
    .catch(error => {
      console.error('Error al ejecutar el script de Python:', error);
      //alert('Error al analizar el video');

      setTestStatus(prevStatus => ({
        ...prevStatus,
        [taskId.id]: 'Error'
      }));
    })
    .finally(() => {
      setIsLoading(false);
    });
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
          <h2 className="page-title">Proyecto {projectName}</h2>
          <Button variant="outline-primary" className="d-flex align-items-center add-button" onClick={handleAddTask}>
            <MdAdd size={20} style={{ marginRight: '5px'}} />
            Agregar
          </Button>
        </div>

        {/*isLoading && (
          <div className="progress-bar-container">
            <div className="progress-bar">
              <span className="progress-bar-text">Cargando...</span>
            </div>
          </div>
        )*/}

        <div style={{ marginTop: '20px' }}>
          <Table striped bordered hover responsive className="rounded-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Subido</th>
                <th>Estado</th>
                <th>Descarga</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task.id}>
                  <td className="text-truncate">{task.nombreTarea}</td>
                  <td>{new Date(task.fechaCreacion).toLocaleDateString()}</td>
                  <td>{testStatus[task.id] || 'Pendiente'}</td>
                  <td>
                      <Button
                        variant="outline-primary"
                        onClick={handleDownload}
                        className="me-2 pdf-button">
                        PDF
                      </Button>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <Button 
                        variant="success" 
                        onClick={() => handlePlayTask(task)}  
                        className="play-button"
                      >
                        <MdPlayArrow size={20} />
                      </Button>
                      <Button 
                        variant="danger" 
                        onClick={() => deleteTask(task.id)} 
                        className="delete-button"
                      >
                        <MdDelete size={20} />
                      </Button>
                    </div>
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
    </div>
  );
}

export default ProjectPage;
