import React, { useState } from "react";
import Button from 'react-bootstrap/Button';
import axios from 'axios';
import jsPDF from 'jspdf';

const CriteriaPDFGenerator = ({ task, disabled }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [criteria, setCriteria] = useState(null);

  const handleGeneratePDF = async () => {
    setIsLoading(true);

    try {
      const response = await axios.get('http://localhost:3001/criteria');
      const criteriaData = response.data;

      setCriteria({
        task,
        criteria: criteriaData
      });

      generatePDF(task, criteriaData);

    } catch (error) {
      console.error('Error al obtener los criterios:', error);
      alert('Hubo un error al obtener los criterios');
    } finally {
      setIsLoading(false);
    }
  };

  const generatePDF = (task, criteriaData) => {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 10;
    const maxLineWidth = pageWidth - 2 * margin;
    const lineHeight = 10;
    let y = 20;

    doc.text('Criterios de la Tarea', margin, y);
    doc.setFontSize(12);

    y += lineHeight;
    doc.text(`Nombre de la tarea: ${task.nombreTarea}`, margin, y);

    y += lineHeight;
    const inputDescriptionLines = doc.splitTextToSize(`Descripción de la tarea: ${task.inputValue}`, maxLineWidth);
    inputDescriptionLines.forEach(line => {
      if (y + lineHeight > pageHeight - margin) {
        doc.addPage();
        y = margin;
      }
      y += lineHeight;
      doc.text(line, margin, y);
    });

    // Agregar el usuario seleccionado si está definido
    if (task.selectedOption) {
      y += lineHeight;
      doc.text(`El usuario seleccionado es: ${task.selectedOption}`, margin, y);
    }

    y += lineHeight;
    doc.text('Criterios:', margin, y);

    // Parsear el objeto criteriaData si no está en formato JSON
    const parsedCriteria = typeof criteriaData === 'string' ? JSON.parse(criteriaData) : criteriaData;

    // Obtener el valor de fontSize y convertirlo a número
    const fontSize = parseFloat(parsedCriteria.fontSize);

    // Ejemplo de condición para comparar fontSize con 14px
    if (!isNaN(fontSize) && fontSize > 14) {
      y += lineHeight;
      doc.text(`El tamaño de letra es mayor a 14px: ${parsedCriteria.fontSize}`, margin, y);
    }

    const criteriaText = JSON.stringify(criteriaData, null, 2);
    const criteriaLines = doc.splitTextToSize(criteriaText, maxLineWidth);

    criteriaLines.forEach(line => {
      if (y + lineHeight > pageHeight - margin) {
        doc.addPage();
        y = margin;
      }
      y += lineHeight;
      doc.text(line, margin, y);
    });

    doc.save('criterios.pdf');
  };

  return (
    <div>
      <Button variant="primary" onClick={handleGeneratePDF} disabled={disabled || isLoading}>
        {isLoading ? 'Generando PDF...' : 'Generar Feedback'}
      </Button>
      {criteria && (
        <div>
          {/* Aquí puedes agregar cualquier otra interfaz de usuario o mensaje que desees mostrar después de generar el PDF */}
        </div>
      )}
    </div>
  );
};

export default CriteriaPDFGenerator;
