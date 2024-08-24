import React, { useState } from "react";
import NavBar from "./navBar"; 
import "../login-register.css";
import { useNavigate } from 'react-router-dom';
import Container from "react-bootstrap/Container";
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import { db, storage } from "./firebase"; 
import { doc, setDoc, collection } from "firebase/firestore";
import { getDownloadURL, ref, uploadBytes } from "firebase/storage"; 
import { useParams } from 'react-router-dom';

function NewTask() {
    const { id: projectId } = useParams(); 
    const [selectedOption, setSelectedOption] = useState('');
    const [inputValue, setInputValue] = useState('');
    const [nombreTarea, setNombreTarea] = useState('');
    const [errors, setErrors] = useState({});
    const navigate = useNavigate(); 
    const [files, setFiles] = useState([]);
    const [uploadStatus, setUploadStatus] = useState({});

    const handleSelectChange = (e) => {
        setSelectedOption(e.target.value);
    };

    const handleInputChange = (e) => {
        setInputValue(e.target.value);
    };

    const handleNombreTareaChange = (e) => {
        setNombreTarea(e.target.value);
    };

    const validate = () => {
        const errors = {};
        if (!nombreTarea) errors.nombreTarea = "El nombre de la tarea es obligatorio.";
        setErrors(errors);
        return Object.keys(errors).length === 0;
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

        if (!validate()) {
            return;
        }

        try {
            if (!projectId) {
                alert("Error: No se pudo obtener el ID del proyecto.");
                return;
            }

            const tarea = {
                nombreTarea,
                selectedOption,
                inputValue,
                files 
            };

            const projectRef = doc(db, "proyectos", projectId);
            await setDoc(doc(collection(projectRef, "tasks"), Date.now().toString()), tarea);

            setSelectedOption('');
            setInputValue('');
            setNombreTarea('');
            setFiles([]);

            alert("Tarea guardada correctamente!");
            navigate(`/project/${projectId}`)
        } catch (error) {
            console.error("Error al guardar la tarea en Firebase: ", error);
            alert("Hubo un error al guardar la tarea");
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
                    width: "90%", 
                    maxWidth: "1200px", 
                    height: "80vh", 
                    overflowY: "auto", 
                    boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)", 
                }}
            >
                <div className="d-flex justify-content-between align-items-center">
                    <h2 style={{ textAlign: "left", margin: 0 }}>Creación de Tarea</h2>
                </div>
                <hr
                    style={{
                        color: '#000000',
                        backgroundColor: '#000000',
                        height: 5
                    }}
                />

                <div className="d-flex justify-content-between align-items-center">
                    <h5 style={{ textAlign: "left", marginTop: '20px' }}>Nombre de la tarea</h5>
                </div>
                <Form.Group controlId="formBasicNombreTarea">
                    <Form.Control
                        type="text"
                        placeholder="Escribe el nombre de la tarea..."
                        value={nombreTarea}
                        onChange={handleNombreTareaChange}
                        isInvalid={!!errors.nombreTarea}
                    />
                    <Form.Control.Feedback type="invalid">
                        {errors.nombreTarea}
                    </Form.Control.Feedback>
                </Form.Group>

                <div className="d-flex justify-content-between align-items-center" style={{ marginTop: '20px' }}>
                    <h5 style={{ textAlign: "left", marginTop: '20px' }}>Subir Archivos</h5>
                </div>
                <div
                    style={{
                        border: '2px dashed #ccc',
                        borderRadius: '10px',
                        padding: '20px',
                        textAlign: 'center',
                        marginBottom: '20px'
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
                        Drag&Drop your files here or <span style={{ color: '#007bff', textDecoration: 'underline' }}>browse</span> to upload.
                    </label>
                </div>

                <div>
                    <h5>Archivos Subidos</h5>
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
                </div>

                <div style={{ display: 'flex', justifyContent: 'center', marginTop: '50px' }}>
                    <Button variant="primary" onClick={handleSubmit}>
                        Guardar tarea
                    </Button>
                </div>
            </Container>
        </div>
    );
}

export default NewTask;
