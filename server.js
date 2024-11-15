const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const app = express();
const port = 3001;

// Configurar CORS para permitir solicitudes
app.use(cors({
    origin: '*'
  }));

app.use(express.json());

app.post('/run-python', (req, res) => {
    const { videoUrl, urlTarea, categorias, idT , idP} = req.body;

    if (!videoUrl || !urlTarea || !categorias) {
        return res.status(400).json({ error: 'Video URL, URL de la Tarea y Categorías son requeridos' });
    }

    // Log para ver los datos recibidos
    console.log(`Datos recibidos - videoUrl: ${videoUrl}, urlTarea: ${urlTarea}, categorias: ${categorias}, id:${idT}, id Proyecto: ${idP}`);

    // Ejecutar el proceso de Python
    const pythonProcess = spawn('python', ['checkAccesibilidad.py', videoUrl,urlTarea,categorias,idT,idP]);
    

    pythonProcess.stdout.on('data', (data) => {
        console.log(`stdout: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Proceso finalizado con código ${code}`);
        res.json({ message: 'Script ejecutado correctamente', code });
    });
});

app.listen(port, () => {
    console.log(`Servidor escuchando en http://localhost:${port}`);
});
