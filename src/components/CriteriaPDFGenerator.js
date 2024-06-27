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

    y += lineHeight;
    doc.text('Criterios:', margin, y);

    const criteriaText = JSON.stringify(criteriaData, null, 2);
    const criteriaLines = doc.splitTextToSize(criteriaText, maxLineWidth);

    console.log(criteriaLines);

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
        </div>
      )}
    </div>
  );
};

export default CriteriaPDFGenerator;
