from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF
import os
from textstat import textstat
from PIL import Image, ImageStat
import spacy

# Configurar Selenium con Chrome en modo headless
chrome_options = Options()
chrome_options.add_argument("--headless=old")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Cargar el modelo de SpaCy
nlp = spacy.load("en_core_web_md")

# Configurar directorios
capturas_dir = "capturas_selenium"
legibility_dir = os.path.join(capturas_dir, "legibility")
os.makedirs(legibility_dir, exist_ok=True)

# Inicializar el PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Verificación de Legibilidad de Texto en la UI", ln=True, align='C')

# Navegar a la URL
url = "https://www.mercadolibre.cl"  # URL de ejemplo
driver.get(url)

# Guardar la captura de pantalla completa
screenshot_path = os.path.join(legibility_dir, "captura_completa.png")
driver.save_screenshot(screenshot_path)

def is_mostly_black(image_path, threshold=0.9):
    """ Verifica si la imagen tiene más de `threshold` porcentaje de píxeles negros """
    with Image.open(image_path) as img:
        img = img.convert('L')  # Convertir a escala de grises
        stat = ImageStat.Stat(img)
        num_pixels = img.width * img.height
        num_black_pixels = sum(1 for pixel in img.getdata() if pixel < 30)  # Umbral para considerar un píxel "negro"
        black_ratio = num_black_pixels / num_pixels
        return black_ratio >= threshold

# Extraer todos los elementos de texto
elements = driver.find_elements(By.XPATH, "//*[not(self::script or self::style)][text()]")

# Verificar legibilidad
for index, elem in enumerate(elements, start=1):
    text = elem.text.strip()
    if text:
        # Calcular índices de legibilidad
        gunning_fog = textstat.gunning_fog(text)
        flesch_reading_ease = textstat.flesch_reading_ease(text)
        print("gunning_fog: ",gunning_fog)
        print("flesch: ", flesch_reading_ease)
        
        # Definir umbrales para aceptabilidad
        if gunning_fog > 12 or flesch_reading_ease < 60:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200, 10, txt=f"- Advertencia: Texto con legibilidad insuficiente encontrado: '{text[:50]}...'\n  Gunning Fog: {gunning_fog}, Flesch Reading Ease: {flesch_reading_ease}")
            
            # Capturar la imagen del elemento
            location = elem.location
            size = elem.size
            with Image.open(screenshot_path) as img:
                left = location['x']
                top = location['y']
                right = left + size['width']
                bottom = top + size['height']

                # Recortar la región del elemento
                region_recortada = img.crop((left, top, right, bottom))
                captura_elemento = os.path.join(legibility_dir, f"texto_legibilidad_insuficiente_{index}.png")
                region_recortada.save(captura_elemento)
                
                # Filtrar imágenes que sean mayoritariamente negras
                if not is_mostly_black(captura_elemento):
                    pdf.image(captura_elemento, x=15, y=None, w=100)  # Añadir la captura al PDF centrada
                else:
                    os.remove(captura_elemento)

# Guardar el PDF con los resultados
output_filename = "reporte_legibilidad_ui.pdf"
pdf.output(output_filename)

# Cerrar el navegador
driver.quit()
