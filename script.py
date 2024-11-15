import cv2
import os
from firebase_admin import credentials, initialize_app, storage, firestore
from io import BytesIO
from fpdf import FPDF
from firebase_admin import credentials, storage
import sys
import shutil
from flask import jsonify
from fpdf import FPDF
from requests import request
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from IPython.display import display, Image
import subprocess
from inference_sdk import InferenceHTTPClient
from dataclasses import dataclass
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from requests_html import AsyncHTMLSession
import time
import re
import spacy
from PIL import Image
from io import BytesIO
from collections import Counter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse
from collections import defaultdict
from spellchecker import SpellChecker
from fpdf import FPDF
from urllib.parse import urlparse, unquote

# Crea un objeto PDF
pdf = FPDF()

# Agrega una página
pdf.add_page()

# Establece la fuente (tipografía y tamaño)
pdf.set_font("Arial", size=14)

# Agrega un título
pdf.cell(200, 10, txt="Revisión de Criterios Usabilidad Web.", ln=True, align='C')

output_folder = "output_images"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Obtener la ruta del video desde los argumentos de la línea de comandos
video_path = sys.argv[1]
url = sys.argv[2]
categorias = sys.argv[3].split(',')
id = sys.argv[4]
idP = sys.argv[5]

print(video_path)
print(url)
print(categorias[0])

# Crear una carpeta para guardar las capturas si no existe
output_dir = 'capturas'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Abrir el video con la función moderna de scenedetect
video = open_video(video_path)

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
# Configurar Selenium con Chrome
chrome_options = Options()
chrome_options.add_argument("--headless=old")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
nlp = spacy.load("en_core_web_md")

def hdu_uno(url):
    # Navegar a la URL
    driver.get(url)
    
    # Obtener el contenido de la página renderizada
    html_content = driver.page_source

    # --- Criterios de Usabilidad ---

    # 1. Búsqueda de campos de búsqueda con diferentes atributos y validaciones adicionales
    search_fields = driver.find_elements(By.CSS_SELECTOR, 'input[type="search"], input[name*="search"], input[placeholder*="search"], input[type="text"][name*="search"], input[type="text"][placeholder*="search"], form[action*="search"] input')

    # Inicializar un contador de campos de búsqueda válidos
    valid_search_fields_count = 0
    
    pdf.ln(10)

    pdf.set_font("Arial", size=11)

    pdf.cell(200, 10, txt="Página de Inicio", align='C')

    pdf.set_font("Arial", size=10)

    # Agrega un título
    pdf.cell(200, 10, txt="Campos de búsqueda:", ln=True, align='L')

    if search_fields:
        for field in search_fields:
            issues = []
            # Verificar si el campo de búsqueda tiene atributos de accesibilidad
            aria_label = field.get_attribute('aria-label')
            title_attr = field.get_attribute('title')
            if not (aria_label or title_attr):
                issues.append("No tiene atributos de acceso ('aria-label' o 'title').")

            # Verificar visibilidad y tamaño
            if not field.is_displayed() or field.size['width'] <= 100:
                issues.append("Podría no ser visible o su tamaño es insuficiente.")
            else:
                # Obtener la posición del campo de búsqueda
                location = field.location
                if location['y'] >= 600:
                    issues.append(f"Ubicación inusual para un campo de búsqueda (posicionada en y={location['y']}).")

            # Comprobar si el campo de búsqueda está dentro de un contenedor de cabecera
            parent_header = field.find_elements(By.XPATH, "ancestor::header")
            if not parent_header:
                issues.append("No está ubicado dentro de la cabecera.")

            if issues:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, f"- Problemas encontrados en un campo de búsqueda ({field.get_attribute('name')}'): " + " // ".join(issues))
            else:
                valid_search_fields_count += 1
        pdf.set_font("Arial", size=8)
        if valid_search_fields_count > 0:
            pdf.set_x(15)
            pdf.multi_cell(0, 8, f"- {valid_search_fields_count} campo(s) de búsqueda válido(s) y bien posicionado(s) detectado(s).")
    else:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 8,"- Campo de búsqueda NO detectado.")

    pdf.set_font("Arial", size=10)
    # Agrega un título
    pdf.cell(200, 10, txt="Palabras Clave:", ln=True, align='L')

    # 2. Verificación de palabras clave en enlaces
    N = 3
    def obtener_palabras_clave_frecuentes(texto, min_frecuencia):
        palabras = re.findall(r'\b\w+\b', texto.lower())
        palabras_filtradas = [palabra for palabra in palabras if len(palabra) > 3]
        contador_palabras = Counter(palabras_filtradas)
        return {palabra: frecuencia for palabra, frecuencia in contador_palabras.items() if frecuencia >= min_frecuencia}

    # Extraer todo el texto de los enlaces
    enlaces = driver.find_elements(By.TAG_NAME, 'a')
    todo_el_texto = ' '.join([enlace.text.strip() for enlace in enlaces])
    palabras_clave_frecuentes = obtener_palabras_clave_frecuentes(todo_el_texto, N)

    enlaces_con_palabras_clave = []
    palabras_usadas = set()
    
    for enlace in enlaces:
        texto_enlace = enlace.text.strip().lower()
        if texto_enlace:
            for palabra in palabras_clave_frecuentes:
                if palabra in texto_enlace and palabra not in palabras_usadas:
                    enlaces_con_palabras_clave.append(f"Enlace: '{texto_enlace}' contiene la palabra clave: '{palabra}'.")
                    palabras_usadas.add(palabra)
                    break

    if enlaces_con_palabras_clave:
        for detalle in enlaces_con_palabras_clave:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 8, '- ' + ' '.join(detalle.split()))

    else:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 8, f"- No se encontraron enlaces que contengan palabras clave que aparezcan al menos {N} veces.")

    pdf.set_font("Arial", size=10)
    # Agrega un título
    pdf.cell(200, 10, txt="Imágenes Genéricas:", ln=True, align='L')

    # Función para extraer el nombre del archivo de una URL
    def obtener_nombre_archivo(src):
        # Quitar los parámetros después del '?'
        parsed_url = urlparse(src)
        clean_url = parsed_url.path
        # Decodificar caracteres especiales (%20 por espacios, etc.)
        decoded_url = unquote(clean_url)
        # Extraer la última parte de la URL, que normalmente es el nombre del archivo
        nombre_archivo = decoded_url.split('/')[-1]
        return nombre_archivo

    # Continuación del código original
    nlp = spacy.load("en_core_web_md")
    palabras_clave_negativas = [
        'clipart', 'generic', 'placeholder', 'dummy', 'image1', 'stock',
        'shutterstock', 'getty', 'example', 'lorem', 'ipsum', 'filler', 'template'
    ]
    mensajes_advertencia = []
    conteo_errores_imagenes = 0

    imagenes = driver.find_elements(By.TAG_NAME, 'img')
    for img in imagenes:
        alt_text = img.get_attribute('alt').strip().lower()
        src = img.get_attribute('src').strip().lower()
        problema_detectado = False

        # Obtener solo el nombre del archivo
        nombre_archivo = obtener_nombre_archivo(src)

        # Validar que la imagen tenga texto alternativo significativo
        if not alt_text:
            mensajes_advertencia.append(f"- Imagen sin descripción adecuada. Archivo: {nombre_archivo}")
            problema_detectado = True
        else:
            # Verificar si el texto alternativo o el src contienen términos genéricos o problemáticos
            if any(negativa in alt_text for negativa in palabras_clave_negativas) or any(negativa in src for negativa in palabras_clave_negativas):
                mensajes_advertencia.append(f"- Imagen genérica o de baja calidad detectada. Archivo: {nombre_archivo} con descripción '{alt_text}'")
                problema_detectado = True

        # Verificación de dimensiones de imagen usando Selenium
        width = img.size['width']
        height = img.size['height']

        if width < 50 or height < 50:
            mensajes_advertencia.append(f"- Imagen muy pequeña detectada. Archivo: {nombre_archivo}")
            problema_detectado = True
        elif width / height < 0.5 or width / height > 2:
            mensajes_advertencia.append(f"- Imagen con dimensiones inusuales detectada. Archivo: {nombre_archivo}")
            problema_detectado = True

        # Verificar si el nombre del archivo de la imagen en el src indica que podría ser genérica
        if re.search(r'\b(?:img|image|placeholder|stock)\b', src):
            mensajes_advertencia.append(f"- El nombre del archivo sugiere que la imagen podría ser genérica. Archivo: {nombre_archivo}")
            problema_detectado = True

        if problema_detectado:
            conteo_errores_imagenes += 1

    if mensajes_advertencia:
        for mensaje in mensajes_advertencia:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 8, mensaje)

        if conteo_errores_imagenes >= 5:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 8, f"- Se encontraron {conteo_errores_imagenes} problemas con las imágenes del sitio.")
    else:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 8, "- Validación de imágenes completada sin problemas.")


    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Optimización en buscadores:", ln=True, align='L')
    # 4. Optimización del título para buscadores
    nlp = spacy.load("en_core_web_md")
    title_tag = driver.find_element(By.TAG_NAME, 'title').text
    mensajes_advertencia = []

    if title_tag:
        title_text = title_tag.strip()

        if 50 <= len(title_text) <= 60:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 8, "- Título con longitud óptima para buscadores:", title_text)
        elif len(title_text) < 50:
            mensajes_advertencia.append(f"- El título es demasiado corto ({len(title_text)} caracteres): {title_text}")
        else:
            mensajes_advertencia.append(f"- El título es demasiado largo ({len(title_text)} caracteres): {title_text}")

        # Análisis de palabras clave en el título
        page_content = " ".join([p.text for p in driver.find_elements(By.TAG_NAME, 'p')])
        title_similarity = nlp(title_text).similarity(nlp(page_content))

        if title_similarity < 0.2:
            mensajes_advertencia.append(f"- El título '{title_text}' puede no ser relevante para el contenido de la página.")
        else:
            print(f"- El título es semánticamente relevante con una similitud de {title_similarity:.2f} con el contenido de la página.")
    else:
        mensajes_advertencia.append("- Error crítico: No se encontró un título en la página.")

    if mensajes_advertencia:
        for mensaje in mensajes_advertencia:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 8, mensaje)

    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Información Corporativa:", ln=True, align='L')
    # 5. Información corporativa en la página
    palabras_clave_corporativas = [
        "acerca de", "sobre nosotros", "about", "about us", "empresa", "quiénes somos",
        "compañía", "our company", "our team", "our story", "historia", "nuestra empresa", "contacto", "contact us"
    ]

    secciones_corporativas = driver.find_elements(By.TAG_NAME, 'footer') + driver.find_elements(By.TAG_NAME, 'div')
    corporate_info_detectada = False

    for section in secciones_corporativas:
        section_text = section.text.lower()

        if any(keyword in section_text for keyword in palabras_clave_corporativas):
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 8, "- Información corporativa detectada correctamente.")
            corporate_info_detectada = True
            break

    if not corporate_info_detectada:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 8, "- Información corporativa NO detectada.")

    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Sencillez de URL:", ln=True, align='L')
    # 6. URL sencilla y fácil de recordar
    url_parts = urlparse(url)
    path = url_parts.path.strip('/')
    path_segments = path.split('/')
    query = url_parts.query

    url_simple = True
    mensajes_advertencia = []

    if query:
        url_simple = False
        mensajes_advertencia.append(f"- URL compleja: contiene parámetros en la cadena de consulta: '{query}'")
    if len(url) > 100:
        url_simple = False
        mensajes_advertencia.append(f"- URL demasiado larga: {len(url)} caracteres")
    if len(path_segments) > 2:
        url_simple = False
        mensajes_advertencia.append(f"- URL con múltiples subdirectorios: {'/'.join(path_segments)}")

    if url_simple:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 8, "- La URL es sencilla y fácil de recordar:", url)
    else:
        for mensaje in mensajes_advertencia:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 8, mensaje)

    #driver.quit()
    

def obtener_atributo_safe(elemento, atributo, max_intentos=3):
    intento = 0
    while intento < max_intentos:
        try:
            return elemento.get_attribute(atributo)
        except StaleElementReferenceException:
            intento += 1
            time.sleep(0.5)  # Esperar brevemente antes de intentar de nuevo
    return None  # Si después de varios intentos no se puede obtener, devuelve None

