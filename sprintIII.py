import shutil
import cv2
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
import shutil
from inference_sdk import InferenceHTTPClient
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector


# Crear una carpeta para guardar las capturas si no existe
output_dir = 'capturas'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
video_path = "ml.mp4"
# Abrir el video con la función moderna de scenedetect
video = open_video(video_path)

pdf = FPDF()
pdf.add_page()


# Crear un SceneManager y añadir un detector de contenido
scene_manager = SceneManager()
scene_manager.add_detector(ContentDetector(threshold=30.0))  # Ajusta el umbral si es necesario

# Detectar escenas en el video
scene_manager.detect_scenes(video)

# Obtener la lista de escenas detectadas
scene_list = scene_manager.get_scene_list()

print(f"Detectadas {len(scene_list)} escenas.")

# Cargar el video con OpenCV para capturar fotogramas
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)  # Obtener los FPS del video

for i, scene in enumerate(scene_list):
    start_frame, end_frame = scene[0].get_frames(), scene[1].get_frames()
    timestamp = scene[0].get_seconds()

    # Calcular el número de fotogramas a avanzar para capturar el fotograma 1.5 segundos después
    frames_to_advance = int(fps * 1.5)
    new_frame_position = start_frame + frames_to_advance

    # Mover el puntero del video al nuevo fotograma (1.5 segundos después)
    cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame_position)

    # Leer y guardar el fotograma 1.5 segundos después del cambio de escena
    ret, frame = cap.read()
    if ret:
        filename = os.path.join(output_dir, f"Escena_{i + 1}_{int(timestamp + 1.5)}s.png")
        cv2.imwrite(filename, frame)
        print(f"Guardado {filename}")

cap.release()


# Inicializar el cliente HTTP para inferencias
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="bUyMUjRY0TGSKrbNpksy"
)

# Directorio de imágenes de entrada
input_dir = "capturas"
output_base_dir = "output_evaluated_images"
os.makedirs(output_base_dir, exist_ok=True)

# Inicializar el diccionario para las clases
dic_clases = {}

# Obtener dimensiones de la página
page_width = pdf.w
page_height = pdf.h

# Centrar el título horizontal y verticalmente
pdf.set_xy(0, page_height / 2 - 10)  # Centramos en Y a la mitad de la página
pdf.set_font("Arial", 'B', 16)
pdf.cell(page_width, 10, txt="Componentes Encontrados y Elementos a Analizar", ln=True, align="C")

