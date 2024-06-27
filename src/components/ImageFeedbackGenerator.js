import React, { useState } from 'react';
import Button from 'react-bootstrap/Button';
import { saveAs } from 'file-saver';
import jsPDF from 'jspdf';

const ImageFeedbackGenerator = ({ imageUrl }) => {
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(false);

  const generateFeedback = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:3001/generate-feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ imageUrl }),
      });
      const data = await response.json();
      if (data.success) {
        setFeedback(data.feedback);
        downloadFeedbackPDF(data.feedback); // Llamar a la función para descargar el PDF
      } else {
        setFeedback('Error al generar el feedback.');
      }
    } catch (error) {
      console.error('Error al generar el feedback:', error);
      setFeedback('Error al generar el feedback.');
    } finally {
      setLoading(false);
    }
  };

  const downloadFeedbackPDF = (feedbackText) => {
    const pdf = new jsPDF();
    const textLines = pdf.splitTextToSize(feedbackText, 180); // Ajustar el texto al ancho de 180 puntos
  
    let startY = 20; // Posición inicial de escritura
    const pageHeight = pdf.internal.pageSize.height; // Altura de la página
  
    textLines.forEach((line, index) => {
      if (startY + 10 > pageHeight) { // Si no hay suficiente espacio en la página actual, agregar una nueva página
        pdf.addPage();
        startY = 20; // Reiniciar la posición de escritura en la nueva página
      }
      pdf.text(line, 20, startY); // Escribir la línea de texto en la posición actual
      startY += 10; // Ajustar la posición para la siguiente línea
    });
  
    const pdfName = 'Feedback.pdf';
    pdf.save(pdfName);
  };

  return (
    <div>
      <Button variant="primary" className="feed-btn" onClick={generateFeedback} disabled={loading}>
        {loading ? 'Generando Feedback...' : 'Generar Feedback de la Imágen'}
      </Button>
      {feedback && (
        <div>
        </div>
      )}
    </div>
  );
};

export default ImageFeedbackGenerator;