def hdu_dos(url):
    driver.get(url)
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 10, txt="Orientación de Tareas", ln=True, align='C')

    # --- Análisis de Recursos ---
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Recuento y análisis de recursos cargados:", ln=True, align='L')

    # Recuento y análisis de scripts
    scripts = driver.find_elements(By.TAG_NAME, 'script')
    large_scripts = [script for script in scripts if obtener_atributo_safe(script, 'src') and len(obtener_atributo_safe(script, 'src')) > 0]
    
    pdf.set_font("Arial", size=8)
    pdf.set_x(15)
    pdf.multi_cell(200, 10, txt=f"- Se encontró {len(scripts)} script{'s' if len(scripts) != 1 else ''} en la página.")

    if large_scripts:
        pdf.set_x(15)
        pdf.multi_cell(200, 10, txt=f"- Script{'s' if len(large_scripts) != 1 else ''} con fuente externa: {len(large_scripts)}")

    # Recuento y análisis de videos
    videos = driver.find_elements(By.TAG_NAME, 'video')
    pdf.set_x(15)
    pdf.multi_cell(200, 10, txt=f"- Se encontró {len(videos)} video{'s' if len(videos) != 1 else ''} en la página.")
    
    for video in videos:
        video_size = int(obtener_atributo_safe(video, 'size')) if obtener_atributo_safe(video, 'size') else 0
        if video_size > 5000000:  # Umbral ajustable, por ejemplo, 5MB
            pdf.set_x(15)
            pdf.multi_cell(200, 10, txt=f"- Advertencia: Video grande detectado con tamaño {video_size / 1000000:.2f}MB")

    # Recuento y análisis de imágenes
    imagenes = driver.find_elements(By.TAG_NAME, 'img')
    pdf.set_x(15)
    pdf.multi_cell(200, 10, txt=f"- Se encontró {len(imagenes)} imagen{'es' if len(imagenes) != 1 else ''} en la página.")
    
    for img in imagenes:
        width = img.size['width']
        height = img.size['height']
        if width < 50 or height < 50:
            pdf.set_x(15)
            pdf.multi_cell(200, 10, txt=f"- Advertencia: Imagen muy pequeña detectada (dimensiones: {width}x{height}px)")
        elif width / height < 0.5 or width / height > 2:
            pdf.set_x(15)
            pdf.multi_cell(200, 10, txt=f"- Advertencia: Imagen con dimensiones inusuales detectada (dimensiones: {width}x{height}px)")

    # Recuento y análisis de archivos de audio
    audios = driver.find_elements(By.TAG_NAME, 'audio')
    pdf.set_x(15)
    pdf.multi_cell(200, 10, txt=f"- Se encontró {len(audios)} archivo{'s de audio' if len(audios) != 1 else ' de audio'} en la página.")

    # Recuento y análisis de applets
    applets = driver.find_elements(By.TAG_NAME, 'applet')
    pdf.set_x(15)
    pdf.multi_cell(200, 10, txt=f"- Se encontró {len(applets)} applet{'s' if len(applets) != 1 else ''} en la página.")
    if applets:
        pdf.set_x(15)
        pdf.multi_cell(200, 10, txt="- Advertencia: Uso de applets detectado. Esto podría afectar la compatibilidad y rendimiento de la página.")

    # Evaluación de la cantidad total de recursos
    total_resources = len(scripts) + len(videos) + len(imagenes) + len(audios) + len(applets)
    if total_resources > 50:
        pdf.set_x(15)
        pdf.multi_cell(200, 10, txt=f"- Advertencia: Se cargaron {total_resources} recursos en la página, lo que puede afectar el rendimiento.")
    else:
        pdf.set_x(15)
        pdf.multi_cell(200, 10, txt=f"- Cantidad total de recursos cargados en la página: {total_resources}")

    # --- Detección de Barreras Innecesarias ---
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Detección de Barreras Innecesarias:", ln=True, align='L')
    pdf.set_font("Arial", size=8)
    # 1. Detección de formularios de registro
    try:
        registration_forms = driver.find_elements(By.CSS_SELECTOR, 'form[action*="register"], form[action*="signup"], form[action*="subscribe"]')
        if registration_forms:
            for form in registration_forms:
                if form.is_displayed():
                    pdf.set_x(15)
                    pdf.multi_cell(200,10,txt= f"- Formulario de registro detectado: {form.get_attribute('action')}")
                    #print(f"Formulario de registro detectado: {form.get_attribute('action')}")
                else:
                    pdf.set_x(15)
                    pdf.multi_cell(200,10,txt= f"- Formulario de registro no visible: {form.get_attribute('action')}")
                    #print(f"Formulario de registro no visible: {form.get_attribute('action')}")
        else:
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= "- No se encontraron formularios de registro visibles en la página.")
            #print("No se encontraron formularios de registro visibles en la página.")
    except NoSuchElementException:
        #pdf.multi_cell(200,10,txt= "Error al buscar formularios de registro.")
        print("Error al buscar formularios de registro.")

    # 2. Detección de ventanas modales de suscripción
    try:
        modals = driver.find_elements(By.CSS_SELECTOR, '[class*="modal"], [class*="popup"], [class*="subscribe"], [class*="signup"]')
        modal_detected = False
        for modal in modals:
            if modal.is_displayed():
                modal_text = modal.text.lower()
                if any(keyword in modal_text for keyword in ['registrarse', 'suscribirse', 'register', 'sign up', 'subscribe']):
                    pdf.set_x(15)
                    pdf.multi_cell(200,10,txt= f"- Ventana modal de suscripción detectada con contenido relevante: {modal_text[:100]}...")
                    #print(f"Ventana modal de suscripción detectada con contenido relevante: {modal_text[:100]}...")
                    modal_detected = True
                else:
                    pdf.set_x(15)
                    pdf.multi_cell(200,10,txt= f"- Ventana modal detectada, pero no parece relacionada con el registro o suscripción: {modal_text[:100]}...")
                    #print(f"Ventana modal detectada, pero no parece relacionada con el registro o suscripción: {modal_text[:100]}...")
        if not modal_detected:
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= "- No se encontraron ventanas modales de suscripción que bloqueen el acceso al contenido.")
            #print("No se encontraron ventanas modales de suscripción que bloqueen el acceso al contenido.")
    except NoSuchElementException:
        #pdf.multi_cell(200,10,txt= "Error al buscar ventanas modales de suscripción.")
        print("Error al buscar ventanas modales de suscripción.")

    # 3. Verificación de posibilidad de cierre de modales
    try:
        close_buttons = driver.find_elements(By.CSS_SELECTOR, '[class*="close"], button[class*="close"], button[class*="cancel"]')
        for button in close_buttons:
            if button.is_displayed() and button.is_enabled():
                pdf.set_x(15)
                pdf.multi_cell(200,10,txt= "- Botón de cierre de ventana modal detectado y habilitado.")
                #print("Botón de cierre de ventana modal detectado y habilitado.")
            else:
                pdf.set_x(15)
                pdf.multi_cell(200,10,txt= "- Advertencia: Botón de cierre de ventana modal no disponible o no visible.")
                #print("Advertencia: Botón de cierre de ventana modal no disponible o no visible.")
    except NoSuchElementException:
        print("Error al buscar botones de cierre para ventanas modales.")

    # --- Cantidad de Ventanas/Pestañas Abiertas ---
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Cantidad de pestañas durante navegación:", ln=True, align='L')
    pdf.set_font("Arial", size=8)
    # Obtener el número inicial de ventanas/pestañas abiertas
    initial_window_handles = driver.window_handles
    initial_window_count = len(initial_window_handles)
    pdf.set_x(15)
    pdf.multi_cell(200,10,txt= f"- Cantidad inicial de ventanas/pestañas abiertas: {initial_window_count}")
    #print(f"Cantidad inicial de ventanas/pestañas abiertas: {initial_window_count}")

    # Inicializar current_window_count
    current_window_count = initial_window_count

    # Ejecutar una acción para verificar si se abren nuevas ventanas/pestañas
    try:
        potential_link = driver.find_element(By.CSS_SELECTOR, 'a[target="_blank"]')
        potential_link_text = potential_link.text or potential_link.get_attribute('href')
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= f"- Se hizo clic en el enlace que potencialmente abre nueva pestaña: '{potential_link_text}'")
        #print(f"Se hizo clic en el enlace que potencialmente abre nueva pestaña: '{potential_link_text}'")

        potential_link.click()

        # Esperar un momento para permitir la apertura de la nueva pestaña
        time.sleep(2)

        # Comprobar el número de ventanas/pestañas después de la acción
        current_window_handles = driver.window_handles
        current_window_count = len(current_window_handles)

        if current_window_count > initial_window_count:
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- Se abrieron {current_window_count - initial_window_count} nueva(s) ventana(s)/pestaña(s) al hacer clic en el enlace: '{potential_link_text}'.")
            #print(f"Se abrió(eron) {current_window_count - initial_window_count} nueva(s) ventana(s)/pestaña(s) al hacer clic en el enlace: '{potential_link_text}'.")
        else:
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- No se abrió ninguna nueva ventana/pestaña al hacer clic en el enlace: '{potential_link_text}'.")
            #print(f"No se abrió ninguna nueva ventana/pestaña al hacer clic en el enlace: '{potential_link_text}'.")
    except NoSuchElementException:
        pdf.set_x(15)
        pdf.multi_cell(200,10,"- No se encontró un enlace que abra una nueva ventana o pestaña.")

    # Evaluación final de ventanas abiertas
    if current_window_count > initial_window_count:
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= f"- Advertencia: Se abrieron {current_window_count - initial_window_count} nueva(s) ventana(s)/pestaña(s), lo que podría afectar la experiencia del usuario.")
        #print(f"Advertencia: Se abrió(eron) {current_window_count - initial_window_count} nueva(s) ventana(s)/pestaña(s), lo que podría afectar la experiencia del usuario.")
    else:
        pdf.set_x(15)
        pdf.multi_cell(200,10, "- Navegación sin apertura de ventanas/pestañas adicionales innecesarias.")

    # --- Longitud y Cantidad de Clics ---
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Longitud de la página para tareas:", ln=True, align='L')
    pdf.set_font("Arial", size=8)
    # 1. Medición de la longitud de la página
    page_height = driver.execute_script("return document.body.scrollHeight")
    pdf.set_x(15)
    pdf.multi_cell(200,10,txt= f"- Altura total de la página: {page_height} píxeles")
    #print(f"Altura total de la página: {page_height} píxeles")

    if page_height > 3000:
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= "- Advertencia: La página es demasiado larga, lo que podría afectar la navegación eficiente.")
        #print("Advertencia: La página es demasiado larga, lo que podría afectar la navegación eficiente.")
    else:
        pdf.set_x(15)
        pdf.multi_cell(200,10,"- Longitud de la página dentro del rango aceptable.")


    # 2. Análisis de la cantidad de clics para completar una tarea clave (sección corporativa/contacto)
    palabras_clave_corporativas = [
        "acerca de", "sobre nosotros", "about", "about us", "empresa", "quiénes somos",
        "compañía", "our company", "our team", "our story", "historia", "nuestra empresa", "contacto", "contact us"
    ]

    click_count = 0
    seccion_encontrada = False

    for palabra in palabras_clave_corporativas:
        try:
            enlace_corporativo = driver.find_element(By.PARTIAL_LINK_TEXT, palabra)
            if enlace_corporativo.is_displayed():
                enlace_corporativo.click()
                click_count += 1
                seccion_encontrada = True
                pdf.set_x(15)
                pdf.multi_cell(200,10,txt= f"- Sección '{palabra}' encontrada en un enlace y accedida con {click_count} clic(s).")
                #print(f"Sección '{palabra}' encontrada en un enlace y accedida con {click_count} clic(s).")
                break
        except NoSuchElementException:
            continue

    if not seccion_encontrada:
        for palabra in palabras_clave_corporativas:
            try:
                secciones = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{palabra}')]")
                for seccion in secciones:
                    if seccion.is_displayed():
                        seccion_encontrada = True
                        pdf.set_x(15)
                        pdf.multi_cell(200,10,txt= f"- Sección '{palabra}' encontrada en un elemento no enlazado.")
                        #print(f"Sección '{palabra}' encontrada en un elemento no enlazado.")
                        break
                if seccion_encontrada:
                    break
            except NoSuchElementException:
                continue

    if seccion_encontrada and click_count > 0:
        if click_count > 3:
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- Advertencia: Se requieren {click_count} clics para acceder a la sección corporativa.")
            #print(f"Advertencia: Se requieren {click_count} clics para acceder a la sección corporativa.")
        else:
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- La sección corporativa fue accesible con {click_count} clic(s), dentro del rango aceptable.")
            #print(f"La sección corporativa fue accesible con {click_count} clic(s), dentro del rango aceptable.")
    elif seccion_encontrada and click_count == 0:
        pdf.set_x(15)
        pdf.multi_cell(200,10,"- Sección corporativa encontrada sin necesidad de clics adicionales.")
    else:
        pdf.set_x(15)
        pdf.multi_cell(200,10,"- No se encontró ninguna sección corporativa utilizando las palabras clave especificadas.")

    # 3. Verificación de la profundidad de navegación
    menus = driver.find_elements(By.CSS_SELECTOR, 'nav, ul, ol')
    depth_counts = []

    for menu in menus:
        depth = len(menu.find_elements(By.CSS_SELECTOR, 'ul ul'))  # Contar submenús anidados
        depth_counts.append(depth)

    if depth_counts:
        max_depth = max(depth_counts)
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= f"- Profundidad máxima de navegación detectada: {max_depth} niveles.")
        #print(f"Profundidad máxima de navegación detectada: {max_depth} niveles.")
        if max_depth > 2:
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= "- Advertencia: La estructura de navegación es demasiado profunda.")
            #print("Advertencia: La estructura de navegación es demasiado profunda.")
        else:
            pdf.set_x(15)
            pdf.multi_cell(200,10,"- La estructura de navegación es aceptablemente profunda.")
    else:
        pdf.set_x(15)
        pdf.multi_cell(200,10,"- No se detectaron menús con subniveles.")

    # --- Formularios y Un-Click ---
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Acciones Rápidas:", ln=True, align='L')
    pdf.set_font("Arial", size=8)
    # Búsqueda de formularios y verificación de autocompletar
    formularios = driver.find_elements(By.TAG_NAME, 'form')
    formularios_con_autocompletar = []
    formularios_con_un_click = []

    for form in formularios:
        # Verificar si el formulario tiene autocompletar habilitado
        autocomplete = form.get_attribute('autocomplete')
        if autocomplete and autocomplete.lower() != 'off':
            formularios_con_autocompletar.append(form)

        # Verificar si el formulario tiene botones de acción rápida (un-click)
        botones_un_click = form.find_elements(By.CSS_SELECTOR, 'button, input[type="submit"], input[type="button"]')
        for boton in botones_un_click:
            if 'one-click' in boton.get_attribute('class').lower() or 'quick' in boton.get_attribute('class').lower():
                formularios_con_un_click.append(form)
                break

    if formularios_con_autocompletar:
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= f"- Se encontraron {len(formularios_con_autocompletar)} formulario(s) con autocompletar habilitado.")
        #print(f"Se encontraron {len(formularios_con_autocompletar)} formularios con autocompletar habilitado.")
    else:
        pdf.set_x(15)
        pdf.multi_cell(200,10,"- No se encontraron formularios con autocompletar habilitado.")

    if formularios_con_un_click:
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= f"- Se encontraron {len(formularios_con_un_click)} formulario(s) con botones de acción rápida (un-click).")
        #print(f"Se encontraron {len(formularios_con_un_click)} formularios con botones de acción rápida (un-click).")
    else:
        pdf.set_x(15)
        pdf.multi_cell(200,10,"- No se encontraron formularios con botones de acción rápida (un-click).")

    # Evaluación final
    if not formularios_con_autocompletar and not formularios_con_un_click:
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= "- No se encontraron formularios con autocompletar ni con botones de acción rápida, podría considerarse una oportunidad de mejora en la usabilidad.")
        #print("No se encontraron formularios con autocompletar ni con botones de acción rápida, podría considerarse una oportunidad de mejora en la usabilidad.")
    #driver.quit()

