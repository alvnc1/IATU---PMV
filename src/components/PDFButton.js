// PDFButton.js
import React from 'react';
import Button from 'react-bootstrap/Button';

const PDFButton = ({ onClick }) => {
  return (
    <Button onClick={onClick}>Generate PDF</Button>
  );
};

export default PDFButton;
