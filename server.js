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

// Variable global para almacenar los criterios obtenidos
let storedCriteria = null;

// Función para verificar criterios de diseño con Puppeteer
async function checkDesignCriteria(webLink) {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto(webLink, { waitUntil: "networkidle0" });

  // Lógica para verificar los criterios de diseño
  const result = await page.evaluate(() => {
    const body = document.body;

    // Obtener el tamaño de letra y espaciado entre líneas
    const bodyStyles = window.getComputedStyle(body);
    const fontSize = parseFloat(bodyStyles.getPropertyValue("font-size"));
    const lineHeight = parseFloat(bodyStyles.getPropertyValue("line-height"));

    // Obtener botones y sus tamaños
    const buttons = document.querySelectorAll("button");
    const buttonSizes = [];
    buttons.forEach((button) => {
      const buttonRect = button.getBoundingClientRect();
      buttonSizes.push({ width: buttonRect.width, height: buttonRect.height });
    });

    // Obtener tamaños de letra para títulos (h1 a h6)
    const headings = document.querySelectorAll("h1, h2, h3, h4, h5, h6");
    const headingSizes = [];
    headings.forEach((heading) => {
      const headingStyles = window.getComputedStyle(heading);
      const headingFontSize = parseFloat(headingStyles.getPropertyValue("font-size"));
      headingSizes.push(headingFontSize);
    });

    // Función para calcular relación de contraste
    function getContrastRatio(color1, color2) {
      const lum1 = getRelativeLuminance(color1);
      const lum2 = getRelativeLuminance(color2);
      const ratio = (Math.max(lum1, lum2) + 0.05) / (Math.min(lum1, lum2) + 0.05);
      return ratio.toFixed(2);
    }

    // Función para calcular luminancia relativa
    function getRelativeLuminance(color) {
      const rgb = color.match(/\d+/g);
      const [r, g, b] = rgb.map((c) => {
        let val = parseInt(c) / 255;
        val = val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4);
        return val;
      });
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    }

    // Verificar todos los criterios
    const criteriaResult = {
      fontSize: fontSize >= 14 ? `${fontSize}px` : 'No cumple el tamaño mínimo de 14px',
      lineHeight: lineHeight >= 1.5 ? lineHeight.toFixed(2) : 'No cumple el espaciado mínimo de 1.5',
      headingSizes: headingSizes.map(size => size >= 26 ? `${size}px` : `Título no cumple el tamaño mínimo de 26px`),
      buttonSizes: buttonSizes.every(button => button.width >= 44 && button.height >= 44) ? buttonSizes : 'Al menos un botón no cumple el tamaño mínimo de 44x44 píxeles',
    };

    // Agregar verificación de relación de contraste (ejemplo: verificar el color de fondo y texto)
    const bodyColor = bodyStyles.getPropertyValue("color");
    const bgColor = bodyStyles.getPropertyValue("background-color");
    const contrastRatio = getContrastRatio(bodyColor, bgColor);
    criteriaResult.contrastRatio = contrastRatio >= 7 ? contrastRatio : 'No cumple la relación de contraste mínima de 7:1';

    return criteriaResult;
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
            content: `para Puppeteer crea el código completo con {headless: false} (solo el código) para: ${project.inputValue}, en la web: ${project.webLink} y después de realizar las acciones requeridas, toma una captura de pantalla con el nombre ${project.id}. No ocupes la funcion page.waitForTimeout de puppeteer ni tampoco uses el delimitador backticks. Abre en pantalla completa con: await page.setViewport({width: 1920,height: 1080 ,deviceScaleFactor: 1,}); y no uses la función waitForNavigation() de Puppeteer`,
          },
        ],
        model: "gpt-3.5-turbo",
        max_tokens: 800,
      });

      const url = await openai.chat.completions.create({
        messages: [
          {
            role: "user",
            content: `${project.inputValue} en ${project.webLink}$ que url debo usar? dame solo el url por favor y que sea válido`,
          },
        ],
        model: "gpt-3.5-turbo",
        max_tokens: 800,
      });

      const urlResponse = url.choices[0].message.content;
      console.log("Link de OpenAI:", urlResponse);

      const generatedCode = response.choices[0].message.content;
      console.log("Respuesta de OpenAI:", generatedCode);

      // Ejecutar el código generado por OpenAI
      await eval(generatedCode);

      // Verificar criterios de diseño después de ejecutar el código
      criteriaResult = await checkDesignCriteria(urlResponse);

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

    // Guardar los criterios en la variable global
    storedCriteria = criteriaResult;

    res.status(200).json({ success: true, criteriaResult });
  }
});

// Ruta para obtener los criterios de diseño después de la prueba
app.get("/criteria", async (req, res) => {
  try {
    if (storedCriteria) {
      res.status(200).json(storedCriteria);
    } else {
      res.status(404).json({ error: 'No hay criterios almacenados. Por favor, ejecuta la prueba primero.' });
    }
  } catch (error) {
    console.error('Error al obtener los criterios:', error);
    res.status(500).json({ error: 'Hubo un error al obtener los criterios' });
  }
});

// Iniciar el servidor
app.listen(port, () => {
  console.log(`Servidor Node.js corriendo en http://localhost:${port}`);
});