def hdu_tres(url):
    # Navegar a la URL
    driver.get(url)

    pdf.ln(10)

    pdf.set_font("Arial", size=11)


    pdf.cell(200, 10, txt="Navegabilidad", align='C')
    
    pdf.ln(10)
    # --- Verificación de menús de navegación y enlaces visibles ---
    selectors = ['nav', 'ul', 'ol', '.menu', '.navbar', '.navigation']
    navigation_menus = []
    for selector in selectors:
        navigation_menus.extend(driver.find_elements(By.CSS_SELECTOR, selector))

    # Evaluación de la existencia de menús de navegación
    if navigation_menus:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 8, txt= f"- Se encontraron {len(navigation_menus)} menús de navegación.")
        #print(f"Se encontraron {len(navigation_menus)} menús de navegación.")
        for index, menu in enumerate(navigation_menus, start=1):
            items = menu.find_elements(By.TAG_NAME, 'li')
            visible_items = [item for item in items if item.is_displayed()]
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 8, txt= f"- Menú {index} con {len(visible_items)} elementos visibles.")
            #print(f"Menú {index} con {len(visible_items)} elementos visibles.")

            # Verificación de enlaces dentro del menú
            links = menu.find_elements(By.TAG_NAME, 'a')
            visible_links = [link for link in links if link.is_displayed()]
            if visible_links:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, txt= f"- Menú {index} con {len(visible_items)} elementos visibles.")
                print(f"Menú {index} tiene {len(visible_links)} enlaces visibles y clickeables.")
            else:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, f"- Advertencia: Menú {index} no tiene enlaces visibles y clickeables.")
                #print(f"Advertencia: Menú {index} no tiene enlaces visibles y clickeables.")
    else:
        print("No se encontraron menús de navegación.")

    # --- Verificación de un enlace para regresar a la página de inicio ---
    try:
        home_link = driver.find_element(By.CSS_SELECTOR, 'a[href="/"], a[rel="home"], a[class*="home"], a[href^="/index"]')
        if home_link.is_displayed():
            print("Enlace para regresar a la página de inicio detectado y visible.")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 8, "- Advertencia: El enlace para regresar a la página de inicio no es visible.")
            #print("Advertencia: El enlace para regresar a la página de inicio no es visible.")
    except NoSuchElementException:
        print("No se encontró un enlace para regresar a la página de inicio.")

    # --- Búsqueda de menús de navegación y análisis de su estructura ---
    total_items = 0
    deep_menus_count = 0
    max_depth = 0

    for menu in navigation_menus:
        items = menu.find_elements(By.TAG_NAME, 'li')
        total_items += len(items)

        submenus = menu.find_elements(By.CSS_SELECTOR, 'ul ul, ol ol')
        if submenus:
            deep_menus_count += 1
            depth = max(len(submenu.find_elements(By.TAG_NAME, 'ul, ol')) for submenu in submenus) + 1
            max_depth = max(max_depth, depth)

    if total_items > 0:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 8, f"- Se encontraron un total de {total_items} elementos en los menús de navegación.")
        #print(f"Se encontraron un total de {total_items} elementos en los menús de navegación.")
        if deep_menus_count > 0:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 8, f" - Se encontraron {deep_menus_count} menús de navegación profundos con una profundidad máxima de {max_depth} niveles.")
            #print(f"Se encontraron {deep_menus_count} menús de navegación profundos con una profundidad máxima de {max_depth} niveles.")
        else:
            print("Todos los menús de navegación son amplios (sin niveles profundos).")
    else:
        print("No se encontraron menús de navegación en la página.")

    # --- Verificación de la ubicación y clicabilidad de las pestañas de navegación ---
    tabs = driver.find_elements(By.CSS_SELECTOR, 'nav a, header a, .menu a, .navbar a')
    tabs_at_top = [tab for tab in tabs if tab.location['y'] < 200]

    if tabs_at_top:
        clickeable_tabs = [tab for tab in tabs_at_top if tab.is_displayed() and tab.is_enabled()]
        if clickeable_tabs:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 8, f"- Se encontraron {len(clickeable_tabs)} pestañas de navegación en la parte superior, todas clickeables.")
            #print(f"Se encontraron {len(clickeable_tabs)} pestañas de navegación en la parte superior, todas clickeables.")
            for index, tab in enumerate(clickeable_tabs, start=1):
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, f"- Pestaña {index}: Texto='{tab.text}', Posición Y={tab.location['y']}px")
                #print(f"Pestaña {index}: Texto='{tab.text}', Posición Y={tab.location['y']}px")
                tab.screenshot(f"pestana_{index}_captura.png")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 8, "- Se encontraron pestañas en la parte superior, pero ninguna es clickeable.")
            #print("Se encontraron pestañas en la parte superior, pero ninguna es clickeable.")
    else:
        print("No se encontraron pestañas de navegación en la parte superior.")

    top_containers = driver.find_elements(By.CSS_SELECTOR, 'header, .top-menu, .navbar, .top-navigation')
    for container in top_containers:
        if container.location['y'] < 200:
            container_tabs = container.find_elements(By.TAG_NAME, 'a')
            if container_tabs:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, f"- Contenedor de navegación superior encontrado con {len(container_tabs)} pestañas.")
                #print(f"Contenedor de navegación superior encontrado con {len(container_tabs)} pestañas.")
                container.screenshot(f"contenedor_superior_captura.png")
            else:
                print(f"Contenedor de navegación superior encontrado, pero sin pestañas clickeables.")

    # --- Verificación de la accesibilidad del contenido desde múltiples enlaces ---
    ruta_links = defaultdict(list)
    for link in driver.find_elements(By.TAG_NAME, 'a'):
        href = link.get_attribute('href')
        if href:
            parsed_url = urlparse(href)
            ruta = parsed_url.path
            ruta_links[ruta].append(link)

    rutas_con_multiples_enlaces = 0
    rutas_unicas = 0

    for ruta, links in ruta_links.items():
        if len(links) > 1:
            rutas_con_multiples_enlaces += 1
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 8, f"- Ruta '{ruta}' accesible desde {len(links)} enlaces diferentes.")
            #print(f"Ruta '{ruta}' accesible desde {len(links)} enlaces diferentes.")
            if rutas_con_multiples_enlaces == 1:
                links[0].screenshot(f"multiple_links_{ruta.strip('/').replace('/', '_')}.png")
        else:
            rutas_unicas += 1

    if rutas_con_multiples_enlaces > 0:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 8, f"- Se encontraron {rutas_con_multiples_enlaces} rutas accesibles desde múltiples enlaces.")
        #print(f"Se encontraron {rutas_con_multiples_enlaces} rutas accesibles desde múltiples enlaces.")
    else:
        print("No se encontraron rutas accesibles desde múltiples enlaces.")

    print(f"Total de rutas únicas: {rutas_unicas}")

    # --- Verificación de enlaces diferenciados para acciones especiales ---
    action_links = driver.find_elements(By.CSS_SELECTOR, 'a[target="_blank"], a[download], a[href^="javascript"], a[rel*="noopener"], a[rel*="noreferrer"], a[href*="file"], a[href*="download"], a[href*="pdf"]')

    if action_links:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 8, f"- Se encontraron {len(action_links)} enlaces que ejecutan acciones especiales (descargas, abrir nuevas ventanas).")
        print(f"Se encontraron {len(action_links)} enlaces que ejecutan acciones especiales (descargas, abrir nuevas ventanas).")
        for link in action_links:
            link_text = link.text.strip()
            href = link.get_attribute('href')

            if not link_text:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, f"- Advertencia: Enlace de acción especial sin texto visible. Enlace: {href}")
                #print(f"Advertencia: Enlace de acción especial sin texto visible. Enlace: {href}")
            else:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, f"- Enlace de acción especial encontrado: {link_text} - Enlace: {href}")
                print(f"Enlace de acción especial encontrado: {link_text} - Enlace: {href}")

            title_attr = link.get_attribute('title')
            aria_label = link.get_attribute('aria-label')
            if title_attr or aria_label:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, f"- Enlace mejorado con atributos de accesibilidad: title='{title_attr}', aria-label='{aria_label}'")
                print(f"Enlace mejorado con atributos de accesibilidad: title='{title_attr}', aria-label='{aria_label}'")
    else:
        print("No se encontraron enlaces con acciones especiales diferenciadas.")

    # --- Verificación de enlaces "Logo" y "Inicio" para regresar a la página principal ---
    try:
        logo_selectores = [
            'a[rel="home"]', 'a.logo', 'a[href="/"]', 'a[href*="index"]',
            'a[class*="logo"]', 'a[id*="logo"]', 'img[alt*="logo"]'
        ]
        home_selectores = [
            'a[title="Inicio"]', 'a[href="/home"]', 'a[href*="home"]', 'a[href*="index"]',
            'a[href*="main"]', 'a[title="Home"]', 'a[title="Página principal"]'
        ]

        logo_link = None
        home_link = None

        for selector in logo_selectores:
            try:
                logo_link = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except NoSuchElementException:
                continue

        for selector in home_selectores:
            try:
                home_link = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except NoSuchElementException:
                continue

        if logo_link and home_link:
            if logo_link.get_attribute('href') == home_link.get_attribute('href'):
                print("Tanto el logo como el botón de Inicio llevan al usuario de vuelta a la página principal.")
            else:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, "- El logo y el botón de Inicio no llevan al usuario de vuelta a la página principal de manera consistente.")
                #print("El logo y el botón de Inicio no llevan al usuario de vuelta a la página principal de manera consistente.")

            driver.get(logo_link.get_attribute('href'))
            if driver.current_url == logo_link.get_attribute('href'):
                print("El logo lleva correctamente a la página principal.")
            else:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, "- El logo no lleva correctamente a la página principal.")
                print("El logo no lleva correctamente a la página principal.")

            driver.get(home_link.get_attribute('href'))
            if driver.current_url == home_link.get_attribute('href'):
                print("El botón de Inicio lleva correctamente a la página principal.")
            else:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, "- El botón de Inicio no lleva correctamente a la página principal.")
                print("El botón de Inicio no lleva correctamente a la página principal.")
        else:
            if not logo_link:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, "- No se encontró el logo que lleve a la página principal.")
                print("No se encontró el logo que lleve a la página principal.")
            if not home_link:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, "- No se encontró el botón de Inicio que lleve a la página principal.")
                print("No se encontró el botón de Inicio que lleve a la página principal.")

    except NoSuchElementException:
        print("No se encontró el elemento de logo o botón de Inicio.")
    except Exception as e:
        pass

    # --- Verificación de consistencia en la ubicación de instrucciones, preguntas y mensajes ---
    try:
        instruction_elements = driver.find_elements(By.CSS_SELECTOR, '.instruction, .help-text, .error-message, .hint, .validation-message')

        if instruction_elements:
            locations = set((elem.location['x'], elem.location['y']) for elem in instruction_elements)

            if len(locations) == 1:
                print("Las instrucciones, preguntas y mensajes están ubicados consistentemente en el mismo lugar en cada página.")
            else:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, f"- Advertencia: Se encontró {len(locations)} ubicacion(es) distinta(s) para instrucciones, preguntas y mensajes.")
                #print(f"Advertencia: Se encontró {len(locations)} ubicacion(es) distinta(s) para instrucciones, preguntas y mensajes.")

            for elem in instruction_elements:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 8, f"- Elemento de instrucción encontrado en posición relativa X: {elem.location['x']} Y: {elem.location['y']}.")
                #print(f"Elemento de instrucción encontrado en posición relativa X: {elem.location['x']} Y: {elem.location['y']}.")
        else:
            print("No se encontraron elementos de instrucciones, preguntas o mensajes en la página.")
    except Exception as e:
        print(f"Error al verificar la consistencia de ubicación: {str(e)}")

    # --- Verificación de la existencia de páginas de ayuda y mensajes de error detallados ---
    try:
        help_pages = driver.find_elements(By.LINK_TEXT, 'Ayuda') + driver.find_elements(By.PARTIAL_LINK_TEXT, 'Help')
        error_pages = driver.find_elements(By.CSS_SELECTOR, '.error-message, .error-page, .alert-danger, .validation-error')

        if help_pages:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 8, f"- Se encontraron {len(help_pages)} páginas de ayuda disponibles.")
            print(f"Se encontraron {len(help_pages)} páginas de ayuda disponibles.")
        else:
            print("No se encontraron páginas de ayuda.")

        if error_pages:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 8, f"- Se encontraron {len(error_pages)} mensajes de error detallados.")
            #print(f"Se encontraron {len(error_pages)} mensajes de error detallados.")
        else:
            print("No se encontraron mensajes de error detallados.")
    except Exception as e:
        print(f"Error al verificar páginas de ayuda o mensajes de error: {str(e)}")

    # Cerrar el driver
    #driver.quit()

