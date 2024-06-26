import React, { useState } from "react";
import NavBar from "./navBar";
import "../login-register.css";
import { useNavigate } from 'react-router-dom';
import Container from "react-bootstrap/Container";
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import { db } from "./firebase";
import { doc, setDoc, collection } from "firebase/firestore";
import { useParams } from 'react-router-dom';

function NewTask() {
    const { id: projectId } = useParams(); // Obtener el ID del proyecto desde la URL
    const [selectedOption, setSelectedOption] = useState('');
    const [inputValue, setInputValue] = useState('');
    const [nombreTarea, setNombreTarea] = useState('');
    const [errors, setErrors] = useState({});
    const navigate = useNavigate(); // Crear instancia de useNavigate
    const [tipoInput, setTipoInput] = useState('enlace');
    const [webLink, setWebLink] = useState('');
    const [imagenFile, setImagenFile] = useState(null);

    const handleSelectChange = (e) => {
        setSelectedOption(e.target.value);
    };

    const handleWebLinkChange = (e) => {
        setWebLink(e.target.value);
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        setImagenFile(file);
    };

    const handleTipoInputChange = (e) => {
        setTipoInput(e.target.value);
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
        if (!selectedOption) errors.selectedOption = "Debe seleccionar un usuario.";
        if (!inputValue) errors.inputValue = "Debe definir la prueba a realizar.";

        setErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!validate()) {
            return;
        }

        try {
            // Verifica que projectId no esté vacío
            if (!projectId) {
                alert("Error: No se pudo obtener el ID del proyecto.");
                return;
            }

            // Objeto con los datos a guardar
            const tarea = {
                nombreTarea,
                selectedOption,
                inputValue,
                webLink
            };

            // Guardar documento en Firestore dentro de la colección tasks del proyecto específico
            const projectRef = doc(db, "proyectos", projectId);
            await setDoc(doc(collection(projectRef, "tasks"), Date.now().toString()), tarea);

            // Limpiar los campos después de guardar
            setSelectedOption('');
            setInputValue('');
            setNombreTarea('');

            // Mostrar los datos en la consola
            console.log("Tarea guardada en Firebase:", tarea);

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
                    width: "90%", // Ancho del contenedor interno
                    maxWidth: "1200px", // Ancho máximo del contenedor interno
                    height: "80vh", // Altura del contenedor interno
                    overflowY: "auto", // Scroll vertical si es necesario
                    boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)", // Sombra ligera
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

                <Form onSubmit={handleSubmit}>
                    <div className="d-flex justify-content-between align-items-center">
                        <h5 style={{ textAlign: "left", marginTop: '20px' }}>Recurso/s a Testear</h5>
                    </div>

                    <Form.Group controlId="formBasicTipoInput">
                        <Form.Label>Tipo de recurso</Form.Label>
                        <Form.Control as="select" value={tipoInput} onChange={handleTipoInputChange}>
                            <option value="enlace">Enlace Web</option>
                            <option value="imagen">Imagen</option>
                        </Form.Control>
                    </Form.Group>

                    {tipoInput === 'enlace' && (
                        <Form.Group style={{ marginTop: '10px' }} controlId="formBasicWebLink">
                            <Form.Control
                                type="text"
                                placeholder="Escribe el enlace de tu web..."
                                value={webLink}
                                onChange={handleWebLinkChange}
                            />
                        </Form.Group>
                    )}

                    {tipoInput === 'imagen' && (
                        <Form.Group controlId="formBasicImageUpload" style={{ marginTop: '10px' }}>
                            <Form.Control
                                type="file"
                                id="custom-file"
                                label="Selecciona un archivo"
                                custom
                                onChange={handleFileChange}
                            />
                        </Form.Group>
                    )}
                </Form>

                <div className="d-flex justify-content-between align-items-center">
                    <h5 style={{ textAlign: "left", marginTop: '20px' }}>Seleccione el usuario</h5>
                </div>
                <Form.Group controlId="formBasicDropdown">
                    <Form.Control 
                        as="select" 
                        value={selectedOption} 
                        onChange={handleSelectChange} 
                        isInvalid={!!errors.selectedOption}
                    >
                        <option value="">Seleccione...</option>
                        <option value="opcion1">Javier Sánchez, 32 años: Apasionado por la tecnología.</option>
                        <option value="opcion2">José Gómez, 68 años: Entusiasta del arte contemporáneo.</option>
                    </Form.Control>
                    <Form.Control.Feedback type="invalid">
                        {errors.selectedOption}
                    </Form.Control.Feedback>
                </Form.Group>

                <div className="d-flex justify-content-between align-items-center">
                    <h5 style={{ textAlign: "left", marginTop: '20px', marginBottom:'-10px' }}>Defina la prueba a realizar en lenguaje natural</h5>
                </div>
                <Form.Group controlId="formBasicText">
                    <Form.Label></Form.Label>
                    <Form.Control
                        type="text"
                        placeholder="Escriba en lenguaje natural la prueba a realizar..."
                        value={inputValue}
                        onChange={handleInputChange}
                        isInvalid={!!errors.inputValue}
                    />
                    <Form.Control.Feedback type="invalid">
                        {errors.inputValue}
                    </Form.Control.Feedback>
                </Form.Group>

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
