// PDFGenerator.js
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import myImage from "./images/ConcursoPoleraGen2020.png"

export const generatePDF = async () => {
  const doc = new jsPDF();
  const titulo = "Titulo";
  const pageWidth = doc.internal.pageSize.getWidth();
  const textWidth = doc.getTextDimensions(titulo).w;
  
  const x_titulo = (pageWidth - textWidth)/2;

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(22);
  doc.text(titulo, x_titulo, 20);
  doc.setFontSize(16);
  doc.text('This is a PDF document generated with jsPDF.', 20, 30);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(16);
  const listItems = [
    'First item in the list',
    'Second item in the list',
    'Third item in the list',
  ];
  let y = 40;
  listItems.forEach((item, index) => {
    doc.text(`${index + 1}. ${item}`, 10, y);
    y += 10;
  });


  const img = new Image();
  img.src = myImage;
  img.onload = () => {
    const imgWidth = 120;
    const imgHeight = (img.height * imgWidth) / img.width; // Mantener la proporción de la imagen

    // Agregar imagen al PDF
    doc.addImage(img, 'PNG', 10, y + 10, imgWidth, imgHeight); // (imagen, tipo, X, Y, ancho, alto)

    alert("La descarga ha iniciado");
    doc.save('generated.pdf');
  };
};