def hdu_cuatro(url):

    pdf.ln(10)

    pdf.set_font("Arial", size=11)

    pdf.cell(200, 10, txt="Formularios", align='C')
    
    pdf.ln(10)

    # Navegar a la URL
    driver.get(url)

    # 15. Verificación de valores predeterminados en campos de entrada
    input_fields = driver.find_elements(By.CSS_SELECTOR, 'input, textarea')
    for field in input_fields:
        field_type = field.get_attribute('type')
        field_name = field.get_attribute('name')
        field_placeholder = field.get_attribute('placeholder')
        default_value = field.get_attribute('value').strip()

        if default_value:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10, txt=f"- Campo de entrada '{field_name}' de tipo '{field_type}' con valor predeterminado: '{default_value}'")

            # Validar longitud del valor predeterminado
            if len(default_value) < 3 or len(default_value) > 255:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt=f"- Advertencia: El valor predeterminado para el campo '{field_name}' tiene una longitud inusual: {len(default_value)} caracteres.")

            # Validar estructura dependiendo del tipo de campo
            if field_type == 'email':
                if not re.match(r"[^@]+@[^@]+\.[^@]+", default_value):
                    pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                    pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                    pdf.multi_cell(200,10, txt=f"- Advertencia: El valor predeterminado para el campo de correo electrónico '{field_name}' no tiene una estructura válida.")

            elif field_type == 'tel':
                if not re.match(r"^\+?\d{10,15}$", default_value):
                    pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                    pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                    pdf.multi_cell(200,10, txt=f"- Advertencia: El valor predeterminado para el campo de teléfono '{field_name}' no tiene una estructura válida.")

            elif field_type == 'number':
                try:
                    float(default_value)
                except ValueError:
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10, txt=f"- Advertencia: El valor predeterminado para el campo numérico '{field_name}' no es un número válido.")

            elif field_type == 'text' and ('date' in field_name.lower() or 'date' in field_placeholder.lower()):
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", default_value):
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10, txt=f"- Advertencia: El valor predeterminado para el campo de fecha '{field_name}' no sigue el formato YYYY-MM-DD.")

            elif field_type == 'text' and ('currency' in field_name.lower() or 'currency' in field_placeholder.lower()):
                if not re.match(r"^\$?\d+(\.\d{2})?$", default_value):
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10, txt=f"- Advertencia: El valor predeterminado para el campo de moneda '{field_name}' no tiene un formato de moneda válido.")

            elif field_type == 'url':
                if not re.match(r"^(https?|ftp)://[^\s/$.?#].[^\s]*$", default_value):
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10, txt=f"- Advertencia: El valor predeterminado para el campo de URL '{field_name}' no tiene una estructura válida.")

            elif field_type == 'password':
                if len(default_value) < 8:
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10, txt=f"- Advertencia: El valor predeterminado para el campo de contraseña '{field_name}' es demasiado corto (menor a 8 caracteres).")

            elif field_type == 'checkbox' or field_type == 'radio':
                if default_value not in ['on', 'off']:
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10, txt=f"- Advertencia: El valor predeterminado para el campo de selección '{field_name}' tiene un valor inusual: '{default_value}'")

            # Validación adicional: campos que deberían estar vacíos
            if field_type == 'password' or field_type == 'hidden':
                if default_value:
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10, txt=f"- Advertencia: El campo '{field_name}' de tipo '{field_type}' no debería tener un valor predeterminado visible.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Campo de entrada '{field_name}' de tipo '{field_type}' no tiene valor predeterminado.")

        # Verificación adicional: uso de placeholders en lugar de valores predeterminados
        if field_placeholder:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Campo de entrada '{field_name}' con placeholder: '{field_placeholder}'")
            # Validación de longitud y formato según el placeholder
            if 'phone' in field_placeholder.lower() and not re.match(r"^\+?\d{10,15}$", default_value):
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt=f"- Advertencia: El valor del placeholder '{field_placeholder}' en el campo '{field_name}' no coincide con un formato de teléfono válido.")
            elif 'date' in field_placeholder.lower() and not re.match(r"^\d{4}-\d{2}-\d{2}$", default_value):
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt=f"- Advertencia: El valor del placeholder '{field_placeholder}' en el campo '{field_name}' no sigue el formato YYYY-MM-DD.")

    invalid_fields = [field for field in input_fields if not field.get_attribute('value') and not field.get_attribute('placeholder')]
    if invalid_fields:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200,10, txt=f"- Advertencia: Se encontraron {len(invalid_fields)} campos de entrada sin valores predeterminados ni placeholders útiles.")

    # 16. Verificación de formateo automático de datos
    for field in input_fields:
        field_name = field.get_attribute('name')
        field_type = field.get_attribute('type')
        pattern = field.get_attribute('pattern')
        input_mode = field.get_attribute('inputmode')
        placeholder = field.get_attribute('placeholder')
        autocomplete = field.get_attribute('autocomplete')

        if pattern or input_mode:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Campo '{field_name}' con formateo automático detectado (pattern: {pattern}, inputmode: {input_mode})")

        if input_mode:
            if input_mode == 'numeric' and field_type == 'text':
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt=f"- Campo '{field_name}' utiliza 'inputmode=numeric' para facilitar la entrada de datos numéricos.")
            elif input_mode == 'decimal' and field_type == 'text':
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt=f"- Campo '{field_name}' utiliza 'inputmode=decimal' para facilitar la entrada de números decimales.")

        if autocomplete:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Campo '{field_name}' tiene habilitado el autocompletado con 'autocomplete={autocomplete}'.")

    # 17. Detección de etiquetas para campos requeridos y opcionales
    palabras_clave_requerido = ['required', 'obligatorio', 'necesario', '*', 'must', 'mandatory']
    palabras_clave_opcional = ['optional', 'opcional']
    labels = driver.find_elements(By.CSS_SELECTOR, 'label')
    for label in labels:
        text = label.text.lower()

        if any(palabra in text for palabra in palabras_clave_requerido):
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Etiqueta de campo requerido detectada: {text}")
        elif any(palabra in text for palabra in palabras_clave_opcional):
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Etiqueta de campo opcional detectada: {text}")
        else:
            for_attr = label.get_attribute('for')
            associated_input = driver.find_element(By.ID, for_attr) if for_attr else None

            if associated_input:
                if associated_input.get_attribute('required'):
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10, txt=f"- Campo asociado a la etiqueta '{text}' es requerido basado en el atributo 'required'.")
                elif associated_input.get_attribute('aria-required') == 'true':
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10, txt=f"- Campo asociado a la etiqueta '{text}' es requerido basado en 'aria-required=true'.")
                else:
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10, txt=f"- Campo asociado a la etiqueta '{text}' no indica si es requerido u opcional.")
            else:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt=f"- Advertencia: No se encontró un campo asociado para la etiqueta '{text}'.")

    input_fields = driver.find_elements(By.CSS_SELECTOR, 'input, textarea, select')
    for field in input_fields:
        aria_label = field.get_attribute('aria-label')
        placeholder = field.get_attribute('placeholder')
        field_name = field.get_attribute('name')

        if field.get_attribute('required') or field.get_attribute('aria-required') == 'true':
            if aria_label:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt=f"- Campo '{aria_label}' es requerido basado en atributos ARIA.")
            elif placeholder:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt=f"- Campo con placeholder '{placeholder}' es requerido basado en atributos HTML.")
            else:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt=f"- Campo '{field_name}' es requerido pero no tiene una etiqueta visible asociada.")
        elif 'optional' in (aria_label or '').lower() or 'optional' in (placeholder or '').lower():
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Campo '{aria_label or placeholder}' es opcional.")

    print("Detección de etiquetas de campos completada.")

    # 18. Verificación del tamaño adecuado de cajas de texto
    for field in input_fields:
        field_type = field.get_attribute('type') or 'text'
        size = field.size['width']
        max_length = field.get_attribute('maxlength')
        min_length = field.get_attribute('minlength')
        placeholder = field.get_attribute('placeholder')

        size_thresholds = {
            'text': 150,
            'email': 200,
            'number': 100,
            'password': 150,
            'search': 200,
            'url': 250,
            'tel': 150
        }

        min_size = size_thresholds.get(field_type, 100)

        if size >= min_size:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Campo de tipo {field_type} con tamaño adecuado ({size}px de ancho).")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Advertencia: Campo de tipo {field_type} con tamaño insuficiente ({size}px de ancho).")

        if max_length:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Campo de tipo {field_type} tiene un 'maxlength' de {max_length}.")
        if min_length:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Campo de tipo {field_type} tiene un 'minlength' de {min_length}.")

        default_value = field.get_attribute('value') or ''
        if len(default_value) > 0 and size < len(default_value) * 8:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Advertencia: El valor predeterminado podría no ser completamente visible en el campo ({size}px de ancho).")
            #print(f"Advertencia: El valor predeterminado podría no ser completamente visible en el campo ({size}px de ancho).")

        if placeholder and size < len(placeholder) * 8:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Advertencia: El placeholder '{placeholder}' podría no ser completamente visible en el campo ({size}px de ancho).")
            #print(f"Advertencia: El placeholder '{placeholder}' podría no ser completamente visible en el campo ({size}px de ancho).")

    print("Verificación del tamaño de las cajas de texto completada.")

    # 19. Verificación de uso de listas de opciones, botones de radio y casillas en lugar de cajas de texto
    select_fields = driver.find_elements(By.TAG_NAME, 'select')
    radio_buttons = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
    checkboxes = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')

    if select_fields:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200,10, txt=f"- Se encontraron {len(select_fields)} listas de opciones.")
        #print(f"Se encontraron {len(select_fields)} listas de opciones.")
    else:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200,10, txt="- No se encontraron listas de opciones.")
        #print("No se encontraron listas de opciones.")

    if radio_buttons:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200,10, txt=f"- Se encontraron {len(radio_buttons)} botones de radio.")
        #print(f"Se encontraron {len(radio_buttons)} botones de radio.")
    else:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200,10, txt="- No se encontraron botones de radio.")
        #print("No se encontraron botones de radio.")

    if checkboxes:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200,10, txt=f"- Se encontraron {len(checkboxes)} casillas de verificación.")
        #print(f"Se encontraron {len(checkboxes)} casillas de verificación.")
    else:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200,10, txt="- No se encontraron casillas de verificación.")
        #print("No se encontraron casillas de verificación.")

    if not select_fields and not radio_buttons and not checkboxes:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200,10, txt="- Advertencia: No se encontraron listas de opciones, botones de radio o casillas de verificación, revisa si se está utilizando adecuadamente cajas de texto.")
        #print("Advertencia: No se encontraron listas de opciones, botones de radio o casillas de verificación, revisa si se está utilizando adecuadamente cajas de texto.")

    # 20. Verificación de posición automática del cursor en el campo adecuado
    focused_element = driver.switch_to.active_element
    if focused_element:
        field_name = focused_element.get_attribute('name') or focused_element.get_attribute('id')
        field_type = focused_element.get_attribute('type')

        form_elements = driver.find_elements(By.CSS_SELECTOR, 'input, select, textarea')
        first_relevant_element = form_elements[0] if form_elements else None

        if first_relevant_element and first_relevant_element == focused_element:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- El cursor está correctamente posicionado en el primer campo relevante: {field_name} de tipo {field_type}.")
            #print(f"El cursor está correctamente posicionado en el primer campo relevante: {field_name} de tipo {field_type}.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Advertencia: El cursor está en el campo: {field_name}, pero podría no ser el primer campo relevante.")
            #print(f"Advertencia: El cursor está en el campo: {field_name}, pero podría no ser el primer campo relevante.")
    else:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200,10, txt="- No se detectó que el cursor esté posicionado automáticamente en un campo.")
        #print("No se detectó que el cursor esté posicionado automáticamente en un campo.")

    # 21. Verificación de formatos claramente indicados en campos de entrada
    for field in input_fields:
        placeholder = field.get_attribute('placeholder')
        pattern = field.get_attribute('pattern')
        input_mode = field.get_attribute('inputmode')
        title = field.get_attribute('title')
        aria_label = field.get_attribute('aria-label')

        if placeholder:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f" -Campo con formato sugerido mediante placeholder: {placeholder}")
            #print(f"Campo con formato sugerido mediante placeholder: {placeholder}")

        if pattern:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Campo con validación mediante patrón: {pattern}")
            #print(f"Campo con validación mediante patrón: {pattern}")

        if input_mode:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Campo con sugerencia de input mode: {input_mode}")
            #print(f"Campo con sugerencia de input mode: {input_mode}")

        if title:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Campo con formato descrito en el título: {title}")
            #print(f"Campo con formato descrito en el título: {title}")

        if aria_label:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Campo con indicación de formato en aria-label: {aria_label}")
            #print(f"Campo con indicación de formato en aria-label: {aria_label}")

        if not any([placeholder, pattern, input_mode, title, aria_label]):
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- Advertencia: El campo {field.get_attribute('name') or field.get_attribute('id')} no tiene una indicación clara de formato.")
            #print(f"Advertencia: El campo {field.get_attribute('name') or field.get_attribute('id')} no tiene una indicación clara de formato.")

    # 22. Validación automática de formularios
    forms = driver.find_elements(By.TAG_NAME, 'form')
    for form in forms:
        if not form.get_attribute('novalidate'):
            form_id_or_name = form.get_attribute('id') or form.get_attribute('name')
            if form_id_or_name:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt=f"- Formulario con validación automática detectado: {form_id_or_name}")
                #print(f"Formulario con validación automática detectado: {form_id_or_name}")
            else:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt="- Formulario sin ID o nombre específico detectado, pero con validación automática.")
                #print("Formulario sin ID o nombre específico detectado, pero con validación automática.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt="- Formulario sin validación automática detectado.")
            #print("Formulario sin validación automática detectado.")

    # 23. Verificación de validación en tiempo real de los campos de entrada
    for field in input_fields:
        outer_html = field.get_attribute('outerHTML')
        if any(event in outer_html for event in ['oninput', 'onchange', 'onblur']) or \
          any(attr in field.get_attribute('outerHTML') for attr in ['pattern', 'required', 'maxlength']):
            field_name_or_id = field.get_attribute('name') or field.get_attribute('id')
            if field_name_or_id:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt=f"- Campo con validación en tiempo real detectado: {field_name_or_id}")
                #print(f"Campo con validación en tiempo real detectado: {field_name_or_id}")
            else:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt="- Campo sin ID o nombre específico detectado, pero con validación en tiempo real.")
                #print("Campo sin ID o nombre específico detectado, pero con validación en tiempo real.")

    # 25. Verificación de la posición de etiquetas cerca de los campos correspondientes
    labels = driver.find_elements(By.TAG_NAME, 'label')
    for label in labels:
        associated_field_id = label.get_attribute('for')
        if associated_field_id:
            try:
                field = driver.find_element(By.ID, associated_field_id)
                if field.is_displayed():
                    vertical_distance = abs(label.location['y'] - field.location['y'])
                    horizontal_distance = abs(label.location['x'] - field.location['x'])
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10, txt=f"- Etiqueta '{label.text}' está a {vertical_distance}px verticalmente y a {horizontal_distance}px horizontalmente de su campo asociado.")

                    #print(f"Etiqueta '{label.text}' está a {vertical_distance}px verticalmente y a {horizontal_distance}px horizontalmente de su campo asociado.")
                else:
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10, txt=f"- Campo asociado con ID '{associated_field_id}' no está visible.")
                    #print(f"Campo asociado con ID '{associated_field_id}' no está visible.")
            except NoSuchElementException:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt=f"- No se encontró el campo con ID '{associated_field_id}' asociado a la etiqueta '{label.text}'.")
                #print(f"No se encontró el campo con ID '{associated_field_id}' asociado a la etiqueta '{label.text}'.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10, txt=f"- La etiqueta '{label.text}' no está asociada con ningún campo.")
            #print(f"La etiqueta '{label.text}' no está asociada con ningún campo.")

    # 26. Verificación de la posibilidad de cambiar valores predeterminados
    for field in input_fields:
        field_name_or_id = field.get_attribute('name') or field.get_attribute('id')
        try:
            # Verificación de que el campo está habilitado, no es de solo lectura, es visible y es un campo de entrada
            if field.is_enabled() and not field.get_attribute('readonly') and field.is_displayed() and field.tag_name in ['input', 'textarea']:
                original_value = field.get_attribute('value')
                test_value = "test_value"

                try:
                    # Intentar cambiar el valor del campo solo si es de tipo texto, email, etc.
                    if field.get_attribute('type') in ['text', 'email', 'password', 'search', 'tel', 'url']:
                        field.clear()
                        field.send_keys(test_value)

                        # Verificación de que el valor se ha cambiado
                        if field.get_attribute('value') == test_value:
                            pdf.set_font("Arial", size=8)
                            pdf.set_x(15)
                            pdf.multi_cell(200,10, txt=f"- El campo '{field_name_or_id}' permite cambiar el valor predeterminado.")
                            #print(f"El campo '{field_name_or_id}' permite cambiar el valor predeterminado.")
                        else:
                            pdf.set_font("Arial", size=8)
                            pdf.set_x(15)
                            pdf.multi_cell(200,10, txt=f"- El campo '{field_name_or_id}' NO permite cambiar el valor predeterminado, cambio fallido.")
                            #print(f"El campo '{field_name_or_id}' NO permite cambiar el valor predeterminado, cambio fallido.")
                    else:
                        pdf.set_font("Arial", size=8)
                        pdf.set_x(15)
                        pdf.multi_cell(200,10, txt=f"- El campo '{field_name_or_id}' no es un tipo de campo editable (tipo {field.get_attribute('type')}).")
                        #print(f"El campo '{field_name_or_id}' no es un tipo de campo editable (tipo {field.get_attribute('type')}).")
                except Exception as interaction_error:
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10, txt=f"- Hubo un problema al intentar cambiar el valor del campo '{field_name_or_id}': {interaction_error}")
                    #print(f"Hubo un problema al intentar cambiar el valor del campo '{field_name_or_id}': {interaction_error}")

                # Intentar restaurar el valor original si fue cambiado
                try:
                    if field.get_attribute('type') in ['text', 'email', 'password', 'search', 'tel', 'url']:
                        field.clear()
                        field.send_keys(original_value)
                except Exception as restore_error:
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10, txt=f"- Hubo un problema al intentar restaurar el valor original del campo '{field_name_or_id}': {restore_error}")
                    #print(f"Hubo un problema al intentar restaurar el valor original del campo '{field_name_or_id}': {restore_error}")
            else:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10, txt=f"- El campo '{field_name_or_id}' está deshabilitado, es de solo lectura, no es visible, o no es un campo de entrada.")
                #print(f"El campo '{field_name_or_id}' está deshabilitado, es de solo lectura, no es visible, o no es un campo de entrada.")
        except Exception as e:
            print(f"Hubo un problema al interactuar con el campo '{field_name_or_id}': {e}")

    # Cerrar el driver
    driver.quit
    
    
