import React, { useEffect, useState } from "react";
import Sidebar from "./sidebar"; 
import Container from "react-bootstrap/Container";
import Table from "react-bootstrap/Table";
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import { MdDelete, MdPlayArrow, MdAdd, MdVideoLibrary } from "react-icons/md";
import { collection, getDocs, deleteDoc, doc, getDoc, updateDoc } from 'firebase/firestore';
import { db } from "./firebase";
import { useNavigate } from 'react-router-dom';
import { useParams } from 'react-router-dom';
import './css/projectPage.css';

function ProjectPage() {
  const { id } = useParams();
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [videoUrl, setVideoUrl] = useState(''); // Nuevo estado para la URL del video
  const [showVideoModal, setShowVideoModal] = useState(false); // Nuevo estado para controlar la visibilidad del modal de video
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

  const handlePlayTask = (task) => {
    setIsLoading(true);
  
    const videoUrl = task.files.find(file => file.url).url;
    const urlTarea = task.urlTarea;
    const categorias = task.categorias;
    const idT = task.id;
    const idP = id;
    console.log(videoUrl);
    console.log(urlTarea);
    console.log(categorias);
    console.log(task.id);
  
    if (!videoUrl || !urlTarea || !categorias) {
      setIsLoading(false);
      return alert('Faltan datos para ejecutar el análisis');
    }
  
    setTestStatus(prevStatus => ({
      ...prevStatus,
      [task.id]: 'Ejecutando'
    }));
  
    fetch('http://localhost:3001/run-python', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ videoUrl, urlTarea, categorias, idT, idP })
    })
    .then(response => response.json())
    .catch(error => {
      console.error('Error al ejecutar el script de Python:', error);
      setTestStatus(prevStatus => ({
        ...prevStatus,
        [task.id]: 'Error'
      }));
    })
    .finally(() => {
      setIsLoading(false);
    });
  };

  // Función para manejar la descarga del PDF
  const handleDownloadPDF = (pdfUrl, taskId) => {
    if (!pdfUrl) return;
  
    // Crear un enlace temporal para forzar la descarga
    const link = document.createElement('a');
    link.href = pdfUrl;
  
    // Abrir en una nueva ventana o pestaña
    link.target = '_blank';

    // Forzar la descarga del archivo utilizando el atributo 'download'
    link.setAttribute('download', `${taskId}_informe.pdf`);
  
    // Añadir el enlace al DOM y simular el clic para iniciar la descarga
    document.body.appendChild(link);
    link.click();
  
    // Eliminar el enlace después de que se haya descargado el archivo
    document.body.removeChild(link);
  };
  

  // Maneja la reproducción del video
  const handleShowVideoModal = (task) => {
    const videoFile = task.files.find(file => file.url);
    if (videoFile) {
      setVideoUrl(videoFile.url);
      setShowVideoModal(true);
    } else {
      alert('No se encontró la URL del video.');
    }
  };

  const handleCloseVideoModal = () => {
    setShowVideoModal(false);
    setVideoUrl('');
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
                  <td>{testStatus[task.id]}</td>
                  <td>
                    <Button
                      variant="outline-primary"
                      onClick={() => handleDownloadPDF(task.pdfUrl)}
                      className="me-2 pdf-button"
                      disabled={!task.pdfUrl}  // Deshabilitar el botón si no hay pdfUrl
                    >
                      PDF
                    </Button>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <Button variant="success" onClick={() => handlePlayTask(task)} className="play-button">
                        <MdPlayArrow size={20} />
                      </Button>
                      <Button variant="success" onClick={() => handleShowVideoModal(task)} className="play-button">
                        <MdVideoLibrary size={20} />
                      </Button>
                      <Button variant="danger" onClick={() => deleteTask(task.id)} className="delete-button">
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

      <Modal show={showVideoModal} onHide={handleCloseVideoModal} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Reproducir Video</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {videoUrl ? (
            <div className="embed-responsive embed-responsive-16by9">
              <iframe
                src={videoUrl}
                title="Video"
                width="100%"
                height="400px"
                allowFullScreen
                frameBorder="0"
              ></iframe>
            </div>
          ) : (
            <p>No se encontró la URL del video.</p>
          )}
        </Modal.Body>
      </Modal>
    </div>
  );
}

export default ProjectPage;