# Procesar cada imagen
for idx, image_filename in enumerate(os.listdir(input_dir)):
    if image_filename.endswith(('.jpg', '.jpeg', '.png')):
        image_path = os.path.join(input_dir, image_filename)

        # Realizar la inferencia con los modelos
        result = CLIENT.infer(image_path, model_id="cingoz8/1")
        result_model_2 = CLIENT.infer(image_path, model_id="app-icon/45")

        # Combinar los resultados de ambos modelos
        combined_results = result['predictions'] + result_model_2['predictions']

        # Crear subdirectorio para la imagen
        image_output_dir = os.path.join(output_base_dir, os.path.splitext(image_filename)[0])
        os.makedirs(image_output_dir, exist_ok=True)

        # Cargar la imagen original
        image = cv2.imread(image_path)
        original_height, original_width, _ = image.shape

        # Procesar los resultados y dibujar bounding boxes en la imagen original
        for i, prediction in enumerate(combined_results):
            # Coordenadas de la bounding box
            x0 = int(prediction['x'] - prediction['width'] / 2)
            y0 = int(prediction['y'] - prediction['height'] / 2)
            x1 = int(prediction['x'] + prediction['width'] / 2)
            y1 = int(prediction['y'] + prediction['height'] / 2)

            # Dibujar la bounding box en la imagen original
            cv2.rectangle(image, (x0, y0), (x1, y1), color=(0, 255, 0), thickness=2)

            # Poner el label (clase y confianza) encima de la bounding box
            label = f"{prediction['class']} ({prediction['confidence']:.2f})"
            cv2.putText(image, label, (x0, y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Guardar la imagen original con todas las bounding boxes dibujadas
        output_image_path = os.path.join(image_output_dir, os.path.basename(image_path))
        cv2.imwrite(output_image_path, image)

        # Añadir la imagen completa con bounding boxes al PDF
        if idx % 2 == 0:
            pdf.add_page()  # Añadir nueva página para cada par de imágenes

        # Posicionar la primera o segunda imagen en la página
        x_pos = 10  # Margen izquierdo
        y_pos = 10 if idx % 2 == 0 else 150  # Posicionar la imagen: arriba (y=10) o abajo (y=150)
        pdf.image(output_image_path, x=x_pos, y=y_pos, w=180)  # Ajustar el tamaño según sea necesario

pdf.add_page()

#result = CLIENT.infer(your_image.jpg, model_id="cingoz8/1")


def hdu_tres(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless=old")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Cargar el modelo de SpaCy
    nlp = spacy.load("en_core_web_md")

    driver.get(url)
    # Configurar directorios
    capturas_dir = "capturas_selenium"
    legibility_dir = os.path.join(capturas_dir, "legibility")
    os.makedirs(legibility_dir, exist_ok=True)
    # Guardar la captura de pantalla completa
    screenshot_path = os.path.join(legibility_dir, "captura_completa.png")
    driver.save_screenshot(screenshot_path)

    def has_few_colors(image_path, max_colors=10):
        """ Verifica si la imagen tiene menos de `max_colors` colores diferentes """
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            colors = img.getcolors(maxcolors=256)  # Limitar la cantidad de colores para optimizar el rendimiento
            if colors and len(colors) <= max_colors:
                return True
            return False

    def is_mostly_black(image_path, threshold=0.9):
        """ Verifica si la imagen tiene más de `threshold` porcentaje de píxeles negros """
        with Image.open(image_path) as img:
            img = img.convert('L')  # Convertir a escala de grises
            num_pixels = img.width * img.height
            num_black_pixels = sum(1 for pixel in img.getdata() if pixel < 30)  # Umbral para considerar un píxel "negro"
            black_ratio = num_black_pixels / num_pixels
            return black_ratio >= threshold

    def is_useful_image(image_path):
        """ Verifica si una imagen es útil usando varios criterios """
        if is_mostly_black(image_path):
            return False
        if has_few_colors(image_path):
            return False
        return True

    def is_small_image(image_path, max_size=(400, 400)):
        """ Verifica si la imagen tiene un tamaño pequeño adecuado para un elemento UI """
        with Image.open(image_path) as img:
            return img.size[0] <= max_size[0] and img.size[1] <= max_size[1]
    # Inicializar el PDF
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Verificación de Legibilidad de Texto en la UI", ln=True, align='C')
    # Extraer todos los elementos de texto
    elements = driver.find_elements(By.XPATH, "//*[not(self::script or self::style)][text()]")

    # Guardar las capturas de los elementos y añadirlas al PDF sin modificar su tamaño si son útiles y pequeñas
    for index, elem in enumerate(elements, start=1):
        text = elem.text.strip()
        if text:
            # Calcular índices de legibilidad
            gunning_fog = textstat.gunning_fog(text)
            flesch_reading_ease = textstat.flesch_reading_ease(text)
            
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
                    
                    # Filtrar imágenes que sean mayoritariamente negras o demasiado grandes
                    if is_useful_image(captura_elemento) and is_small_image(captura_elemento):
                        pdf.image(captura_elemento, x=15, y=None, w=0, h=0)  # Añadir la captura al PDF
                    else:
                        print(f"La captura {captura_elemento} fue descartada por no ser útil o ser demasiado grande.")
                        os.remove(captura_elemento)  # Eliminar la captura si no es útil o demasiado grande


    # Cerrar el navegador
    #driver.quit()

    # Eliminar el directorio de capturas al finalizar
    if os.path.exists(capturas_dir):
        shutil.rmtree(capturas_dir)

# Guardar el PDF con los resultados
    


def verificar_enlaces_coherencia_titulo(url):
    # Configurar Selenium con Chrome en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless=old")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Configurar directorios
    capturas_dir = "capturas_selenium"
    enlaces_dir = os.path.join(capturas_dir, "enlaces")
    os.makedirs(enlaces_dir, exist_ok=True)

    
    pdf.add_page()
    pdf.cell(200, 10, txt="Verificación de Coherencia entre Enlaces y Títulos de Página", ln=True, align='C')

    # Navegar a la URL
    driver.get(url)

    # Buscar todos los enlaces visibles
    enlaces = driver.find_elements(By.TAG_NAME, 'a')
    enlaces_coinciden = 0  # Contador de enlaces que coinciden
    for index, enlace in enumerate(enlaces, start=1):
        if enlace.is_displayed() and enlace.get_attribute('href'):
            link_text = enlace.text.strip()
            link_url = enlace.get_attribute('href')
            
            # Abrir el enlace en una nueva pestaña
            driver.execute_script("window.open(arguments[0], '_blank');", link_url)
            driver.switch_to.window(driver.window_handles[1])

            # Obtener el título de la página de destino
            page_title = driver.title.strip()

            # Verificar si se redirigió a una página de inicio de sesión
            if "login" in driver.current_url.lower() or "signin" in driver.current_url.lower() or "iniciar sesión" in page_title.lower():
                print(f"Redirigido a una página de inicio de sesión para el enlace '{link_text}'. Ignorando este enlace.")
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                continue

            # Comparar el texto del enlace con el título de la página
            safe_link_text = link_text.encode('ascii', 'ignore').decode()
            safe_page_title = page_title.encode('ascii', 'ignore').decode()

            if safe_link_text.lower() in safe_page_title.lower():
                enlaces_coinciden += 1
            else:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200, 10, txt=f"- Advertencia: El enlace '{safe_link_text}' NO coincide con el título de la página de destino: '{safe_page_title}'")
                
                # Guardar la captura de pantalla de la página de destino
                screenshot_path = os.path.join(enlaces_dir, f"enlace_{index}_captura.png")
                driver.save_screenshot(screenshot_path)

                # Redimensionar la imagen para hacerla 1.5 veces más grande, sin ocupar toda la página
                with Image.open(screenshot_path) as img:
                    original_width, original_height = img.size
                    new_width, new_height = int(original_width * 1.5), int(original_height * 1.5)
                    
                    # Asegurar que las dimensiones no excedan el tamaño de la página
                    max_width, max_height = 150, 150
                    new_width = min(new_width, max_width)
                    new_height = min(new_height, max_height)

                    img_resized = img.resize((new_width, new_height))
                    resized_screenshot_path = os.path.join(enlaces_dir, f"enlace_{index}_captura_resized.png")
                    img_resized.save(resized_screenshot_path)

                    # Añadir la captura al PDF
                    pdf.image(resized_screenshot_path, x=15, y=None)

            # Cerrar la pestaña actual y volver a la original
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

    # Añadir el resumen de los enlaces que coinciden al PDF
    pdf.set_font("Arial", size=10)
    pdf.set_x(15)
    pdf.multi_cell(200, 10, txt=f"- Número de enlaces que coinciden con el título de la página de destino: {enlaces_coinciden}")

    # Guardar el PDF con los resultados
    #output_filename = "reporte_coherencia_enlaces.pdf"
    #pdf.output(output_filename, dest='F')  # Guardar usando 'utf-8'

    # Cerrar el navegador
    #driver.quit()

    # Eliminar el directorio de capturas al finalizar
    if os.path.exists(capturas_dir):
        shutil.rmtree(capturas_dir)

def verificar_enlaces_genericos(url):
    # Configurar Selenium con Chrome en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless=old")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    
    pdf.add_page()
    pdf.cell(200, 10, txt="Verificación de Enlaces con Texto Genérico", ln=True, align='C')

    # Navegar a la URL
    driver.get(url)

    # Buscar todos los enlaces visibles
    enlaces = driver.find_elements(By.TAG_NAME, 'a')
    textos_genericos = ["click aquí", "haga clic aquí", "aquí", "leer más", "ver más", "más información"]

    enlaces_genericos_count = 0  # Contador de enlaces genéricos
    enlaces_correctos_count = 0  # Contador de enlaces correctos

    for enlace in enlaces:
        if enlace.is_displayed() and enlace.get_attribute('href'):
            link_text = enlace.text.strip().lower()

            # Verificar si el texto del enlace es genérico
            if any(texto_generico in link_text for texto_generico in textos_genericos):
                enlaces_genericos_count += 1
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.cell(200, 10, txt=f"- Advertencia: Enlace con texto genérico encontrado: '{link_text}'", ln=True)
            else:
                enlaces_correctos_count += 1

    # Añadir resumen al PDF
    pdf.set_font("Arial", size=10)
    pdf.set_x(15)
    pdf.cell(200, 10, txt=f"- Número total de enlaces con texto descriptivo: {enlaces_correctos_count}", ln=True)

    # Guardar el PDF con los resultados
    #output_filename = "reporte_enlaces_genericos.pdf"
    #pdf.output(output_filename, dest='F')

    # Cerrar el navegador
    driver.quit()


url = "https://www.mercadolibre.cl"  # URL de ejemplo
hdu_tres(url)
verificar_enlaces_coherencia_titulo(url)
verificar_enlaces_genericos(url)

output_filename = "reporte_legibilidad_ui.pdf"
pdf.output(output_filename)