def is_element_displayed_safely(element, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Verificar si el elemento está visible
            return element.is_displayed()
        except StaleElementReferenceException:
            # Si ocurre un error de referencia obsoleta, esperar y reintentar
            time.sleep(0.5)
    return False  # Si no se puede verificar después de varios intentos, retornar False
    
def hdu_cinco(url): 

    pdf.ln(10)

    pdf.set_font("Arial", size=11)

    pdf.cell(200, 10, txt="Confianza y Credibilidad", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=10)

    pdf.cell(200, 10, txt="Anuncios y Pop-Ups:", ln=True, align='L')

    # Navegar a la URL
    driver.get(url)

    # 27. Detección de anuncios y pop-ups
    driver.implicitly_wait(5)

    # Selección ampliada para detectar varios tipos de anuncios y pop-ups
    ads_selectors = [
        '[class*="ad"]', '[id*="ad"]', '[class*="pop"]', '[id*="pop"]'
    ]
    ads = []

    # Búsqueda de anuncios y pop-ups en la página principal
    for selector in ads_selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for element in elements:
            # Verificar si el elemento está visible de forma segura
            if is_element_displayed_safely(element):
                ads.append(element)

    # Resultado de la detección
    if ads:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= f"- Se detectaron {len(ads)} anuncios, pop-ups o elementos distractores en la página.")
    else:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= "- No se detectaron anuncios ni pop-ups.")

    # 28. Verificación de la presencia del logo en cada página
    logo_selectors = [
        'a.logo', 'img[alt*="logo"]', '[class*="logo"]', '[id*="logo"]',
        'img[src*="logo"]', '[class*="header-logo"]', '[class*="site-logo"]', '[class*="brand-logo"]'
    ]

    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Logo Constante:", ln=True, align='L')

    logo_elements = []
    for selector in logo_selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for element in elements:
            if element.is_displayed():
                logo_elements.append(element)

    # Resultado de la verificación
    if logo_elements:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= "- El logo de la marca aparece en la página.")
        #print("El logo de la marca aparece en la página.")
    else:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= "- El logo de la marca NO aparece en la página.")
        #print("El logo de la marca NO aparece en la página.")

    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Potenciales Errores:", ln=True, align='L')
    # 29. Detección de errores tipográficos y ortográficos
    spell = SpellChecker(language='es')  # Cambia a 'en' para inglés u otros idiomas según sea necesario

    # Obtener el contenido de la página
    text_content = driver.find_element(By.TAG_NAME, 'body').text

    # Dividir el texto en palabras y limpiarlo de posibles residuos de HTML o scripts
    words = text_content.split()

    # Encontrar palabras mal escritas
    misspelled = spell.unknown(words)

    # Lista de errores comunes, puede ampliarse o personalizarse
    common_mistakes = ["hte", "recieve", "adn", "teh", "seperated"]

    # Combinar errores comunes con palabras mal escritas
    found_errors = misspelled.union(set(word for word in common_mistakes if word in words))
    found_errors_list = list(found_errors)

    if found_errors_list:
        pdf.set_font("Arial", size=8)  # Añadimos un salto de línea
        pdf.set_x(15)
        # Corregir la cadena que genera el error
        pdf.multi_cell(200, 10, txt=f"- Se detectaron palabras desconocidas, alguna(s) podría(n) ser errores: {', '.join(map(str, found_errors_list[:5]))}")
    else:
        pdf.set_font("Arial", size=8)  # Añadimos un salto de línea
        pdf.set_x(15)
        pdf.multi_cell(200, 10, txt="- No se detectaron errores tipográficos u ortográficos que requieran atención inmediata.")
            #print("No se detectaron errores tipográficos u ortográficos.")

    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Listas y Viñetas:", ln=True, align='L')
    # 30. Detección de Listas y Viñetas
    # Detectar listas no ordenadas, ordenadas y listas de definiciones
    list_types = ['ul', 'ol', 'dl']
    lists = []
    for list_type in list_types:
        elements = driver.find_elements(By.CSS_SELECTOR, list_type)
        for element in elements:
            if element.is_displayed() and element.text.strip():  # Asegura que la lista esté visible y no esté vacía
                lists.append(element)

    # Resultado de la detección
    if lists:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt=f"- Se encontraron {len(lists)} listas (viñetas, numeradas o de definiciones) en la página." )
        #print(f"Se encontraron {len(lists)} listas (viñetas, numeradas o de definiciones) en la página.")
    else:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= "- No se encontraron listas en la página, posible uso excesivo de texto narrativo.")
        #print("No se encontraron listas en la página, posible uso excesivo de texto narrativo.")

    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Jerarquia de Contenido:", ln=True, align='L')
    # 31. Evaluación de la Jerarquía del Contenido mediante Encabezados (H1, H2, etc.)
    headers = driver.find_elements(By.CSS_SELECTOR, 'h1, h2, h3, h4, h5, h6')
    if headers:
        last_level = 0
        hierarchy_correct = True
        for header in headers:
            header_text = header.text.strip()
            if header.is_displayed() and header_text:
                current_level = int(header.tag_name[1])
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)
                pdf.multi_cell(200,10,txt= f"- Encabezado {header.tag_name.upper()} encontrado: {header_text}")
                #print(f"Encabezado {header.tag_name.upper()} encontrado: {header_text}")

                # Verificar jerarquía
                if current_level > last_level + 1:
                    pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                    pdf.set_x(15)
                    pdf.multi_cell(200,10,txt=f"- Advertencia: El encabezado {header.tag_name.upper()} parece estar fuera de orden jerárquico." )
                    #print(f"Advertencia: El encabezado {header.tag_name.upper()} parece estar fuera de orden jerárquico.")
                    hierarchy_correct = False

                last_level = current_level
            else:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)
                pdf.multi_cell(200,10,txt= f"- Encabezado {header.tag_name.upper()} encontrado, pero está vacío o no es visible.")
                #print(f"Encabezado {header.tag_name.upper()} encontrado, pero está vacío o no es visible.")

        if hierarchy_correct:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= "- La jerarquía de encabezados está presente y parece correcta.")
            #print("La jerarquía de encabezados está presente y parece correcta.")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= "- Se detectaron posibles problemas en la jerarquía de encabezados.")
            #print("Se detectaron posibles problemas en la jerarquía de encabezados.")
    else:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt="- No se encontraron encabezados, posible falta de estructura jerárquica en el contenido.")
        #print("No se encontraron encabezados, posible falta de estructura jerárquica en el contenido.")

    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Legibilidad del Sitio:", ln=True, align='L')
    # 32. Análisis de la Estructura de las Páginas para Mejorar la Legibilidad
    large_titles = driver.find_elements(By.CSS_SELECTOR, 'h1')
    subtitles = driver.find_elements(By.CSS_SELECTOR, 'h2, h3, h4')
    paragraphs = driver.find_elements(By.CSS_SELECTOR, 'p')

    # Verificar la presencia y cantidad de elementos
    if large_titles and subtitles and paragraphs:
        # Verificar la longitud de los párrafos
        long_paragraphs = [p for p in paragraphs if len(p.text.split()) > 100]  # Umbral de 100 palabras por párrafo

        if long_paragraphs:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- Se detectaron {len(long_paragraphs)} párrafos largos. Considera dividirlos para mejorar la legibilidad.")
            #print(f"Se detectaron {len(long_paragraphs)} párrafos largos. Considera dividirlos para mejorar la legibilidad.")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= "- Los párrafos son cortos y adecuados para la legibilidad.")
            #print("Los párrafos son cortos y adecuados para la legibilidad.")
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= "- La página contiene títulos grandes, subtítulos y párrafos cortos, lo que mejora la legibilidad.")
        #print("La página contiene títulos grandes, subtítulos y párrafos cortos, lo que mejora la legibilidad.")
    else:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= "- La estructura de la página podría no estar optimizada para la legibilidad.")
        #print("La estructura de la página podría no estar optimizada para la legibilidad.")
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Longitud de Titulos y Subtitulos:", ln=True, align='L')
    # 33. Análisis de la Longitud y Descriptividad de Títulos y Subtítulos
    title_threshold = 60  # Definir un umbral para la longitud de los títulos
    def is_descriptive(text):
        return len(text) > 5  # Define aquí tu criterio de descriptividad

    # Análisis de títulos
    for title in large_titles:
        title_length = len(title.text)
        if title_length > title_threshold:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- Título largo detectado: {title.text} (longitud: {title_length} caracteres).")
            #print(f"Título largo detectado: {title.text} (longitud: {title_length} caracteres).")
        elif not is_descriptive(title.text):
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt=f"- Título genérico o poco descriptivo detectado: {title.text}" )
            #print(f"Título genérico o poco descriptivo detectado: {title.text}")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- Título descriptivo adecuado: {title.text}")
            #print(f"Título descriptivo adecuado: {title.text}")

    # Análisis de subtítulos
    for subtitle in subtitles:
        subtitle_length = len(subtitle.text)
        if subtitle_length > title_threshold:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- Subtítulo largo detectado: {subtitle.text} (longitud: {subtitle_length} caracteres).")
            #print(f"Subtítulo largo detectado: {subtitle.text} (longitud: {subtitle_length} caracteres).")
        elif not is_descriptive(subtitle.text) or subtitle.text != ' ' or subtitle.text != '':
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- Subtítulo genérico o poco descriptivo detectado: {subtitle.text}")
            #print(f"Subtítulo genérico o poco descriptivo detectado: {subtitle.text}")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"Subtítulo descriptivo adecuado: {subtitle.text}")
            #print(f"Subtítulo descriptivo adecuado: {subtitle.text}")

    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Numeración de Listas:", ln=True, align='L')
    # 34. Detección de Listas Numeradas para Verificar que Comienzan en "1"
    numbered_lists = driver.find_elements(By.CSS_SELECTOR, 'ol')
    for ol in numbered_lists:
        if ol.get_attribute('start') and ol.get_attribute('start') != '1':
            pdf.multi_cell(200,10,txt= f"Lista numerada que no comienza en 1 detectada: {ol.get_attribute('start')}")
            #print(f"Lista numerada que no comienza en 1 detectada: {ol.get_attribute('start')}")
        else:
            pdf.multi_cell(200,10,txt= "Todas las listas numeradas comienzan en 1.")
            #print("Todas las listas numeradas comienzan en 1.")

    # Cerrar el driver
    #driver.quit()

