// src/components/CriteriaPDFGenerator.js
import React, { useState } from "react";
import Button from 'react-bootstrap/Button';
import axios from 'axios';
import jsPDF from 'jspdf';

const CriteriaPDFGenerator = ({ project }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [criteria, setCriteria] = useState(null);

  const handleGeneratePDF = async () => {
    setIsLoading(true);

    try {
      // Realizar solicitud GET para obtener los criterios
      const response = await axios.get('http://localhost:3001/criteria');
      const criteriaData = response.data;

      // Establecer los criterios y la información del proyecto en el estado local
      setCriteria({
        project,
        criteria: criteriaData
      });

      // Generar el PDF con los criterios obtenidos y la información del proyecto
      generatePDF(project, criteriaData);

    } catch (error) {
      console.error('Error al obtener los criterios:', error);
      alert('Hubo un error al obtener los criterios');
    } finally {
      setIsLoading(false);
    }
  };

  // Función para generar el PDF con los criterios y la información del proyecto
  const generatePDF = (project, criteriaData) => {
    // Crear un nuevo documento PDF
    const doc = new jsPDF();

    // Título y contenido del PDF
    doc.text('Criterios del Proyecto', 10, 10);
    doc.setFontSize(12);

    // Información del proyecto
    doc.text(`Nombre del Proyecto: ${project.nombreProyecto}`, 10, 20);
    doc.text(`Descripción de la Prueba: ${project.inputValue}`, 10, 30);
    doc.text(`Sitio Web: ${project.webLink}`, 10, 40);

    // Criterios obtenidos
    doc.text('Criterios:', 10, 50);
    doc.text(JSON.stringify(criteriaData, null, 2), 10, 60);

    // Guardar el documento PDF como un archivo descargable
    doc.save('criterios.pdf');
  };

  return (
    <div>
      <Button onClick={handleGeneratePDF} disabled={isLoading}>
        {isLoading ? 'Generando PDF...' : 'Generar PDF con Criterios'}
      </Button>
      {criteria && (
        <div>
        </div>
      )}
    </div>
  );
};

export default CriteriaPDFGenerator;
