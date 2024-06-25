import React, { useState } from "react";
import Button from 'react-bootstrap/Button';
import axios from 'axios';
import jsPDF from 'jspdf';

const CriteriaPDFGenerator = ({ project, disabled }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [criteria, setCriteria] = useState(null);

  const handleGeneratePDF = async () => {
    setIsLoading(true);

    try {
      const response = await axios.get('http://localhost:3001/criteria');
      const criteriaData = response.data;

      setCriteria({
        project,
        criteria: criteriaData
      });

      generatePDF(project, criteriaData);

    } catch (error) {
      console.error('Error al obtener los criterios:', error);
      alert('Hubo un error al obtener los criterios');
    } finally {
      setIsLoading(false);
    }
  };

  const generatePDF = (project, criteriaData) => {
    const doc = new jsPDF();
    doc.text('Criterios del Proyecto', 10, 10);
    doc.setFontSize(12);

    doc.text(`Nombre del Proyecto: ${project.nombreProyecto}`, 10, 20);
    doc.text(`Descripción de la Prueba: ${project.inputValue}`, 10, 30);
    doc.text(`Sitio Web: ${project.webLink}`, 10, 40);

    doc.text('Criterios:', 10, 50);
    doc.text(JSON.stringify(criteriaData, null, 2), 10, 60);

    doc.save('criterios.pdf');
  };

  return (
    <div>
      <Button onClick={handleGeneratePDF} disabled={disabled || isLoading}>
        {isLoading ? 'Generando PDF...' : 'Generar Feedback'}
      </Button>
      {criteria && (
        <div>
        </div>
      )}
    </div>
  );
};

export default CriteriaPDFGenerator;
