const express = require("express");
const puppeteer = require("puppeteer");
const openai = require("./src/openaiConfig"); // Asegúrate de tener tu configuración de OpenAI adecuada aquí
const cors = require("cors"); // Importa el middleware CORS

const app = express();
const port = 3001;

// Configura CORS para permitir solicitudes desde http://localhost:3000
app.use(cors());

app.use(express.json());

const MAX_ATTEMPTS = 10;

// Función para verificar criterios de diseño con Puppeteer
async function checkDesignCriteria(webLink) {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto(webLink, { waitUntil: "networkidle0" });

  // Lógica para verificar los criterios de diseño
  const result = await page.evaluate(() => {
    const body = document.body;

    // Ejemplo de verificación de tamaño de letra y espaciado entre líneas
    const bodyStyles = window.getComputedStyle(body);
    const fontSize = parseFloat(bodyStyles.getPropertyValue("font-size"));
    const lineHeight = parseFloat(bodyStyles.getPropertyValue("line-height"));

    // Ejemplo de verificación de tamaño de letra para títulos
    const headings = document.querySelectorAll("h1, h2, h3, h4, h5, h6");
    const headingSizes = [];
    headings.forEach((heading) => {
      const headingStyles = window.getComputedStyle(heading);
      const headingFontSize = parseFloat(headingStyles.getPropertyValue("font-size"));
      headingSizes.push(headingFontSize);
    });

    // Ejemplo de verificación de tamaño de botones
    const buttons = document.querySelectorAll("button");
    const buttonSizes = [];
    buttons.forEach((button) => {
      const buttonRect = button.getBoundingClientRect();
      buttonSizes.push({ width: buttonRect.width, height: buttonRect.height });
    });

    return {
      fontSize: `${fontSize}px`,
      lineHeight: lineHeight.toFixed(2),
      headingSizes,
      buttonSizes,
    };
  });

  await browser.close();

  return result;
}

// Ruta para ejecutar la prueba con OpenAI y verificar criterios de diseño
app.post("/run-test", async (req, res) => {
  const { project } = req.body;

  let success = false;
  let criteriaResult = null;

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

      // Verificar criterios de diseño después de ejecutar el código
      criteriaResult = await checkDesignCriteria(project.webLink);

      success = true;
      break; // Salir del bucle si la prueba es exitosa
    } catch (error) {
      console.error(`Error al ejecutar la prueba en el intento ${attempt}: `, error);
      if (attempt === MAX_ATTEMPTS) {
        res.status(500).json({
          success: false,
          error: "Hubo un error al ejecutar la prueba después de múltiples intentos, intenta de nuevo o cambia tus parámetros",
        });
      } else {
        // Esperar un tiempo antes del siguiente intento
        await new Promise((resolve) => setTimeout(resolve, 2000)); // Espera 2 segundos
      }
    }
  }

  if (success) {
    // Mostrar los criterios cumplidos en el log
    console.log("Criterios cumplidos:");
    console.log(`Tamaño de letra: ${criteriaResult.fontSize}`);
    console.log(`Tamaño de botones: ${JSON.stringify(criteriaResult.buttonSizes)}`);
    console.log("Tamaños de letra para títulos:");
    criteriaResult.headingSizes.forEach((size, index) => {
      console.log(`  - Título ${index + 1}: ${size}px`);
    });

    res.status(200).json({ success: true, criteriaResult });
  }
});

// Iniciar el servidor
app.listen(port, () => {
  console.log(`Servidor Node.js corriendo en http://localhost:${port}`);
});
