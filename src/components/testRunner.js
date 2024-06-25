import React, { useState } from 'react';
import { Button } from 'react-bootstrap';
import { IoMdPlayCircle } from 'react-icons/io';

const TestRunner = ({ project, onTestRun }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [responseText, setResponseText] = useState('');

  const handleRunTest = async () => {
    setLoading(true);

    try {
      const response = await fetch('http://localhost:3001/run-test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ project }),
      });

      const data = await response.json();
      if (data.success) {
        console.log('Respuesta de OpenAI:', data.generatedCode);
        setResponseText(data.generatedCode);
        onTestRun(); // Llamar a la función de callback cuando la prueba se ejecuta correctamente
      } else {
        setError('Hubo un error al ejecutar la prueba');
      }
    } catch (error) {
      console.error('Error al ejecutar la prueba: ', error);
      setError('Hubo un error al ejecutar la prueba');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Button variant="success" onClick={handleRunTest} disabled={loading}>
        {loading ? 'Cargando...' : <><IoMdPlayCircle /> Ejecutar Prueba</>}
      </Button>

      {error && <p>{error}</p>}
      {responseText && (
        <div style={{ marginTop: '20px', border: '1px solid #ccc', padding: '10px' }}>
          <h4>Resultado de la Prueba:</h4>
          <pre>{responseText}</pre>
        </div>
      )}
    </div>
  );
};

export default TestRunner;
