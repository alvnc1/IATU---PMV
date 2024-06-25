import React, { useState } from "react";
import NavBar from "./navBar";
import "../login-register.css";
import Container from "react-bootstrap/Container";
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import { db } from "./firebase";
import { doc, setDoc } from "firebase/firestore";


function NewProject() {
    const [selectedOption, setSelectedOption] = useState('');
    const [inputValue, setInputValue] = useState('');
    const [tipoInput, setTipoInput] = useState('enlace');
    const [webLink, setWebLink] = useState('');
    const [imagenFile, setImagenFile] = useState(null);
    const [nombreProyecto, setNombreProyecto] = useState('');
    const [descripcionProyecto, setDescripcionProyecto] = useState('');

    const handleSelectChange = (e) => {
        setSelectedOption(e.target.value);
    };

    const handleInputChange = (e) => {
        setInputValue(e.target.value);
    };

    const handleTipoInputChange = (e) => {
        setTipoInput(e.target.value);
    };

    const handleWebLinkChange = (e) => {
        setWebLink(e.target.value);
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        setImagenFile(file);
    };

    const handleNombreProyectoChange = (e) => {
        setNombreProyecto(e.target.value);
    };

    const handleDescripcionProyectoChange = (e) => {
        setDescripcionProyecto(e.target.value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            // Objeto con los datos a guardar
            const proyecto = {
                nombreProyecto,
                descripcionProyecto,
                fechaCreacion: new Date().toISOString() // Guardar la fecha de creación en formato ISO
            };

            // Guardar documento en Firestore
            await setDoc(doc(db, "proyectos", Date.now().toString()), proyecto);

            // Limpiar los campos después de guardar
            setSelectedOption('');
            setInputValue('');
            setTipoInput('enlace');
            setWebLink('');
            setImagenFile(null);
            setNombreProyecto('');

            // Mostrar los datos en la consola
            console.log("Datos guardados en Firebase:", proyecto);

            alert("Proyecto guardado correctamente!");
        } catch (error) {
            console.error("Error al guardar proyecto en Firebase: ", error);
            alert("Hubo un error al guardar el proyecto");
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
                    <h2 style={{ textAlign: "left", margin: 0 }}>Creación de Proyecto</h2>
                </div>
                <hr
                    style={{
                        color: '#000000',
                        backgroundColor: '#000000',
                        height: 5
                    }}
                />
                <div className="d-flex justify-content-between align-items-center">
                    <h5 style={{ textAlign: "left", marginTop: '20px' }}>Nombre del Proyecto</h5>
                </div>
                <Form.Group controlId="formBasicNombreProyecto">
                        <Form.Control
                            type="text"
                            placeholder="Escribe el nombre del proyecto..."
                            value={nombreProyecto}
                            onChange={handleNombreProyectoChange}
                        />
                    </Form.Group>

                <div className="d-flex justify-content-between align-items-center">
                <h5 style={{ textAlign: "left", marginTop: '20px' }}>Descripción del Proyecto</h5>
                </div>
                    <Form.Group controlId="formBasicDescripcionProyecto">
                        <Form.Control
                            type="text"
                            placeholder="Da una breve descripción del proyecto..."
                            value={descripcionProyecto}
                            onChange={handleDescripcionProyectoChange}
                        />
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
                            <Form.Control type="file" id="custom-file"
                                label="Selecciona un archivo"
                                custom
                                onChange={handleFileChange} />

                        </Form.Group>
                    )}


                    <div style={{ display: 'flex', justifyContent: 'center', marginTop: '50px' }}>
                        <Button variant="primary" type="submit">
                            Guardar Proyecto
                        </Button>
                    </div>
                </Form>
            </Container>
        </div>

    );
}

export default NewProject;
