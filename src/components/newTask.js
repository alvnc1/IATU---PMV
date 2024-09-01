import React, { useState } from "react";
import Container from "react-bootstrap/Container";

function NewTask() {
    return (
        <div>
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

            </Container>
        </div>
    );
}

export default NewTask;
