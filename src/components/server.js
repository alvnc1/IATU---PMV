const express = require('express');
const { spawn } = require('child_process');
const app = express();
const port = 3001;

app.use(express.json());

app.post('/run-python', (req, res) => {
    const { videoUrl } = req.body;

    if (!videoUrl) {
        return res.status(400).json({ error: 'Video URL is required' });
    }

    const pythonProcess = spawn('python', ['../frameCapture.py', videoUrl]);

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
