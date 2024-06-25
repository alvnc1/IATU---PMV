import React, { useState } from "react";
import NavBar from "./navBar";
import "../login-register.css";
import Container from "react-bootstrap/Container";
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import { db } from "./firebase";
import { doc, setDoc, collection } from "firebase/firestore";
import { useParams } from 'react-router-dom';

function NewTask() {
    const projectId = useParams(); // Obtener el ID del proyecto desde la URL
    const [selectedOption, setSelectedOption] = useState('');
    const [inputValue, setInputValue] = useState('');
    const [nombreTarea, setnombreTarea] = useState('');

    const handleSelectChange = (e) => {
        setSelectedOption(e.target.value);
    };

    const handleInputChange = (e) => {
        setInputValue(e.target.value);
    };


    const handleNombreTareaChange = (e) => {
        setnombreTarea(e.target.value);
    };

    console.log("ID", projectId);
    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            // Objeto con los datos a guardar
            const tarea = {
                nombreTarea
            };

            // Guardar documento en Firestore dentro de la colección tasks del proyecto específico
            const projectRef = doc(db, "proyectos", projectId);
            await setDoc(doc(collection(projectRef, "tasks"), Date.now().toString()), tarea);

            // Limpiar los campos después de guardar
            setSelectedOption('');
            setInputValue('');

            // Mostrar los datos en la consola
            console.log("Tarea guardada en Firebase:", tarea);

            alert("Tarea guardada correctamente!");
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
                <Form.Group controlId="formBasicNombreProyecto">
                        <Form.Control
                            type="text"
                            placeholder="Escribe el nombre del proyecto..."
                            value={nombreTarea}
                            onChange={handleNombreTareaChange}
                        />
                    </Form.Group>
                
                <div className="d-flex justify-content-between align-items-center">
                    <h5 style={{ textAlign: "left", marginTop: '20px' }}>Seleccione el usuario</h5>
                </div>
                <Form.Group controlId="formBasicDropdown">
                    <Form.Control as="select" value={selectedOption} onChange={handleSelectChange}>
                        <option value="">Seleccione...</option>
                        <option value="opcion1">Javier Sánchez, 32 años: Apasionado por la tecnología.</option>
                        <option value="opcion2">José Gómez, 68 años: Entusiasta del arte contemporáneo.</option>
                    </Form.Control>
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
                    />
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
