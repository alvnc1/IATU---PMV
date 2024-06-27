import React, { useState } from "react";
import Button from 'react-bootstrap/Button';
import axios from 'axios';
import jsPDF from 'jspdf';
import myImage from "./images/logo.png"

const CriteriaPDFGenerator = ({ task, disabled }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [criteria, setCriteria] = useState(null);

  const getUserInfo = (selectedOption) => {
    if (selectedOption === "opcion1") {
      return "Javier Sánchez, 32 años";
    } else if (selectedOption === "opcion2") {
      return "José Gómez, 68 años";
    } else {
      return "Usuario no especificado";
    }
  };

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
    doc.text('Criterios de la Tarea', (pageWidth - doc.getTextWidth('Criterios de la Tarea'))/2, y);
    doc.setFontSize(12);
    y += lineHeight;
    doc.text(`Nombre de la tarea: ${task.nombreTarea}`, margin, y);

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
    if (task.selectedOption === "opcion1") {
      y += lineHeight;
      doc.text(`El usuario seleccionado es: ${getUserInfo(task.selectedOption)}`, margin, y);

      // Parsear el objeto criteriaData si no está en formato JSON
      const parsedCriteria = typeof criteriaData === 'string' ? JSON.parse(criteriaData) : criteriaData;

      // Obtener el valor de fontSize y convertirlo a número
      const fontSize = parseFloat(parsedCriteria.fontSize);

      // Ejemplo de condición para comparar fontSize con 14px
      if (!isNaN(fontSize) && fontSize > 12) {
        y += lineHeight;
        doc.text(`El tamaño de letra es mayor a 12px: ${parsedCriteria.fontSize} \nEl usuario puede reconocer comodamente el tamaño de letra\n`, margin, y);
      }else{
        y += lineHeight;
        doc.text(`El tamaño de letra no es mayor a 12px: ${parsedCriteria.fontSize}\nEl usuario no puede reconocer comodamente el tamaño de letra\n`, margin, y);
      }

      // Obtener el valor de lineHeight y convertirlo a número
      const lineHeightValue = parseFloat(parsedCriteria.lineHeight);

      // Mostrar el lineHeight solo si es mayor a 1.5
      if (!isNaN(lineHeightValue) && lineHeightValue > 1.3) {
        y += lineHeight;
        doc.text(`El line-height es mayor a 1.3 \nEl interlineado de la pagina es adecuada para este usuario`, margin, y);
      } else {
        y += lineHeight;
        doc.text(`El line-height no es mayor a 1.3\nEl interlineado de la pagina no es adecuada para este usuario`, margin, y);
      }
      
      // Obtener el valor de contrastRatio y mostrarlo si existe
      const contrastRatio = parsedCriteria.contrastRatio;
      if (contrastRatio !== undefined) {
        y += lineHeight;
        const parts = contrastRatio.toString().split('.');
        const contrastPrint = contrastRatio.toString().replace('.',':');
        const ratioDer = parseInt(parts[0], 10);
        const ratioIzq = parseInt(parts[0], 10);
        if(ratioDer >= 4.5 && ratioIzq >= 1){
          doc.text(`La relacion de contraste de la pagina es de al menos 4.5:1: ${contrastPrint}\nLa relacion de contraste es comoda para el usuario`, margin, y);
        } else {
          doc.text(`La relacion de contraste de la pagina es menor a 4.5:1: ${contrastPrint}\nLa relacion de contraste no es comoda para el usuario`, margin, y);
        }
      }

      // Verificar si headingSizes existe y es un array antes de intentar iterar sobre él
      if (Array.isArray(parsedCriteria.headingSizes) && parsedCriteria.headingSizes.length > 0) {
        y += lineHeight;
        doc.text('Tamaños de encabezados:', margin, y);

        parsedCriteria.headingSizes.forEach((headingSize, index) => {
          y += lineHeight;
          if (parseInt(headingSize) >= 24){
            doc.text(`El tamaño del Encabezado ${index + 1} es de al menos 24pt: ${headingSize}\nEl usuario puede leer comodamente este encabezado`, margin, y);
          } else{
            doc.text(`El tamaño del Encabezado ${index + 1} es menor a 24pt: ${headingSize}\nEl usuario no puede leer comodamente este encabezado`, margin, y);
          }
        });
      } else {
        y += lineHeight;
        doc.text('No se encontraron tamaños de encabezados válidos', margin, y);
      }

      // Verificar si buttonSizes existe y es un array antes de intentar iterar sobre él
      alert(parsedCriteria.buttonSizes); //parsedCriteria.buttonSizes es un string que dice "Al menos un boton no cumple el criterio"
      alert(parsedCriteria.buttonSizes.length);

      if (Array.isArray(parsedCriteria.buttonSizes) && parsedCriteria.buttonSizes.length > 0) {
        y += lineHeight;
        doc.text('Tamaños de botones:', margin, y);

        parsedCriteria.buttonSizes.forEach((buttonSize, index) => {
          y += lineHeight;
          doc.text(`La dimension del Botón ${index + 1} es: ${buttonSize.width}x${buttonSize.height} píxeles`, margin, y);
        });
      } else {
        y += lineHeight;
        doc.text('No se encontraron tamaños de botones válidos', margin, y);
      }
    }

    // Aplicar las condiciones solo si task.selectedOption es igual a "opcion2"
    if (task.selectedOption === "opcion2") {
      y += lineHeight;
      doc.text(`El usuario seleccionado es: ${getUserInfo(task.selectedOption)}`, margin, y);

      // Parsear el objeto criteriaData si no está en formato JSON
      const parsedCriteria = typeof criteriaData === 'string' ? JSON.parse(criteriaData) : criteriaData;

      // Obtener el valor de fontSize y convertirlo a número
      const fontSize = parseFloat(parsedCriteria.fontSize);

      // Ejemplo de condición para comparar fontSize con 14px
      if (!isNaN(fontSize) && fontSize > 14) {
        y += lineHeight;
        doc.text(`El tamaño de letra es mayor a 14px: ${parsedCriteria.fontSize}\nEl usuario puede reconocer comodamente el tamaño de letra`, margin, y);
      }else{
        y += lineHeight;
        doc.text(`El tamaño de letra no es mayor a 14px: ${parsedCriteria.fontSize}\nEl usuario no puede reconocer comodamente el tamaño de letra`, margin, y);
      }

      // Obtener el valor de lineHeight y convertirlo a número
      const lineHeightValue = parseFloat(parsedCriteria.lineHeight);

      // Mostrar el lineHeight solo si es mayor a 1.5
      if (!isNaN(lineHeightValue) && lineHeightValue > 1.5) {
        y += lineHeight;
        doc.text(`El line-height es mayor a 1.5\nEl interlineado de la pagina es adecuada para este usuario`, margin, y);
      } else {
        y += lineHeight;
        doc.text(`El line-height no es mayor a 1.5\nEl interlineado de la pagina no es adecuada para este usuario`, margin, y);
      }
      
      // Obtener el valor de contrastRatio y mostrarlo si existe
      const contrastRatio = parsedCriteria.contrastRatio;
      if (contrastRatio !== undefined) {
        y += lineHeight;
        const parts = contrastRatio.toString().split('.');
        const contrastPrint = contrastRatio.toString().replace('.',':');
        const ratioDer = parseInt(parts[0], 10);
        const ratioIzq = parseInt(parts[0], 10);
        if(ratioDer >= 7 && ratioIzq >= 1){
          doc.text(`La relación de contraste de la pagina es de al menos 7:1: ${contrastPrint}\nLa relación de contraste es comoda para el usuario`, margin, y);
        } else {
          doc.text(`La relación de contraste de la pagina es menor a 7:1: ${contrastPrint}\nLa relación de contraste no es comoda para el usuario`, margin, y);
        }
      }

      // Verificar si headingSizes existe y es un array antes de intentar iterar sobre él
      if (Array.isArray(parsedCriteria.headingSizes) && parsedCriteria.headingSizes.length > 0) {
        y += lineHeight;
        doc.text('Tamaños de encabezados:', margin, y);

        parsedCriteria.headingSizes.forEach((headingSize, index) => {
          y += lineHeight;
          if (parseInt(headingSize) >= 26){
            doc.text(`El tamaño del Encabezado ${index + 1} es de al menos 26pt: ${headingSize}\nEl usuario puede leer comodamente este encabezado`, margin, y);
          } else{
            doc.text(`El tamaño del Encabezado ${index + 1} es de menor a 26pt: ${headingSize}\nEl usuario no puede leer comodamente este encabezado`, margin, y);
          }
        });
      } else {
        y += lineHeight;
        doc.text('No se encontraron tamaños de encabezados válidos', margin, y);
      }

      // Verificar si buttonSizes existe y es un array antes de intentar iterar sobre él
      if (Array.isArray(parsedCriteria.buttonSizes) && parsedCriteria.buttonSizes.length > 0) {
        y += lineHeight;
        doc.text('Tamaños de botones:', margin, y);

        parsedCriteria.buttonSizes.forEach((buttonSize, index) => {
          y += lineHeight;
          if (parseInt(buttonSize.width) >= 44 && parseInt(buttonSize.height) >= 44){
            doc.text(`El tamaño del Botón ${index + 1} es de dimension mayor o igual a 44x44: ${buttonSize.width}x${buttonSize.height} píxeles\nEl usuario puede reconocer comodamente este botón`, margin, y);

          } else{
            doc.text(`El tamaño del Botón ${index + 1} es de dimension menor a 44x44: ${buttonSize.width}x${buttonSize.height} píxeles\nEl usuario puede no reconocer comodamente este botón`, margin, y);
          }
        });
      } else {
        y += lineHeight;
        doc.text('No se encontraron tamaños de botones válidos', margin, y);
      }
    }
    const img = new Image();
    img.src = myImage;
    img.onload = () => {
      const imgWidth = 50;
      const imgHeight = (img.height * imgWidth) / img.width; // Mantener la proporción de la imagen

      // Agregar imagen al PDF
      doc.addImage(img, 'PNG', pageWidth - imgWidth - margin, margin, imgWidth, imgHeight); // (imagen, tipo, X, Y, ancho, alto)

      doc.save('Reporte.pdf');
      };
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
