const express = require("express");
const puppeteer = require("puppeteer");
const openai = require("./src/openaiConfig");
const cors = require("cors"); // Importa el middleware CORS
const fs = require("fs");
const path = require("path");

const app = express();
const port = 3001;

// Configura CORS para permitir solicitudes desde http://localhost:3000
app.use(cors());

app.use(express.json());

const MAX_ATTEMPTS = 10;

app.post("/run-test", async (req, res) => {
  const { project } = req.body;

  let success = false;

  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    try {
      console.log(`Intento ${attempt} de ${MAX_ATTEMPTS}`);

      const response = await openai.chat.completions.create({
        messages: [
          {
            role: "user",
            content: `para Puppeteer crea el código completo (solo el código) para: ${project.inputValue}, en la web: ${project.webLink} y después de realizar las acciones requeridas, toma una captura de pantalla con el nombre screenshot. Por favor no uses la función waitforTimeout de Puppeteer.`,
          },
        ],
        model: "gpt-3.5-turbo",
        max_tokens: 800,
      });

      const generatedCode = response.choices[0].message.content;
      console.log("Respuesta de OpenAI:", generatedCode);
      // Ejecutar el código generado por OpenAI
      await eval(generatedCode);

      success = true;
      break; // Salir del bucle si la prueba es exitosa
    } catch (error) {
      console.error(
        `Error al ejecutar la prueba en el intento ${attempt}: `,
        error
      );
      if (attempt === MAX_ATTEMPTS) {
        res
          .status(500)
          .json({
            success: false,
            error:
              "Hubo un error al ejecutar la prueba después de múltiples intentos, intenta de nuevo o cambia tus parámetros",
          });
      } else {
        // Esperar un tiempo antes del siguiente intento
        await new Promise((resolve) => setTimeout(resolve, 2000)); // Espera 2 segundos
      }
    }
  }

  if (success) {
    res.status(200).json({ success: true });
  }
});

app.listen(port, () => {
  console.log(`Servidor Node.js corriendo en http://localhost:${port}`);
});
