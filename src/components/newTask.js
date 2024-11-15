import React, { useState } from "react";
import { useNavigate, useParams } from 'react-router-dom';
import Container from "react-bootstrap/Container";
import Sidebar from "./sidebar"; 
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import { MdSave } from "react-icons/md";
import { db, storage } from "./firebase"; 
import { doc, setDoc, collection } from "firebase/firestore";
import { getDownloadURL, ref, uploadBytes } from "firebase/storage";
import './css/tasks.css';

function NewTask() {
    const { id: projectId } = useParams(); 
    const [nombreTarea, setNombreTarea] = useState('');
    const [urlTarea, setUrlTarea] = useState('');
    const [selectedCategorias, setSelectedCategorias] = useState([]);
    const [files, setFiles] = useState([]);
    const [uploadStatus, setUploadStatus] = useState({});
    const navigate = useNavigate();
    const [openCategory, setOpenCategory] = useState(null); // Controlar qué categoría principal está expandida

    const categorias = {
        Usabilidad: [
            "Página de Inicio",
            "Orientación de Tareas",
            "Navegabilidad",
            "Formularios",
            "Confianza y Credibilidad",
            "Calidad del Contenido",
            "Diagramación y Diseño",
            "Sección de Búsquedas",
            "Sección de Reconocimiento de Errores y Retroalimentación"
        ],
        "Adultos Mayores": [
            "Retroalimentacion de Acciones",
            "Facilidad de Navegacion",
            "Legibilidad del Texto",
            "Interaccion con Elementos Clickables",
            "Cognitiva y Organizacion Visual",
            "Ayuda Contextual"
        ],
        Accesibilidad: [
            "Validación de Accesibilidad Visual",
            "Validación de Accesibilidad Cognitiva",
            "Validación de Accesibilidad Motora"
        ]
    };

    const handleNombreTareaChange = (e) => {
        setNombreTarea(e.target.value);
    };

    const handleUrlTareaChange = (e) => {
        setUrlTarea(e.target.value);
    };

    const handleCategoriaChange = (categoria) => {
        setSelectedCategorias(prevSelected => {
            if (prevSelected.includes(categoria)) {
                return prevSelected.filter(c => c !== categoria);
            } else {
                return [...prevSelected, categoria];
            }
        });
    };

    const toggleCategory = (category) => {
        setOpenCategory(openCategory === category ? null : category);
    };

    const renderCategoriasMenu = () => (
        <Dropdown>
            <Dropdown.Toggle variant="outline-secondary" id="dropdown-basic">
                Selecciona las categorías
            </Dropdown.Toggle>
            <Dropdown.Menu>
                {Object.keys(categorias).map((key) => (
                    <div key={key}>
                        <Dropdown.ItemText onClick={() => toggleCategory(key)} style={{ cursor: "pointer" }}>
                            {key}
                        </Dropdown.ItemText>
                        {openCategory === key && (
                            <div style={{ marginLeft: '20px' }}>
                                {categorias[key].map((subItem) => (
                                    <Form.Check
                                        type="checkbox"
                                        label={subItem}
                                        key={subItem}
                                        checked={selectedCategorias.includes(subItem)}
                                        onChange={() => handleCategoriaChange(subItem)}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </Dropdown.Menu>
        </Dropdown>
    );

    const handleFileUpload = async (file) => {
        const fileId = Date.now().toString();
        setUploadStatus(prevStatus => ({
            ...prevStatus,
            [fileId]: 'uploading'
        }));

        try {
            const storageRef = ref(storage, `uploads/${fileId}_${file.name}`);
            await uploadBytes(storageRef, file);
            const downloadUrl = await getDownloadURL(storageRef);

            setFiles(prevFiles => [...prevFiles, { id: fileId, name: file.name, url: downloadUrl }]);
            setUploadStatus(prevStatus => ({
                ...prevStatus,
                [fileId]: 'success'
            }));
        } catch (error) {
            setUploadStatus(prevStatus => ({
                ...prevStatus,
                [fileId]: 'error'
            }));
        }
    };

    const handleFilesChange = (e) => {
        const filesArray = Array.from(e.target.files);
        filesArray.forEach(file => handleFileUpload(file));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (nombreTarea || urlTarea || files.length > 0) {
                const taskId = Date.now().toString();
                const tareaRef = doc(collection(db, `proyectos/${projectId}/tasks`), taskId);
                const tareaData = {
                    nombreTarea,
                    urlTarea,
                    categorias: selectedCategorias,
                    fechaCreacion: new Date().toISOString(),
                    files
                };
                await setDoc(tareaRef, tareaData);
            }
            setNombreTarea('');
            setUrlTarea('');
            setSelectedCategorias([]);
            setFiles([]);
            navigate(`/project/${projectId}`);
        } catch (error) {
            console.error("Error al guardar la tarea en Firebase: ", error);
            alert("Hubo un error al guardar la tarea");
        }
    };

    return (
        <div style={{ display: 'flex' }}>
            <Sidebar />
            <div style={{ marginLeft: '250px', width: '100%' }}>
                <Container
                    style={{
                        marginTop: "20px",
                        backgroundColor: "white",
                        borderRadius: "10px",
                        padding: "20px",
                        width: "90%", 
                        maxWidth: "1200px", 
                        height: "auto", 
                        overflowY: "auto", 
                        boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)", 
                    }}
                >
                    <div className="d-flex justify-content-between align-items-center">
                        <h2 style={{ textAlign: "left", margin: 0 }}>Nueva Tarea</h2>
                        <div>
                            <Button variant="primary" onClick={handleSubmit}>
                                <MdSave size={18} style={{ marginRight: '5px'}} />
                                Guardar
                            </Button>
                        </div>
                    </div>
                    <hr style={{ color: '#000000', backgroundColor: '#000000', height: 2 }} />

                    <Form onSubmit={handleSubmit}>
                        <Form.Group controlId="formBasicNombreTarea">
                            <Form.Label style={{ fontWeight: 'bold', marginTop: '20px' }}>Nombre de la Tarea</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="Escribe el nombre de la tarea..."
                                value={nombreTarea}
                                onChange={handleNombreTareaChange}
                            />
                        </Form.Group>

                        <Form.Group controlId="formBasicCategoriaTareas">
                            <Form.Label style={{ fontWeight: 'bold', marginTop: '20px' }}>Categoría de la Tarea</Form.Label>
                            {renderCategoriasMenu()}
                        </Form.Group>

                        <Form.Group controlId="formBasicUrlTarea">
                            <Form.Label style={{ fontWeight: 'bold', marginTop: '20px' }}>URL de la Tarea</Form.Label>
                            <Form.Control
                                type="url"
                                placeholder="Ingresa la URL relacionada con la tarea..."
                                value={urlTarea}
                                onChange={handleUrlTareaChange}
                            />
                        </Form.Group>

                        <Form.Group controlId="formBasicFiles">
                            <Form.Label style={{ fontWeight: 'bold', marginTop: '20px' }}>Subir Archivos de la Tarea</Form.Label>
                            <div
                                style={{
                                    border: '2px dashed #ccc',
                                    borderRadius: '10px',
                                    padding: '20px',
                                    textAlign: 'center',
                                    marginBottom: '20px',
                                    height: '180px',
                                    display: 'flex',
                                    justifyContent: 'center',
                                    alignItems: 'center'
                                }}
                                onDrop={(e) => {
                                    e.preventDefault();
                                    handleFilesChange(e);
                                }}
                                onDragOver={(e) => e.preventDefault()}
                            >
                                <input
                                    type="file"
                                    multiple
                                    onChange={handleFilesChange}
                                    style={{ display: 'none' }}
                                    id="fileUpload"
                                />
                                <label htmlFor="fileUpload" style={{ cursor: 'pointer' }}>
                                    Arrastra y suelta tus archivos aquí o <span style={{ color: '#007bff', textDecoration: 'underline' }}>explora</span> para subir.
                                </label>
                            </div>
                        </Form.Group>

                        <Form.Group controlId="formBasicUploadedFiles">
                            <Form.Label style={{ fontWeight: 'bold', marginTop: '20px' }}>Archivos Subidos</Form.Label>
                            {files.map((file) => (
                                <div key={file.id} style={{ marginBottom: '10px' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <span>{file.name}</span>
                                        {uploadStatus[file.id] === 'uploading' && <span>Cargando...</span>}
                                        {uploadStatus[file.id] === 'success' && <span style={{ color: 'green' }}>Subido</span>}
                                        {uploadStatus[file.id] === 'error' && <span style={{ color: 'red' }}>Error al subir</span>}
                                    </div>
                                </div>
                            ))}
                        </Form.Group>
                    </Form>
                </Container>
            </div>
        </div>
    );
}

export default NewTask;
