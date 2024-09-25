import React, { useState } from "react";
import { useNavigate } from 'react-router-dom';
import Sidebar from "./sidebar"; 
import Container from "react-bootstrap/Container";
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import DropdownButton from 'react-bootstrap/DropdownButton';
import { MdSave } from "react-icons/md";
import { db, storage } from "./firebase"; 
import { doc, setDoc, collection } from "firebase/firestore";
import { getDownloadURL, ref, uploadBytes } from "firebase/storage"; 
import { getAuth } from "firebase/auth";

function NewProject() {
    const [nombreProyecto, setNombreProyecto] = useState('');
    const [descripcionProyecto, setDescripcionProyecto] = useState('');
    const [nombreTarea, setNombreTarea] = useState('');
    const [urlTarea, setUrlTarea] = useState('');  
    const [files, setFiles] = useState([]);
    const [uploadStatus, setUploadStatus] = useState({});
    const [selectedCategorias, setSelectedCategorias] = useState([]);
    const navigate = useNavigate();

    const auth = getAuth();  // Inicializamos Firebase Auth

    const categorias = [
        "Página de Inicio",
        "Orientación de Tareas",
        "Navegabilidad",
        "Formularios",
        "Confianza y Credibilidad",
        "Calidad del Contenido",
        "Diagramación y Diseño",
        "Sección de Búsquedas",
        "Sección de Reconocimiento de Errores y Retroalimentación"
    ];

    const handleNombreProyectoChange = (e) => {
        setNombreProyecto(e.target.value);
    };

    const handleDescripcionProyectoChange = (e) => {
        setDescripcionProyecto(e.target.value);
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
            const user = auth.currentUser;  // Obtener el usuario autenticado
            if (!user) {
                alert("Usuario no autenticado.");
                return;
            }

            const userId = user.uid;  // Obtener el UID del usuario
            const proyectoRef = doc(collection(db, "proyectos"));

            const proyectoData = {
                nombreProyecto,
                descripcionProyecto,
                fechaCreacion: new Date().toISOString(),
                userId // Almacenamos el UID del usuario junto con los datos del proyecto
            };

            await setDoc(proyectoRef, proyectoData);

            // Luego crear y guardar la tarea dentro del proyecto recién creado
            if (nombreTarea || urlTarea || files.length > 0) {
                const tareaRef = doc(collection(proyectoRef, "tasks"));
                const tareaData = {
                    nombreTarea,
                    urlTarea,
                    categorias: selectedCategorias,
                    fechaCreacion: new Date().toISOString(),
                    files
                };
                await setDoc(tareaRef, tareaData);
            }

            // Limpiar los estados después de guardar
            setNombreProyecto('');
            setDescripcionProyecto('');
            setNombreTarea('');
            setUrlTarea(''); 
            setSelectedCategorias([]);
            setFiles([]);

            alert("Proyecto y tarea guardados correctamente!");
            navigate('/projects');
        } catch (error) {
            console.error("Error al guardar proyecto y tarea en Firebase: ", error);
            alert("Hubo un error al guardar el proyecto y la tarea");
        }
    };

    return (
        <div style={{ display: 'flex' }}>
            <Sidebar />

            <div style={{ marginLeft: '250px', width: '100%' }}>
                <Container
                    fluid
                    style={{
                        marginTop: "20px",
                        backgroundColor: "white",
                        borderRadius: "10px",
                        padding: "20px",
                        width: "95%", 
                        maxWidth: "1200px",
                        height: "auto",
                        overflowY: "auto",
                        boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
                    }}
                >
                    <div className="d-flex justify-content-between align-items-center">
                        <h2 style={{ textAlign: "left", margin: 0 }}>Nuevo Proyecto</h2>
                        <div>
                            <Button variant="primary" onClick={handleSubmit}>
                                <MdSave size={18} style={{ marginRight: '5px'}} />
                                Guardar
                            </Button>
                        </div>
                    </div>
                    <hr style={{ color: '#000000', backgroundColor: '#000000', height: 2 }} />
                    
                    <Form onSubmit={handleSubmit}>
                        <Form.Group controlId="formBasicNombreProyecto">
                            <Form.Label style={{ fontWeight: 'bold', marginTop: '20px' }}>Nombre del Proyecto</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="Escribe el nombre del proyecto..."
                                value={nombreProyecto}
                                onChange={handleNombreProyectoChange}
                            />
                        </Form.Group>

                        <Form.Group controlId="formBasicDescripcionProyecto">
                            <Form.Label style={{ fontWeight: 'bold', marginTop: '20px' }}>Descripción del Proyecto</Form.Label>
                            <Form.Control
                                as="textarea"
                                rows={3}
                                placeholder="Da una breve descripción del proyecto..."
                                value={descripcionProyecto}
                                onChange={handleDescripcionProyectoChange}
                            />
                        </Form.Group>

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
                            <DropdownButton id="dropdown-basic-button" title="Selecciona las categorías" variant="outline-secondary">
                                {categorias.map((categoria) => (
                                    <Dropdown.Item key={categoria} as="button">
                                        <Form.Check
                                            type="checkbox"
                                            label={categoria}
                                            checked={selectedCategorias.includes(categoria)}
                                            onChange={() => handleCategoriaChange(categoria)}
                                        />
                                    </Dropdown.Item>
                                ))}
                            </DropdownButton>
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
                                    height: '200px',
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

export default NewProject;