def hdu_seis(url):

    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(200,10,txt= "Calidad del Contenido",align='C')

    pdf.ln(10)
    # Navegar a la URL
    driver.get(url)

    # 35. Detección de Listas y Viñetas
    lists = driver.find_elements(By.CSS_SELECTOR, 'ul, ol')
    if lists:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= f"- Se encontraron {len(lists)} listas (viñetas o numeradas) en la página.")
        #print(f"Se encontraron {len(lists)} listas (viñetas o numeradas) en la página.")
    else:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= "- No se encontraron listas en la página, posible uso excesivo de texto narrativo.")
        #print("No se encontraron listas en la página, posible uso excesivo de texto narrativo.")

    # 36. Evaluación de la Jerarquía del Contenido mediante Encabezados (H1, H2, etc.)
    headers = driver.find_elements(By.CSS_SELECTOR, 'h1, h2, h3, h4, h5, h6')
    if headers:
        last_level = 0
        hierarchy_correct = True
        for header in headers:
            header_text = header.text.strip()
            if header.is_displayed() and header_text:
                current_level = int(header.tag_name[1])
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10,txt= f"- Encabezado {header.tag_name.upper()} encontrado: {header_text}")
                #print(f"Encabezado {header.tag_name.upper()} encontrado: {header_text}")

                # Verificar jerarquía
                if current_level > last_level + 1:
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(200,10,txt= f"- Advertencia: El encabezado {header.tag_name.upper()} parece estar fuera de orden jerárquico.")
                    #print(f"Advertencia: El encabezado {header.tag_name.upper()} parece estar fuera de orden jerárquico.")
                    hierarchy_correct = False

                last_level = current_level
            else:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200,10,txt= f"- Encabezado {header.tag_name.upper()} encontrado, pero está vacío o no es visible.")
                #print(f"Encabezado {header.tag_name.upper()} encontrado, pero está vacío o no es visible.")

        if hierarchy_correct:
            print("La jerarquía de encabezados está presente y parece correcta.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= "- Se detectaron posibles problemas en la jerarquía de encabezados.")
            #print("Se detectaron posibles problemas en la jerarquía de encabezados.")
    else:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= "- No se encontraron encabezados, posible falta de estructura jerárquica en el contenido.")
        #print("No se encontraron encabezados, posible falta de estructura jerárquica en el contenido.")

    # 37. Análisis de la Estructura de las Páginas para Mejorar la Legibilidad
    large_titles = driver.find_elements(By.CSS_SELECTOR, 'h1')
    subtitles = driver.find_elements(By.CSS_SELECTOR, 'h2, h3')
    paragraphs = driver.find_elements(By.CSS_SELECTOR, 'p')

    if large_titles and subtitles and paragraphs:
        long_paragraphs = [p for p in paragraphs if len(p.text.split()) > 100]  # Umbral de 100 palabras por párrafo
        if long_paragraphs:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- Se detectaron {len(long_paragraphs)} párrafos largos. Considera dividirlos para mejorar la legibilidad.")
            #print(f"Se detectaron {len(long_paragraphs)} párrafos largos. Considera dividirlos para mejorar la legibilidad.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- Los párrafos son cortos y adecuados para la legibilidad.")
            #print("Los párrafos son cortos y adecuados para la legibilidad.")

        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= f"- La página contiene títulos grandes, subtítulos y párrafos cortos, lo que mejora la legibilidad.")
        #print("La página contiene títulos grandes, subtítulos y párrafos cortos, lo que mejora la legibilidad.")
    else:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200,10,txt= f"- La estructura de la página podría no estar optimizada para la legibilidad.")
        #print("La estructura de la página podría no estar optimizada para la legibilidad.")

    # 38. Análisis de la Longitud y Descriptividad de Títulos y Subtítulos
    title_threshold = 60  # Definir un umbral para la longitud de los títulos
    def is_descriptive(text):
        return len(text) > 5  # Define aquí tu criterio de descriptividad

    # Análisis de títulos
    for title in large_titles:
        title_length = len(title.text)
        if title_length > title_threshold:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- Título largo detectado: {title.text} (longitud: {title_length} caracteres).")
            #print(f"Título largo detectado: {title.text} (longitud: {title_length} caracteres).")
        elif not is_descriptive(title.text):
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- Título genérico o poco descriptivo detectado: {title.text}")
            #print(f"Título genérico o poco descriptivo detectado: {title.text}")
        else:
            print(f"Título descriptivo adecuado: {title.text}")

    # Análisis de subtítulos
    for subtitle in subtitles:
        subtitle_length = len(subtitle.text)
        if subtitle_length > title_threshold:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- Subtítulo largo detectado: {subtitle.text} (longitud: {subtitle_length} caracteres).")
            #print(f"Subtítulo largo detectado: {subtitle.text} (longitud: {subtitle_length} caracteres).")
        elif not is_descriptive(subtitle.text):
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(200,10,txt= f"- Subtítulo genérico o poco descriptivo detectado: {subtitle.text}")
            #print(f"Subtítulo genérico o poco descriptivo detectado: {subtitle.text}")
        else:
            print(f"Subtítulo descriptivo adecuado: {subtitle.text}")

    # Cerrar el driver
    #driver.quit()

