// PDFGenerator.js
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

export const generatePDF = () => {
  const doc = new jsPDF();
  const titulo = "TITULO QL";
  const pageWidth = doc.internal.pageSize.getWidth();
  const textWidth = doc.getTextDimensions(titulo).w;
  
  const x_titulo = (pageWidth - textWidth)/2;

  doc.setFontSize(22);
  doc.text('Hello world!', x_titulo, 20);
  doc.setFontSize(16);
  doc.text('This is a PDF document generated with jsPDF.', 20, 30);

  const imgElement = document.getElementById('myimage')


  alert("La descarga ha iniciado");
  doc.save('generated.pdf');
};