def hdu_siete(url):


    # Navegar a la URL
    driver.get(url)
    
    pdf.ln(10)

    pdf.set_font("Arial", size=11)

    pdf.cell(200, 10, txt="Diagramación y Diseño", align='C')
    
    pdf.ln(10)

    # Funciones auxiliares
    def rgb_or_rgba_to_tuple(color_str):
        nums = re.findall(r'\d+', color_str)
        return tuple(map(int, nums[:3]))

    def luminance(rgb):
        r, g, b = [x / 255.0 for x in rgb]
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def calculate_contrast(rgb1, rgb2):
        lum1 = luminance(rgb1) + 0.05
        lum2 = luminance(rgb2) + 0.05
        return max(lum1, lum2) / min(lum1, lum2)

    # Almacenar resultados agrupados
    grouped_results = {
        "fuentes": [],
        "contraste": [],
        "tamaño_fuente": [],
        "desalineado": [],
        "elementos_subrayados": [],
        "elementos_negrita": [],
        "otros": []
    }

    # 1. Consistencia en el Uso de Fuentes
    fonts = driver.find_elements(By.CSS_SELECTOR, '*[style*="font-family"]')
    font_families = {font.value_of_css_property('font-family') for font in fonts}
    if len(font_families) > 1:
        grouped_results["fuentes"].append(f"Uso inconsistente de varias fuentes en el sitio: {', '.join(font_families)}")

    # 2. Verificación de Desplazamiento Horizontal
    body = driver.find_element(By.TAG_NAME, 'body')
    body_width = body.size['width']
    viewport_width = driver.execute_script("return window.innerWidth")

    if body_width > viewport_width:
        grouped_results["otros"].append("Desplazamiento horizontal detectado.")

    # 3. Detección de Enlaces Subrayados o con Indicación Visual Clara
    links = driver.find_elements(By.TAG_NAME, 'a')
    for link in links:
        link_text = link.text.strip()
        if link.is_displayed() and link_text:
            text_decoration = link.value_of_css_property('text-decoration')
            font_weight = link.value_of_css_property('font-weight')
            border_bottom = link.value_of_css_property('border-bottom')

            if not ('underline' in text_decoration or int(font_weight) >= 700 or 'solid' in border_bottom):
                grouped_results["elementos_subrayados"].append(f"Enlace sin indicación visual clara: '{link_text}'")

    # 4. Revisión de la Legibilidad de las Fuentes (Tamaño y Contraste)
    text_elements = driver.find_elements(By.CSS_SELECTOR, 'body *')
    for elem in text_elements:
        font_size_str = elem.value_of_css_property('font-size')
        font_size = float(re.search(r'\d+(\.\d+)?', font_size_str).group())
        color_str = elem.value_of_css_property('color')
        background_color_str = elem.value_of_css_property('background-color')
        color = rgb_or_rgba_to_tuple(color_str)
        background_color = rgb_or_rgba_to_tuple(background_color_str)

        if font_size < 16:
            grouped_results["tamaño_fuente"].append(f"{elem.tag_name} tiene un tamaño de fuente insuficiente ({font_size}px)")

        if isinstance(color, tuple) and isinstance(background_color, tuple):
            contrast = calculate_contrast(color, background_color)
            if contrast < 4.5:
                grouped_results["contraste"].append(f"{elem.tag_name} tiene un contraste insuficiente ({contrast:.2f})")

    # 9. Análisis de la Alineación de Ítems en el Diseño
    elements = driver.find_elements(By.CSS_SELECTOR, 'body *')
    for elem in elements:
        pos_x = elem.location['x']
        pos_y = elem.location['y']
        if pos_x % 10 != 0 or pos_y % 10 != 0:
            grouped_results["desalineado"].append(f"{elem.tag_name} en posición ({pos_x}, {pos_y}) está desalineado.")

    # Imprimir resultados agrupados
    if grouped_results["fuentes"]:
        #print("**Fuentes:**")
        for item in grouped_results["fuentes"]:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= f"- Fuentes: - {item}")
            #print(f"- {item}")

    if grouped_results["contraste"]:
        #print("\n**Advertencia: Elementos con contraste insuficiente:**")
        for item in grouped_results["contraste"]:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= f"- Advertencia: Elementos con contraste insuficiente: - {item}")
            #print(f"- {item}")

    if grouped_results["tamaño_fuente"]:
        #print("\n**Advertencia: Elementos con tamaño de fuente insuficiente:**")
        for item in grouped_results["tamaño_fuente"]:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= f"- Advertencia: Elementos con tamaño de fuente insuficiente: - {item}")
            #print(f"- {item}")

    if grouped_results["desalineado"]:
        #print("\n**Advertencia: Elementos desalineados:**")
        for item in grouped_results["desalineado"]:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= f"- Advertencia: Elementos desalineados: - {item}")
            #print(f"- {item}")

    if grouped_results["elementos_subrayados"]:
        #print("\n**Advertencia: Enlaces sin indicación visual clara:**")
        for item in grouped_results["elementos_subrayados"]:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= f"- Advertencia: Enlaces sin indicación visual clara: - {item}")
            #print(f"- {item}")

    if grouped_results["elementos_negrita"]:
        #print("\n**Advertencia: Uso de negrita en elementos:**")
        for item in grouped_results["elementos_negrita"]:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= f"- Advertencia: Uso de negrita en elementos: - {item}")
            #print(f"- {item}")

    if grouped_results["otros"]:
        #print("\n**Advertencia: Otros problemas detectados:**")
        for item in grouped_results["otros"]:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= f"- Advertencia: Otros problemas detectados: - {item}")
            #print(f"- {item}")
    # Cerrar el driver
    #driver.quit()

def hdu_ocho(url):
    # Navegar a la URL
    driver.get(url)
    
    pdf.ln(10)
    pdf.set_font("Arial", size=11)

    pdf.cell(200, 10, txt="Sección de Búsquedas", align='C')
    pdf.ln(10)
    
    # 52. Confirmación de Términos de Búsqueda y Opciones de Edición
    try:
        search_terms = driver.find_element(By.CSS_SELECTOR, '.search-terms')
        if search_terms.is_displayed():
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= f"- Términos de búsqueda mostrados: {search_terms.text}")
            #print(f"Términos de búsqueda mostrados: {search_terms.text}")
            edit_button = driver.find_element(By.CSS_SELECTOR, '.edit-search')
            if edit_button.is_displayed():
                try:
                    edit_button.click()
                    pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                    pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                    pdf.multi_cell(200,10,txt="- Opción para editar y reenviar los criterios de búsqueda disponible y funcional." )
                    #print("Opción para editar y reenviar los criterios de búsqueda disponible y funcional.")
                except Exception as e:
                    pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                    pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                    pdf.multi_cell(200,10,txt=f"- Advertencia: El botón de edición no respondió al clic. Error: {e}" )
                    #print(f"Advertencia: El botón de edición no respondió al clic. Error: {e}")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= "- Advertencia: Los términos de búsqueda no son visibles.")
            #print("Advertencia: Los términos de búsqueda no son visibles.")
    except NoSuchElementException:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(200,10,txt= "- Los términos de búsqueda no se muestran o no hay opción para editar y reenviar.")
        #print("Los términos de búsqueda no se muestran o no hay opción para editar y reenviar.")

    # 53. Evaluación de la Clasificación de Resultados por Relevancia
    try:
        results = driver.find_elements(By.CSS_SELECTOR, '.search-result')
        if results:
            for i, result in enumerate(results):
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(200,10,txt= f"- Resultado {i+1}: {result.text[:50]}...")
                #print(f"Resultado {i+1}: {result.text[:50]}...")  # Mostrar parte del resultado para identificar
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= f"- Resultados clasificados por relevancia: {len(results)} resultados encontrados.")
            #print(f"Resultados clasificados por relevancia: {len(results)} resultados encontrados.")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= "- No se encontraron resultados clasificados por relevancia.")
            #print("No se encontraron resultados clasificados por relevancia.")
    except NoSuchElementException:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(200,10,txt= "- No se encontraron resultados clasificados por relevancia.")
        #print("No se encontraron resultados clasificados por relevancia.")

    # 54. Comprobación del Número Total de Resultados y Configuración de Resultados por Página
    try:
        total_results = driver.find_element(By.CSS_SELECTOR, '.total-results')
        if total_results.is_displayed():
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= f"- Número total de resultados mostrado: {total_results.text}")
            #print(f"Número total de resultados mostrado: {total_results.text}")
            per_page_options = driver.find_element(By.CSS_SELECTOR, '.results-per-page')
            if per_page_options.is_displayed():
                try:
                    per_page_options.click()
                    pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                    pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                    pdf.multi_cell(200,10,txt= "- Opción para configurar el número de resultados por página disponible y funcional.")
                    #print("Opción para configurar el número de resultados por página disponible y funcional.")
                except Exception as e:
                    pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                    pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                    pdf.multi_cell(200,10,txt= f"- Advertencia: La opción para configurar los resultados por página no respondió al clic. Error: {e}")
                    #print(f"Advertencia: La opción para configurar los resultados por página no respondió al clic. Error: {e}")
            else:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(200,10,txt= "- Advertencia: La opción para configurar los resultados por página no es visible.")
                #print("Advertencia: La opción para configurar los resultados por página no es visible.")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= "- Advertencia: El número total de resultados no es visible.")
            #print("Advertencia: El número total de resultados no es visible.")
    except NoSuchElementException:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(200,10,txt= ("- No se muestra el número total de resultados o no hay opción para configurar los resultados por página."))
        #print("No se muestra el número total de resultados o no hay opción para configurar los resultados por página.")

    # 55. Verificación del Manejo Correcto de Búsquedas sin Entrada
    try:
        search_box = driver.find_element(By.CSS_SELECTOR, '.search-box')
        search_button = driver.find_element(By.CSS_SELECTOR, '.search-button')

        # Limpiar la caja de búsqueda y realizar la búsqueda
        search_box.clear()
        search_button.click()

        # Verificar el comportamiento al realizar una búsqueda sin entrada
        empty_search_results = driver.find_element(By.CSS_SELECTOR, '.no-results, .empty-search')
        if empty_search_results.is_displayed():
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= "- El motor de búsqueda maneja correctamente las búsquedas sin entrada, mostrando un mensaje adecuado.")
            #print("El motor de búsqueda maneja correctamente las búsquedas sin entrada, mostrando un mensaje adecuado.")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= "- Advertencia: El motor de búsqueda no maneja adecuadamente las búsquedas sin entrada.")
            #print("Advertencia: El motor de búsqueda no maneja adecuadamente las búsquedas sin entrada.")
    except NoSuchElementException:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(200,10,txt= "- El motor de búsqueda no maneja correctamente las búsquedas sin entrada o elementos no encontrados.")
        #print("El motor de búsqueda no maneja correctamente las búsquedas sin entrada o elementos no encontrados.")

    # 56. Comprobación del Etiquetado Claro de la Caja de Búsqueda y Controles
    try:
        search_box_label = driver.find_element(By.CSS_SELECTOR, 'label[for="search-box"], [aria-label="search"]')

        if search_box_label.is_displayed():
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= f"- Caja de búsqueda claramente etiquetada: {search_box_label.text or search_box_label.get_attribute('aria-label')}")
            #print(f"Caja de búsqueda claramente etiquetada: {search_box_label.text or search_box_label.get_attribute('aria-label')}")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= "- Advertencia: La etiqueta de la caja de búsqueda no es visible.")
            #print("Advertencia: La etiqueta de la caja de búsqueda no es visible.")
    except NoSuchElementException:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(200,10,txt= "- La caja de búsqueda o sus controles no están claramente etiquetados.")
        #print("La caja de búsqueda o sus controles no están claramente etiquetados.")

    # 57. Verificación de Opciones para Encontrar Contenido Relacionado
    try:
        related_content = driver.find_element(By.CSS_SELECTOR, '.related-searches')

        if related_content.is_displayed():
            related_links = related_content.find_elements(By.TAG_NAME, 'a')
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= f"- Opciones para encontrar contenido relacionado disponibles: {len(related_links)} enlaces encontrados.")
            #print(f"Opciones para encontrar contenido relacionado disponibles: {len(related_links)} enlaces encontrados.")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= "- Advertencia: Las opciones para encontrar contenido relacionado no son visibles.")
            #print("Advertencia: Las opciones para encontrar contenido relacionado no son visibles.")
    except NoSuchElementException:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(200,10,"No se ofrecen opciones para encontrar contenido relacionado (Si es sitio de comercio omitir sugerencia).")

    # 58. Evaluación de Opciones de Navegación y Búsqueda
    try:
        navigation_menu = driver.find_element(By.CSS_SELECTOR, '.navigation-menu')
        search_box = driver.find_element(By.CSS_SELECTOR, '.search-box')

        if navigation_menu.is_displayed() and search_box.is_displayed():
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= "- El sitio ofrece opciones tanto para la navegación como para la búsqueda.")
            #print("El sitio ofrece opciones tanto para la navegación como para la búsqueda.")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= "- Advertencia: Las opciones de navegación o búsqueda no son visibles.")
            #print("Advertencia: Las opciones de navegación o búsqueda no son visibles.")
    except NoSuchElementException:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(200,10,"- El sitio no ofrece opciones adecuadas para la navegación o la búsqueda o el elemento no fue encontrado.")

    # 59. Verificación de la Ausencia de Resultados Duplicados o Similares
    try:
        result_titles = [result.text for result in driver.find_elements(By.CSS_SELECTOR, '.result-title')]
        duplicates = [title for title in result_titles if result_titles.count(title) > 1]

        if duplicates:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= f"- Advertencia: Resultados duplicados encontrados: {', '.join(set(duplicates))}")
            #print(f"Advertencia: Resultados duplicados encontrados: {', '.join(set(duplicates))}")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(200,10,txt= "- No se encontraron resultados duplicados o muy similares.")
            #print("No se encontraron resultados duplicados o muy similares.")
    except NoSuchElementException:
        print("No se pudo verificar la existencia de resultados duplicados o similares.")

    # Cerrar el driver
    #driver.quit()


def hdu_nueve(url): 
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    
    pdf.cell(200, 10, txt="Sección de Reconocimiento de Errores y Retroalimentación", align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=8) # Añadimos un salto de línea
    pdf.set_x(15) 

    # Medición del tiempo de carga de la página
    start_time = time.time()
    driver.get(url)
    load_time = time.time() - start_time
    if load_time <= 5:
        pdf.multi_cell(200,10,txt= f"- La página se cargó en {load_time:.2f} segundos, dentro del límite aceptable.")
    else:
        pdf.multi_cell(200,10,txt= f"- Advertencia: La página tardó {load_time:.2f} segundos en cargar, excediendo el límite de 5 segundos.")

    # Lista para almacenar mensajes ya mostrados
    shown_messages = []

    def show_message(message):
        """Función para verificar si un mensaje ya fue mostrado."""
        if message not in shown_messages:
            pdf.multi_cell(200,10,txt=message)
            shown_messages.append(message)

    # 61. Comprobación del Tamaño de la Caja de Búsqueda con límite de tiempo
    try:
        search_box = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.search-box')))
        search_box_width = search_box.size['width']
        if search_box_width >= 300:
            pdf.multi_cell(200,10,txt=f"- La caja de búsqueda es lo suficientemente grande: {search_box_width}px de ancho.")
        else:
            pdf.multi_cell(200,10,txt=f"- Advertencia: La caja de búsqueda es pequeña: {search_box_width}px de ancho.")
    except (NoSuchElementException, TimeoutException):
        pdf.multi_cell(200,10,"- No se pudo encontrar la caja de búsqueda para verificar su tamaño.")

    # 62. Verificación del Espaciado y Tamaño de los Elementos Clickeables con límite de elementos
    clickable_elements = driver.find_elements(By.CSS_SELECTOR, 'button, a, input[type="submit"], input[type="button"]')[:20]  # Limitar a 20 elementos
    for elem in clickable_elements:
        try:
            elem_id = elem.get_attribute('id') or elem.get_attribute('name') or elem.text
            size = elem.size
            location = elem.location
            if size['width'] >= 44 and size['height'] >= 44:
                pdf.multi_cell(200,10,txt=f"- Elemento clickeable de tamaño adecuado: {elem.tag_name} con tamaño {size['width']}x{size['height']}.")
            else:
                pdf.multi_cell(200,10,txt=f"- Advertencia: Elemento clickeable pequeño: {elem.tag_name} con tamaño {size['width']}x{size['height']}.")

            # Verificación de espaciado alrededor con límite
            elements_around = driver.find_elements(By.XPATH, f"//body//*[not(self::script)][not(self::style)]")[:10]
            for nearby_elem in elements_around:
                nearby_location = nearby_elem.location
                if abs(location['x'] - nearby_location['x']) < 20 and abs(location['y'] - nearby_location['y']) < 20:
                    pdf.multi_cell(200,10,txt=f"- Advertencia: Elemento clickeable {elem.tag_name} podría tener un espaciado insuficiente.")
        except StaleElementReferenceException:
            pdf.multi_cell(200,10,txt=f"- Advertencia: El elemento '{elem.tag_name}' ya no es válido en el DOM.")

    # 63. Verificación de la Presencia y Adecuación de la Ayuda Contextual con límite
    try:
        help_elements = driver.find_elements(By.CSS_SELECTOR, '.help, .tooltip, .hint, [title], [aria-label]')[:10]  # Limitar a 10 elementos
        if help_elements:
            pdf.multi_cell(200,10,txt=f"- Se encontraron {len(help_elements)} elementos de ayuda contextual visibles.")
            for elem in help_elements:
                try:
                    elem_id = elem.get_attribute('title') or elem.get_attribute('aria-label') or elem.text
                    pdf.multi_cell(200,10,txt=f"- Elemento de ayuda detectado: {elem_id}")
                except StaleElementReferenceException:
                    pdf.multi_cell(200,10,txt=f"- Advertencia: El elemento de ayuda '{elem_id}' ya no es válido en el DOM.")
    except NoSuchElementException:
        pdf.multi_cell(200,10,"Error al buscar elementos de ayuda contextual.")

    # 64. Revisión de Enlaces y Textos Descriptivos para Evitar Texto Genérico
    generic_phrases = ["Click aquí", "Más información", "Haz clic aquí", "Leer más", "Ver detalles"]
    links = driver.find_elements(By.TAG_NAME, 'a')[:20]  # Limitar a 20 enlaces
    for link in links:
        try:
            link_text = link.text.strip()
            if not link_text:
                pdf.multi_cell(200,10,txt="- Advertencia: Enlace sin texto visible o solo con espacios detectado.")
            else:
                if any(phrase.lower() in link_text.lower() for phrase in generic_phrases):
                    pdf.multi_cell(200,10,txt=f"- Advertencia: Enlace con texto genérico encontrado: {link_text}")
                else:
                    pdf.multi_cell(200,10,txt=f"- Enlace con texto descriptivo adecuado: {link_text}")
        except StaleElementReferenceException:
            pdf.multi_cell(200,10,txt=f"- Advertencia: El enlace '{link.text}' ya no es válido en el DOM.")
    
    # Cerrar el driver
    #driver.quit()

for categoria in categorias:
    if categoria == "Página de Inicio":
        hdu_uno(url)
    elif categoria == "Orientación de Tareas":
        hdu_dos(url)
    elif categoria ==  "Navegabilidad":
        hdu_tres(url)
    elif categoria ==   "Formularios":
        hdu_cuatro(url)
    elif categoria ==  "Confianza y Credibilidad":
        hdu_cinco(url)
    elif categoria ==   "Calidad del Contenido":
        hdu_seis(url)
    elif categoria ==   "Diagramación y Diseño":
        hdu_siete(url)
    elif categoria ==  "Sección de Búsquedas":
        hdu_ocho(url)
    elif categoria == "Sección de Reconocimiento de Errores y Retroalimentación":
        hdu_nueve(url)

driver.quit()


# Inicializa Firebase
cred = credentials.Certificate('src\components\config\iatu-pmv-firebase-adminsdk-my9kl-4321b8a185.json')
initialize_app(cred, {'storageBucket': 'iatu-pmv.appspot.com'})

# Usar BytesIO para guardar el PDF en memoria
pdf_stream = BytesIO()
# Guardar el contenido del PDF en el flujo de bytes usando el parámetro dest='S'
pdf_output = pdf.output(dest='S').encode('latin1')  # En FPDF, el formato de salida es string, lo convertimos a bytes
pdf_stream.write(pdf_output)
pdf_stream.seek(0)  # Mover el cursor al inicio del archivo en memoria


# Subir el PDF a Firebase Storage sin guardarlo localmente
bucket = storage.bucket()
blob = bucket.blob(f'pdfs/{id}/informe.pdf')
# Subir directamente el contenido del PDF en bytes
blob.upload_from_string(pdf_stream.getvalue(), content_type='application/pdf')

# Hacer que el archivo sea público y obtener su URL
blob.make_public()
pdf_url = blob.public_url
print(f"PDF disponible en: {pdf_url}")

# Guarda la URL del PDF en Firestore bajo el documento correspondiente en tasks
db = firestore.client()
task_ref = db.collection('proyectos').document(idP).collection('tasks').document(id)

# Actualiza el campo 'pdfUrl' con la URL pública del PDF
task_ref.update({
    'pdfUrl': pdf_url
})

print(f"URL del PDF guardada en Firestore: {pdf_url}")


# Generar y guardar el PDF
#pdf.output(f"public/informe.pdf")
shutil.rmtree('capturas')
shutil.rmtree('output_evaluated_images')
#shutil.rmtree('capturas_navegacion')
#shutil.rmtree('capturasSelenium')
#shutil.rmtree('fotosSelenium')
#shutil.rmtree('output_cingoz')
#shutil.rmtree('output_icon')
#shutil.rmtree('output_pb')
#shutil.rmtree('output_images')