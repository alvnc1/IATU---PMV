import os
import shutil
import time
import re
import threading
import sys
from firebase_admin import credentials, initialize_app, storage, firestore
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    NoSuchElementException, 
    StaleElementReferenceException, 
    ElementClickInterceptedException
)
import numpy as np
import os
import cv2
import time
import spacy
import requests
from textstat import textstat
from inference_sdk import InferenceHTTPClient
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from fpdf import FPDF
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from io import BytesIO
from colorama import Fore, Style
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


backslash = '\n' 
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

def obtener_nombre_elemento(element, idx):
    """Devuelve un nombre representativo del elemento para usar en logs y archivos."""
    if element.get_attribute('id'):
        return f"{element.get_attribute('id')}_{idx}"
    elif element.get_attribute('aria-label'):
        return f"{element.get_attribute('aria-label')}_{idx}"
    elif element.text.strip():
        return f"{element.text.strip().replace(' ', '_')[:20]}_{idx}"  # Limita el texto a los primeros 20 caracteres
    else:
        return f"elemento_{idx}"

pdf = FPDF()
pdf.add_page()
# Directorio de imágenes de entrada
input_dir = "capturas"
output_base_dir = "output_evaluated_images"
os.makedirs(output_base_dir, exist_ok=True)

# Inicializar el diccionario para las clases
dic_clases = {}

# Obtener dimensiones de la página
page_width = pdf.w
page_height = pdf.h

# Insertar el logo centrado en la parte superior
logo_width = 40  # Ancho del logo, ajusta según el tamaño de tu imagen
x_logo = (page_width - logo_width) / 2  # Calcular el x para centrar la imagen
pdf.image("logo.png", x=x_logo, y=10, w=logo_width)

# Establecer la fuente para el título
pdf.set_font("Arial", 'B', 24)

# Calcular la posición para centrar el título
title = "Revisión de Criterios Accesibilidad"
title_width = pdf.get_string_width(title)
pdf.set_xy((page_width - title_width) / 2, 70)  # Ajustar `y=70` para colocar debajo del logo
pdf.cell(title_width, 10, txt=title, ln=True)

# Añadir subtítulo debajo del título con espaciado adecuado
subtitle = "Análisis Integral de Componentes Web"
pdf.set_font("Arial", '', 16)  # Fuente más pequeña para el subtítulo
subtitle_width = pdf.get_string_width(subtitle)
pdf.set_xy((page_width - subtitle_width) / 2, 85)  # Ajustar `y=85` para centrar el subtítulo debajo del título
pdf.cell(subtitle_width, 10, txt=subtitle, ln=True)

# Añadir la fecha de generación un poco más abajo
pdf.set_font("Arial", '', 12)
from datetime import datetime
fecha_actual = datetime.now().strftime('%d/%m/%Y')
fecha_text = f"Fecha de generación: {fecha_actual}"
fecha_width = pdf.get_string_width(fecha_text)
pdf.set_xy((page_width - fecha_width) / 2, 100)  # Ajustar `y=100` para la fecha
pdf.cell(fecha_width, 10, txt=fecha_text, ln=True)

# Iniciar una página antes del loop
#pdf.add_page()

# Agregar el título en la primera página
#pdf.set_font('Arial', 'B', 14)  # Configurar la fuente: Arial, Negrita, tamaño 16
#pdf.cell(200, 10, "Capturas de Frames y Detección de Componentes", ln=True, align='C')  # Centrar el título
#pdf.ln(20)  # Añadir espacio después del título

# Variables de posición para el layout de las imágenes
x_pos = 10  # Posición horizontal inicial
y_pos = 30  # Posición vertical inicial, debajo del título
image_width = 180  # Ancho ajustado para cada imagen
image_height = 100  # Altura ajustada para cada imagen
space_between_images = 10  # Espacio entre imágenes
page_height = 297  # Altura de la página A4 en mm
margin_bottom = 10  # Margen inferior de la página

# Procesar cada imagen
# for idx, image_filename in enumerate(os.listdir(input_dir)):
#     if image_filename.endswith(('.jpg', '.jpeg', '.png')):
#         image_path = os.path.join(input_dir, image_filename)

#         # Realizar la inferencia con los modelos
#         result = CLIENT.infer(image_path, model_id="cingoz8/1")
#         result_model_2 = CLIENT.infer(image_path, model_id="app-icon/48")

#         # Combinar los resultados de ambos modelos
#         combined_results = result['predictions'] + result_model_2['predictions']

#         # Crear subdirectorio para la imagen
#         image_output_dir = os.path.join(output_base_dir, os.path.splitext(image_filename)[0])
#         os.makedirs(image_output_dir, exist_ok=True)

#         # Cargar la imagen original
#         image = cv2.imread(image_path)
#         original_height, original_width, _ = image.shape

#         # Procesar los resultados y dibujar bounding boxes en la imagen original
#         for i, prediction in enumerate(combined_results):
#             # Coordenadas de la bounding box
#             x0 = int(prediction['x'] - prediction['width'] / 2)
#             y0 = int(prediction['y'] - prediction['height'] / 2)
#             x1 = int(prediction['x'] + prediction['width'] / 2)
#             y1 = int(prediction['y'] + prediction['height'] / 2)

#             # Dibujar la bounding box en la imagen original
#             cv2.rectangle(image, (x0, y0), (x1, y1), color=(0, 255, 0), thickness=2)

#             # Poner el label (clase y confianza) encima de la bounding box
#             label = f"{prediction['class']} ({prediction['confidence']:.2f})"
#             cv2.putText(image, label, (x0, y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#         # Guardar la imagen original con todas las bounding boxes dibujadas
#         output_image_path = os.path.join(image_output_dir, os.path.basename(image_path))
#         cv2.imwrite(output_image_path, image)

#         # Verificar si hay suficiente espacio para la imagen actual
#         if y_pos + image_height + margin_bottom > page_height:
#             pdf.add_page()  # Añadir nueva página
#             y_pos = 10  # Resetear la posición vertical para la nueva página

#         # Colocar la imagen en la posición calculada
#         pdf.image(output_image_path, x=x_pos, y=y_pos, w=image_width, h=image_height)

#         # Ajustar la posición vertical para la siguiente imagen
#         y_pos += image_height + space_between_images

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
pdf.add_page()
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

def verificar_accesibilidad_lectores_pantalla(url):
    # Agrega un título
    # Establece la fuente (tipografía y tamaño)
    pdf.set_font("Arial", " I", size=10)
    pdf.cell(200, 10, txt="Lectores de pantalla:", ln=True, align='L')
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Navegar a la URL
    driver.get(url)

    # --- Criterio: Verificar accesibilidad para lectores de pantalla ---
    try:
        elementos_interactivos = driver.find_elements(By.CSS_SELECTOR, 'a, button, input, select, textarea')
        total_elementos = len(elementos_interactivos)
        elementos_accesibles = 0
        
        for elemento in elementos_interactivos:
            # Verificar presencia de etiquetas o atributos descriptivos
            if (elemento.get_attribute('aria-label') or 
                elemento.get_attribute('aria-labelledby') or 
                elemento.get_attribute('title') or 
                elemento.get_attribute('role')):
                elementos_accesibles += 1

        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- {elementos_accesibles} de {total_elementos} elementos interactivos son accesibles mediante lectores de pantalla.")
        if elementos_accesibles < total_elementos:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Advertencia: {total_elementos - elementos_accesibles} elementos interactivos carecen de etiquetas o descripciones claras para lectores de pantalla.")
    except Exception as e:
        print(f"Error al verificar accesibilidad para lectores de pantalla: {e}")
    
    # Cerrar el driver
    driver.quit()

# Ejemplo de uso
#verificar_accesibilidad_lectores_pantalla('https://www.mercadolibre.cl')

chrome_options = Options()
chrome_options.add_argument("--headless=old")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def verificar_accesibilidad_teclado(url):
    pdf.set_font("Arial", size=14)
    pdf.ln(10)
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(200, 10, txt="Criterio: Validación de Accesibilidad", ln=True, align='C')
    # Configurar el driver de Selenium en modo headless
    # Agrega un título
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Accesibilidad con teclado:", ln=True, align='L')
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Navegar a la URL
    driver.get(url)

    try:
        # Encontrar todos los elementos seleccionables
        elementos_seleccionables = driver.find_elements(By.CSS_SELECTOR, 'a, button, input, select, textarea, [tabindex]')

        total_elementos = len(elementos_seleccionables)
        elementos_con_enfoque_claro = 0
        elementos_sin_enfoque_claro = 0

        for idx in range(total_elementos):
            reintentos = 3
            while reintentos > 0:
                try:
                    elemento = driver.find_elements(By.CSS_SELECTOR, 'a, button, input, select, textarea, [tabindex]')[idx]
                    if elemento.is_displayed() and (elemento.get_attribute('tabindex') is not None or elemento.tag_name in ['a', 'button', 'input', 'select', 'textarea']):
                        # Intentar hacer foco en el elemento y verificar si hay un cambio visual
                        driver.execute_script("arguments[0].focus();", elemento)
                        time.sleep(0.2)  # Espera breve para observar el cambio
                        
                        # Verificar si el elemento muestra un cambio visual claro en el estilo
                        estilo_enfoque = elemento.get_attribute('style')
                        if 'outline' in estilo_enfoque or 'border' in estilo_enfoque:
                            elementos_con_enfoque_claro += 1
                        else:
                            elementos_sin_enfoque_claro += 1
                    break  # Salir del ciclo de reintento si fue exitoso
                except StaleElementReferenceException:
                    reintentos -= 1
                    print(f"Advertencia: El elemento {idx+1} se ha actualizado en el DOM. Reintentando ({3 - reintentos}/3)")

        # Resumen de resultados
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- Total de elementos enfocados: {elementos_con_enfoque_claro + elementos_sin_enfoque_claro} de {total_elementos}")
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- Elementos con cambio visual al enfocarse: {elementos_con_enfoque_claro}")
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- Elementos sin cambio visual: {elementos_sin_enfoque_claro}")
        
    except Exception as e:
        print(f"Error en la verificación de accesibilidad mediante teclado: {e}")

    # Cerrar el driver
    driver.quit()

# Ejemplo de uso
#verificar_accesibilidad_teclado('https://www.mercadolibre.cl')

def verificar_accesibilidad_errores(url):
    # Configurar el driver de Selenium en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Accesibilidad de Errores:", ln=True, align='L')
    # Navegar a la URL
    driver.get(url)
    
    try:
        # Buscar elementos que podrían contener mensajes de error o advertencias
        mensajes_error = driver.find_elements(By.CSS_SELECTOR, '[role="alert"], [aria-live]')
        
        total_mensajes = len(mensajes_error)
        mensajes_accesibles = 0

        for idx, mensaje in enumerate(mensajes_error, start=1):
            # Verificar que el mensaje esté en un formato de texto legible por asistentes
            texto_mensaje = mensaje.text.strip()
            es_accesible = False
            
            if texto_mensaje:
                # Verificar que tenga atributos accesibles
                aria_live = mensaje.get_attribute('aria-live')
                role_alert = mensaje.get_attribute('role')

                if (aria_live in ['assertive', 'polite']) or (role_alert == 'alert'):
                    es_accesible = True
                    mensajes_accesibles += 1
            
            if es_accesible:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 6, f"- Mensaje de error/advertencia {idx} es accesible: '{texto_mensaje}'")
            else:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 6, f"- Advertencia: Mensaje de error/advertencia {idx} podría no ser accesible o no tiene descripción clara.")

        # Resumen mejorado
        if total_mensajes > 0:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- \nTotal de mensajes de error/accesibles: {mensajes_accesibles} de {total_mensajes}")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- No se encontraron mensajes de error o advertencia accesibles en la página.")
        
    except Exception as e:
        print(f"Error en la verificación de accesibilidad de errores o advertencias: {e}")

    # Cerrar el driver
    driver.quit()

# Ejemplo de uso
#verificar_accesibilidad_errores('https://www.mercadolibre.cl')

def luminancia(color):
    """Calcula la luminancia relativa de un color en formato RGB."""
    def canal(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    
    r, g, b = color
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)

def contraste(color1, color2):
    """Calcula el contraste entre dos colores en formato RGB."""
    lum1 = luminancia(color1)
    lum2 = luminancia(color2)
    if lum1 > lum2:
        return (lum1 + 0.05) / (lum2 + 0.05)
    else:
        return (lum2 + 0.05) / (lum1 + 0.05)

def parse_rgb(color_str):
    """Convierte una cadena de color CSS en formato RGB o HEX a una tupla de enteros RGB."""
    if "rgb" in color_str:
        try:
            rgb_values = color_str.replace("rgb(", "").replace(")", "").split(",")
            return tuple(map(int, rgb_values))
        except ValueError:
            return None
    elif "#" in color_str and (len(color_str) == 7 or len(color_str) == 4):
        hex_color = color_str.lstrip("#")
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        elif len(hex_color) == 3:
            return tuple(int(hex_color[i]*2, 16) for i in range(3))
    return None

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
import re

def parse_rgb(color):
    """Convierte una cadena RGB a una tupla."""
    try:
        rgb = re.findall(r'\d+', color)
        return tuple(map(int, rgb[:3]))
    except:
        return None

def calcular_luminancia(rgb):
    """Calcula la luminancia relativa de un color RGB."""
    r, g, b = [x / 255.0 for x in rgb]
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contraste(rgb1, rgb2):
    """Calcula el ratio de contraste entre dos colores RGB."""
    l1 = calcular_luminancia(rgb1)
    l2 = calcular_luminancia(rgb2)
    return (l1 + 0.05) / (l2 + 0.05) if l1 > l2 else (l2 + 0.05) / (l1 + 0.05)

def verificar_contraste_accesibilidad(url):
    # Configurar el driver de Selenium en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Navegar a la URL
    driver.get(url)
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Accesibilidad de Contraste:", ln=True, align='L')
    try:
        # Verificación de textos
        elementos_texto = driver.find_elements(By.CSS_SELECTOR, 'p, h1, h2, h3, h4, h5, h6, span, div')
        texto_accesible = 0
        total_texto = len(elementos_texto)

        for elemento in elementos_texto:
            color_texto = elemento.value_of_css_property('color')
            color_fondo = elemento.value_of_css_property('background-color')

            color_texto_rgb = parse_rgb(color_texto)
            color_fondo_rgb = parse_rgb(color_fondo) or (255, 255, 255)  # Fondo blanco predeterminado

            if color_texto_rgb and color_fondo_rgb:
                ratio = contraste(color_texto_rgb, color_fondo_rgb)
                if ratio >= 4.5:  # Nivel WCAG AA
                    texto_accesible += 1

        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- Total de textos con contraste adecuado: {texto_accesible} de {total_texto}")

        # Verificación de imágenes
        elementos_imagen = driver.find_elements(By.TAG_NAME, 'img')
        imagen_accesible = 0
        total_imagenes = len(elementos_imagen)

        for imagen in elementos_imagen:
            alt_text = imagen.get_attribute('alt')
            if alt_text and alt_text.strip():
                imagen_accesible += 1

        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- Total de imágenes con texto alternativo: {imagen_accesible} de {total_imagenes}")

    except Exception as e:
        print(f"Error en la verificación de contraste o accesibilidad: {e}")
    finally:
        driver.quit()

# Ejemplo de uso
#verificar_contraste_accesibilidad('https://www.mercadolibre.cl')

def verificar_indicador_ubicacion(url):
    # Configurar el driver de Selenium en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    # Navegar a la URL
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Accesibilidad de Indicadores:", ln=True, align='L')
    # Navegar a la URL
    driver.get(url)

    try:
        # Buscar elementos que podrían actuar como indicadores de ubicación actual
        indicadores = driver.find_elements(By.CSS_SELECTOR, 
            '.active, [aria-current="page"], .current, .selected, [data-active="true"], .highlighted, .nav-current, .breadcrumb, .breadcrumb-item-active'
        )

        # Añadir una verificación adicional para elementos con estilos específicos de fondo o color
        elementos_navegacion = driver.find_elements(By.CSS_SELECTOR, 'nav a, .menu a, .breadcrumb-item, .sidebar a')
        for elemento in elementos_navegacion:
            bg_color = elemento.value_of_css_property('background-color')
            text_color = elemento.value_of_css_property('color')
            # Definir un color distintivo para considerar como "activo" (simplificado, puede ser personalizado)
            if bg_color != 'rgba(0, 0, 0, 0)' or text_color != 'rgba(0, 0, 0, 0)':
                indicadores.append(elemento)

        # Resumen de indicadores encontrados
        total_indicadores = len(indicadores)
        if total_indicadores > 0:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Se encontraron {total_indicadores} posibles indicadores de la ubicación actual del usuario: ")
            for idx, indicador in enumerate(indicadores, start=1):
                nombre = indicador.text.strip() or indicador.get_attribute('aria-label') or "Sin texto visible"
                clase = indicador.get_attribute('class') or "Sin clase específica"
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 6, f"     » Indicador {idx}: '{nombre}', Clase/CSS: '{clase}'")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, "- No se encontró un indicador claro de la ubicación actual en la interfaz.")

    except Exception as e:
        print(f"Error en la verificación de indicador de ubicación: {e}")

    # Cerrar el driver
    driver.quit()

# Ejemplo de uso
#verificar_indicador_ubicacion('https://www.mercadolibre.cl')

def verificar_claridad_enlaces(url):
    # Configurar el driver de Selenium en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Accesibilidad de Enlaces:", ln=True, align='L')
    # Navegar a la URL
    driver.get(url)

    try:
        enlaces = driver.find_elements(By.CSS_SELECTOR, 'a')
        total_enlaces = len(enlaces)
        enlaces_no_claros = 0

        for enlace in enlaces:
            texto = enlace.text.strip()
            aria_label = enlace.get_attribute('aria-label')
            title = enlace.get_attribute('title')
            color = enlace.value_of_css_property('color')
            subrayado = enlace.value_of_css_property('text-decoration')

            # Condiciones de claridad del enlace
            es_claro = (texto and texto.lower() not in ["click aquí", "aquí", "leer más"]) or aria_label or title
            es_distinguible = 'underline' in subrayado or color != 'rgba(0, 0, 0, 1)'

            if not (es_claro and es_distinguible):
                enlaces_no_claros += 1

        # Resumen de enlaces claros
        if total_enlaces > 0:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Total de enlaces claros y distinguibles: {total_enlaces - enlaces_no_claros} de {total_enlaces}")
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Total de enlaces no claros o no distinguibles: {enlaces_no_claros}")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, "- No se encontraron enlaces en la página.")

    except Exception as e:
        print(f"Error en la verificación de claridad de enlaces: {e}")

    # Cerrar el driver
    driver.quit()

# Ejemplo de uso
#verificar_claridad_enlaces('https://www.mercadolibre.cl')

import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import ElementNotInteractableException, MoveTargetOutOfBoundsException, WebDriverException

def verificar_visibilidad_enfoque(url):
    # Configuración del driver de Selenium en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Accesibilidad de Enfoque:", ln=True, align='L')
    # Navegar a la URL
    driver.get(url)

    try:
        # Encuentra todos los elementos interactivos (botones, enlaces, campos de entrada)
        elementos_interactivos = driver.find_elements(By.CSS_SELECTOR, 'button, a, input, textarea, select')
        total_elementos = len(elementos_interactivos)
        elementos_visibles = 0
        elementos_ocultos = 0

        for idx, elemento in enumerate(elementos_interactivos, start=1):
            try:
                # Descartar elementos sin tamaño o ubicación
                rect = elemento.rect
                if rect['width'] == 0 or rect['height'] == 0:
                    print(f"Elemento {idx} no tiene dimensiones visibles, omitiendo.")
                    elementos_ocultos += 1
                    continue
                
                # Desplazarse hacia el elemento y simular el enfoque
                ActionChains(driver).move_to_element(elemento).perform()
                driver.execute_script("arguments[0].focus();", elemento)

                # Verificar si el elemento está completamente visible en la ventana
                if elemento.is_displayed() and rect['y'] >= 0 and (rect['y'] + rect['height']) <= driver.execute_script("return window.innerHeight"):
                    elementos_visibles += 1
                else:
                    elementos_ocultos += 1
            except (ElementNotInteractableException, MoveTargetOutOfBoundsException, WebDriverException):
                elementos_ocultos += 1  # Contabilizar como oculto si no se puede enfocar

        # Resumen de visibilidad de los elementos enfocados
        if total_elementos > 0:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Total de elementos completamente visibles: {elementos_visibles} de {total_elementos}")
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Total de elementos enfocados pero oscurecidos o parcialmente visibles: {elementos_ocultos}")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- No se encontraron elementos interactivos en la página.")

    except Exception as e:
        print(f"Error en la verificación de visibilidad de elementos enfocados: {e}")

    # Cerrar el driver
    driver.quit()

# Ejemplo de uso
#verificar_visibilidad_enfoque('https://www.mercadolibre.cl')


from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException

def verificar_categorias_visibles(url):
    # Configuración del driver de Selenium en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Accesibilidad de Categorias Visibles:", ln=True, align='L')
    # Navegar a la URL
    driver.get(url)

    try:
        # Buscar elementos que podrían representar categorías
        categorias = driver.find_elements(By.CSS_SELECTOR, 'nav, section, a[role="menuitem"], li, div[role="navigation"]')

        total_categorias = len(categorias)
        categorias_claras = 0

        for idx, categoria in enumerate(categorias, start=1):
            try:
                texto_categoria = categoria.text.strip()
                if texto_categoria:  # Verificar si la categoría tiene texto relevante
                    categorias_claras += 1
            except WebDriverException:
                continue  # Ignorar categorías que no sean accesibles

        # Resumen final
        if total_categorias > 0:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Total de categorías claramente visibles: {categorias_claras} de {total_categorias}")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- No se encontraron categorías en la página.")

    except Exception as e:
        print(f"Error en la verificación de categorías visibles: {e}")

    # Cerrar el driver
    driver.quit()

# Ejemplo de uso
#verificar_categorias_visibles('https://www.mercadolibre.cl')

import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver

def obtener_luminancia(color_hex):
    """Convierte un color HEX a su luminancia relativa."""
    color_rgb = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    r, g, b = [x / 255.0 for x in color_rgb]
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def calcular_contraste(luminancia1, luminancia2):
    """Calcula el ratio de contraste entre dos luminancias."""
    return (luminancia1 + 0.05) / (luminancia2 + 0.05) if luminancia1 > luminancia2 else (luminancia2 + 0.05) / (luminancia1 + 0.05)

def parse_rgb(color_string):
    """Extrae valores RGB de una cadena CSS de color."""
    match = re.search(r'rgb(?:a)?\((\d+),\s*(\d+),\s*(\d+)', color_string)
    if match:
        return tuple(map(int, match.groups()))
    else:
        raise ValueError(f"Formato de color inválido: {color_string}")

def verificar_contraste_hipertextos(url):
    # Configuración del driver de Selenium en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Navegar a la URL
    driver.get(url)
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Accesibilidad de Hipertextos:", ln=True, align='L')

    try:
        hipertextos = driver.find_elements(By.CSS_SELECTOR, 'a')
        total_enlaces = len(hipertextos)
        enlaces_con_contraste_alto = 0

        for enlace in hipertextos:
            try:
                color_texto = enlace.value_of_css_property('color')
                background_color = enlace.value_of_css_property('background-color')

                # Intentar obtener valores RGB
                color_texto_rgb = parse_rgb(color_texto)
                color_texto_hex = '#{:02x}{:02x}{:02x}'.format(*color_texto_rgb)

                try:
                    background_color_rgb = parse_rgb(background_color)
                    background_color_hex = '#{:02x}{:02x}{:02x}'.format(*background_color_rgb)
                except ValueError:
                    background_color_hex = '#ffffff'  # Fondo blanco por defecto

                luminancia_texto = obtener_luminancia(color_texto_hex)
                luminancia_fondo = obtener_luminancia(background_color_hex)

                ratio_contraste = calcular_contraste(luminancia_texto, luminancia_fondo)

                if ratio_contraste >= 4.5:  # Nivel AA de WCAG para texto normal
                    enlaces_con_contraste_alto += 1

            except ValueError as ve:
                print(f"Error procesando enlace: {ve}")
            except WebDriverException:
                print("Error WebDriver procesando enlace, omitiendo.")

        # Resumen final
        if total_enlaces > 0:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Total de hipertextos con contraste adecuado: {enlaces_con_contraste_alto} de {total_enlaces}")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- No se encontraron enlaces en la página.")
    except Exception as e:
        print(f"Error en la verificación de contraste de hipertextos: {e}")
    finally:
        driver.quit()

# Ejemplo de uso
#verificar_contraste_hipertextos('https://www.mercadolibre.cl')

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from PIL import Image
import io
import numpy as np

def medir_espacio_blanco(url):
    # Configuración del driver de Selenium en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Accesibilidad de Espacios:", ln=True, align='L')
    # Navegar a la URL
    driver.get(url)

    try:
        # Capturar una captura de pantalla de la página completa
        screenshot = driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(screenshot))

        # Convertir la imagen a escala de grises
        grayscale_image = image.convert('L')

        # Calcular la densidad de píxeles blancos y no blancos
        image_array = np.array(grayscale_image)
        total_pixels = image_array.size
        white_pixels = np.sum(image_array > 240)  # Consideramos píxeles con un valor muy claro como espacio en blanco
        non_white_pixels = total_pixels - white_pixels

        # Calcular el porcentaje de espacio en blanco y contenido
        porcentaje_blanco = (white_pixels / total_pixels) * 100
        porcentaje_contenido = (non_white_pixels / total_pixels) * 100

        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- Porcentaje de espacio en blanco: {porcentaje_blanco:.2f}%")
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- Porcentaje de contenido: {porcentaje_contenido:.2f}%")

    except Exception as e:
        print(f"Error en la medición de espacio en blanco: {e}")
    finally:
        driver.quit()

# Ejemplo de uso
#medir_espacio_blanco('https://www.mercadolibre.cl')

def verificar_posicion_caja_busqueda(url):
    # Configuración del driver de Selenium en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Navegar a la URL
    driver.get(url)
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Accesibilidad de Búsqueda:", ln=True, align='L')

    try:
        # Ampliar selectores posibles para cajas de búsqueda
        selectores_posibles = [
            'input[type="search"]',
            'input[name="q"]',
            'input[placeholder*="Buscar"]',
            'input[aria-label*="Buscar"]',
            'input[class*="search"]',
            'input[id*="search"]'
        ]

        # Intentar localizar la caja de búsqueda con múltiples selectores
        caja_busqueda = None
        for selector in selectores_posibles:
            try:
                caja_busqueda = driver.find_element(By.CSS_SELECTOR, selector)
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 6, f"- Caja de búsqueda encontrada con el selector: {selector}")
                break
            except NoSuchElementException:
                continue

        if not caja_busqueda:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- No se encontró la caja de búsqueda con los selectores definidos.")

        # Obtener la posición (coordenadas) del elemento
        location = caja_busqueda.location
        y_position = location['y']

        # Definir un umbral de altura para considerar si está "en la parte superior"
        umbral_superior = 200  # En píxeles

        if y_position <= umbral_superior:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- La caja de búsqueda está ubicada en la parte superior de la página (y = {y_position}px).")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Advertencia: La caja de búsqueda no está en la parte superior esperada (y = {y_position}px).")

    except Exception as e:
        print(f"Error al verificar la posición de la caja de búsqueda: {e}")
    finally:
        driver.quit()

# Ejemplo de uso
#verificar_posicion_caja_busqueda('https://www.mercadolibre.cl')

def verificar_estructura_contenido(url):
    # Configuración del driver de Selenium en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Accesibilidad de Contenido:", ln=True, align='L')
    # Navegar a la URL
    driver.get(url)

    try:
        # Verificar la jerarquía de encabezados
        encabezados = driver.find_elements(By.CSS_SELECTOR, 'h1, h2, h3, h4, h5, h6')
        total_encabezados = len(encabezados)

        # Verificar el uso de listas
        listas = driver.find_elements(By.CSS_SELECTOR, 'ul, ol')
        total_listas = len(listas)

        cumple_jerarquia = total_encabezados > 0
        cumple_listas = total_listas > 0

        if cumple_jerarquia:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Se encontraron {total_encabezados} encabezados. Cumplen con las prácticas requeridas por la guía de accesiblidad.")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- No se encontraron encabezados. Podría deberse a problemas de accesiblidad.")

        if cumple_listas:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Se encontraron {total_listas} listas. Cumplen con las prácticas requeridas por la guía de accesiblidad.")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- No se encontraron listas. Podría deberse a problemas de accesiblidad.")

    except Exception as e:
        print(f"Error al analizar la estructura de contenido: {e}")
    finally:
        driver.quit()

# Ejemplo de uso
#verificar_estructura_contenido('https://www.mercadolibre.cl')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, UnexpectedAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import re

def check_ui_flow(url):
    """Verifica el flujo lógico y las instrucciones claras en la UI."""
    pdf.set_font("Arial", size=14)
    pdf.ln(10)
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(200, 10, txt="Criterio: Validación de Accesibilidad", ln=True, align='C')
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ejecución en segundo plano
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    found_instructions = False
    found_buttons = False

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Flujo Lógico e Instrucciones Claras en la UI", ln=True, align='L')

    try:
        driver.get(url)

        # Esperar a que el contenido de la página esté completamente cargado
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//body")))

        # Buscar elementos con instrucciones explícitas
        steps = driver.find_elements(By.XPATH, "//p[contains(text(), 'Paso') or contains(text(), 'Instrucción') or contains(text(), 'Siguiente')]")
        buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Siguiente') or contains(text(), 'Continuar') or contains(text(), 'Finalizar')]")
        
        # Verificar instrucciones explícitas
        if steps:
            found_instructions = True
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- {len(steps)} instrucciones explícitas encontradas:")
            for step in steps:
                pdf.set_x(15)
                pdf.multi_cell(0, 6, f"   - {step.text.strip()}")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron instrucciones explícitas en la UI.")

        # Verificar botones de navegación
        if buttons:
            found_buttons = True
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- {len(buttons)} botones de navegación encontrados:")
            for button in buttons:
                pdf.set_x(15)
                pdf.multi_cell(0, 6, f"   - {button.text.strip()}")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron botones de navegación para continuar el flujo.")

        # Simular la navegación con búsqueda dinámica
        for button_text in [btn.text for btn in buttons]:
            try:
                button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, f"//button[contains(text(), '{button_text}')]"))
                )
                button.click()
                WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, "//body")))
            except StaleElementReferenceException:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, f"- El botón '{button_text}' ya no es válido.")
            except TimeoutException:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, f"- Tiempo de espera agotado al buscar el botón: {button_text}")
            except Exception as e:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, f"- Error al interactuar con el botón: {button_text}. {str(e)}")

    except Exception as e:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, f"- Error al cargar la página o encontrar elementos: {str(e)}")
    finally:
        driver.quit()

    # Veredicto final
    if found_instructions and found_buttons:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, "- La página CUMPLE con el criterio de flujo lógico e instrucciones claras.")
    else:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, "- La página NO CUMPLE con el criterio de flujo lógico e instrucciones claras.")


def check_feedback(url):
    """Verifica la retroalimentación positiva tras completar tareas en un sitio."""
    
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Retroalimentación Positiva para el Usuario tras la Compleción de Tareas", ln=True, align='L')

    # Configurar Firefox con modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//body")))

        messages = driver.find_elements(By.XPATH, "//div[contains(text(), 'Éxito') or contains(text(), 'Completado') or contains(text(), 'Gracias') or contains(text(), 'Hecho') or contains(text(), 'Correcto')]")
        icons = driver.find_elements(By.XPATH, "//span[contains(@class, 'success') or contains(@class, 'check') or contains(@class, 'done')]")

        if messages:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- {len(messages)} mensajes de retroalimentación positiva encontrados:")
            for message in messages:
                pdf.set_x(15)
                pdf.multi_cell(0, 6, f"   - {message.text.strip()}")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron mensajes textuales de retroalimentación positiva.")

        if icons:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- {len(icons)} íconos visuales de retroalimentación positiva encontrados.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron íconos visuales de retroalimentación positiva.")

        if messages or icons:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página CUMPLE con el criterio de retroalimentación positiva.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página NO CUMPLE con el criterio de retroalimentación positiva.")

    except TimeoutException:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, "- Error: La página tardó demasiado en cargar o no contiene elementos esperados.")
    except Exception as e:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, f"- Error inesperado: {str(e)}")
    finally:
        driver.quit()

def get_internal_links(driver, base_url):
    """Recoge todos los enlaces internos del sitio."""
    internal_links = set()
    try:
        links = driver.find_elements(By.TAG_NAME, 'a')
        for link in links:
            href = link.get_attribute('href')
            if href and base_url in href:
                internal_links.add(href)
    except Exception as e:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, f"- Error al obtener enlaces internos: {str(e)}")
    return internal_links

def check_distractors(driver, url):
    """Verifica la presencia de pop-ups y redirecciones en una página."""
    result = {"url": url, "loaded": False, "popup": False}
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "body")))
        result["loaded"] = True

        # Verificar anuncios emergentes
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            result["popup"] = True
            alert.dismiss()
        except TimeoutException:
            pass

    except UnexpectedAlertPresentException:
        result["popup"] = True
    except Exception as e:
        pass

    return result


def crawl_site(url, max_pages=10):
    """Crawlea el sitio web, analiza distractores y genera un informe PDF."""

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Detección de Elementos Distractores en Rutas Críticas del Sitio", ln=True, align='L')

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    base_url = url
    visited = set()
    to_visit = {base_url}
    results = []

    try:
        while to_visit and len(results) < max_pages:
            current_url = to_visit.pop()
            if current_url not in visited:
                result = check_distractors(driver, current_url)
                results.append(result)
                visited.add(current_url)

                # Obtener nuevos enlaces internos para visitar
                internal_links = get_internal_links(driver, base_url)
                to_visit.update(internal_links - visited)

    finally:
        driver.quit()

    # Consolidar e imprimir resultados
    loaded_pages = sum(1 for r in results if r["loaded"])
    popups_detected = sum(1 for r in results if r["popup"])

    pdf.set_font("Arial", size=8)
    pdf.set_x(15)
    pdf.multi_cell(0, 6, f"- {loaded_pages}/10 páginas cargadas correctamente.")
    pdf.set_x(15)
    pdf.multi_cell(0, 6, f"- {popups_detected}/10 páginas detectaron anuncios emergentes.")


def perform_search(url, query="test"):
    """Simula una búsqueda global, valida la cobertura del sitio y genera un informe."""
    
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Cobertura Completa del Sitio en Funcionalidades de Búsqueda", ln=True, align='L')

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-webgl")
    chrome_options.add_argument("--disable-webgl2")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--use-gl=swiftshader")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(url)

        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='text' or @name='q' or @id='search']"))
        )
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, "- Campo de búsqueda encontrado.")
        
        search_box.clear()
        search_box.send_keys(query)
        search_box.submit()

        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, 'http')]"))
        )

        result_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'http')]")
        links = [link.get_attribute('href') for link in result_links if link.get_attribute('href')]

        validate_site_coverage(links, url)

    except TimeoutException:
        pdf.set_x(15)
        pdf.multi_cell(0, 6, "- La búsqueda tomó demasiado tiempo o no se encontraron resultados.")
    except NoSuchElementException:
        pdf.set_x(15)
        pdf.multi_cell(0, 6, "- No se encontró el campo de búsqueda o no se cargaron resultados.")
    finally:
        driver.quit()

def validate_site_coverage(links, base_url):
    """Valida que los resultados cubran diferentes secciones del sitio y consolida resultados."""
    
    sections_covered = set()
    pattern = re.compile(rf"{re.escape(base_url)}(?:/([^/?#]+))?")

    for link in links:
        match = pattern.match(link)
        if match:
            section = match.group(1) if match.group(1) else "home"
            sections_covered.add(section)

    pdf.set_font("Arial", size=8)
    pdf.set_x(15)
    pdf.multi_cell(0, 6, f"- {len(links)} resultados encontrados.")
    pdf.set_x(15)
    pdf.multi_cell(0, 6, f"- Cobertura realizada a {len(sections_covered)} secciones del sitio")

def check_navigation_feedback(url):
    """Verifica si el sitio proporciona retroalimentación de navegación clara (breadcrumbs o sección resaltada)."""
    
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Retroalimentación de Navegación en el Sitio", ln=True, align='L')

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, f"- Página cargada correctamente: {url}")
        
        # Verificar la existencia de breadcrumbs
        try:
            breadcrumbs = driver.find_element(By.XPATH, "//nav[contains(@class, 'breadcrumb') or contains(@aria-label, 'breadcrumb')]")
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- Breadcrumbs encontrados: {breadcrumbs.text}")
        except NoSuchElementException:
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron breadcrumbs.")

        # Verificar si la sección actual está resaltada en el menú de navegación
        try:
            active_section = driver.find_element(By.XPATH, "//nav//a[contains(@class, 'active') or contains(@aria-current, 'page')]")
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- Sección actual resaltada: {active_section.text}")
        except NoSuchElementException:
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontró ninguna sección resaltada.")

    except TimeoutException:
        pdf.set_x(15)
        pdf.multi_cell(0, 6, f"- La página {url} tomó demasiado tiempo en cargar.")
    except Exception as e:
        pdf.set_x(15)
        pdf.multi_cell(0, 6, f"- Error al verificar {url}: {str(e)}")
    finally:
        driver.quit()

def check_error_messages(url):
    """Verifica mensajes de error claros y directivos en la UI."""

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Validación de Mensajes de Error Claros y Directos", ln=True, align='L')

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//body")))

        # Buscar mensajes de error
        error_messages = driver.find_elements(By.XPATH, "//div[contains(text(), 'Error') or contains(text(), 'Incorrecto') or contains(text(), 'Fallo') or contains(text(), 'Inválido')]")
        instructions = driver.find_elements(By.XPATH, "//p[contains(text(), 'Intente nuevamente') or contains(text(), 'Corrija') or contains(text(), 'Revise')]")

        # Verificar mensajes de error
        if error_messages:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- {len(error_messages)} mensajes de error encontrados:")
            for msg in error_messages:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, f"   - {msg.text.strip()}")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron mensajes de error en la UI.")

        # Verificar instrucciones claras para corregir el error
        if instructions:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- {len(instructions)} instrucciones para corregir errores encontradas:")
            for instr in instructions:
                pdf.set_x(15)
                pdf.multi_cell(0, 6, f"- {instr.text.strip()}")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron instrucciones claras para corregir errores.")

        # Comprobación final
        if error_messages and instructions:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página CUMPLE con el criterio de mensajes de error claros y directivos.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página NO CUMPLE con el criterio de mensajes de error claros y directivos.")

    except TimeoutException:
        print("- La página tardó demasiado en cargar o no contiene elementos esperados.")
    except Exception as e:
        print(f"- Error inesperado: {str(e)}")
    finally:
        driver.quit()

def hdu_cuatro(url):
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
    
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Verificación de Legibilidad de Texto en la UI", ln=True, align='L')
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
                pdf.multi_cell(0, 6, txt=f"- Advertencia: Texto con legibilidad insuficiente encontrado: '{text[:50].replace(backslash, '')}...'{backslash}  Gunning Fog: {gunning_fog}, Flesch Reading Ease: {flesch_reading_ease}")      
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

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Verificación de Coherencia entre Enlaces y Títulos de Página", ln=True, align='L')

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
                pdf.multi_cell(0, 6, f"- Advertencia: El enlace '{safe_link_text.replace(backslash, '')}' NO coincide con el título de la página de destino: '{safe_page_title.replace(backslash, '')}'")
                
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
    pdf.multi_cell(0, 6, txt=f"- Número de enlaces que coinciden con el título de la página de destino: {enlaces_coinciden}")

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

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Verificación de Enlaces con Texto Genérico", ln=True, align='L')

    # Navegar a la URL
    driver.get(url)

    # Buscar todos los enlaces visibles
    enlaces = driver.find_elements(By.TAG_NAME, 'a')
    textos_genericos = ["click aquí", "haga clic aquí", "aquí", "leer más", "ver más", "más información"]

    enlaces_genericos_count = 0  # Conta    dor de enlaces genéricos
    enlaces_correctos_count = 0  # Contador de enlaces correctos

    for enlace in enlaces:
        if enlace.is_displayed() and enlace.get_attribute('href'):
            link_text = enlace.text.strip().lower()

            # Verificar si el texto del enlace es genérico
            if any(texto_generico in link_text for texto_generico in textos_genericos):
                enlaces_genericos_count += 1
            else:
                enlaces_correctos_count += 1

    # Añadir resumen al PDF
    pdf.set_font("Arial", size=10)
    pdf.set_x(15)
    pdf.multi_cell(0, 6, txt=f"- Número total de enlaces con texto descriptivo: {enlaces_correctos_count}")

    # Guardar el PDF con los resultados
    #output_filename = "reporte_enlaces_genericos.pdf"
    #pdf.output(output_filename, dest='F')

    # Cerrar el navegador
    driver.quit()

def verificar_autenticacion_facil(url):
    # Configurar Selenium con Chrome en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless=old")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Configurar directorios
    capturas_dir = "capturas_selenium"
    auth_dir = os.path.join(capturas_dir, "authentication")
    os.makedirs(auth_dir, exist_ok=True)

    
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Verificación de Métodos de Autenticación en la UI", ln=True, align='L')

    # Navegar a la URL
    driver.get(url)

    # Verificar si existen métodos de autenticación que no dependan únicamente de pruebas cognitivas
    autenticacion_alternativa_encontrada = False

    # Buscar formularios de autenticación
    forms = driver.find_elements(By.TAG_NAME, 'form')
    for form_index, form in enumerate(forms, start=1):
        # Verificar si el formulario parece ser de autenticación (verificar campos relacionados con usuario/contraseña)
        input_elements = form.find_elements(By.TAG_NAME, 'input')
        campos_usuario = [elem for elem in input_elements if 'user' in elem.get_attribute('name').lower() or 'email' in elem.get_attribute('name').lower()]
        campos_contraseña = [elem for elem in input_elements if 'pass' in elem.get_attribute('name').lower()]

        if campos_usuario and campos_contraseña:
            # Encontró un formulario de autenticación
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, txt=f"- Formulario de autenticación común encontrado (Formulario #{form_index}).")
            
            # Verificar si hay métodos alternativos (ej.: opciones biométricas, enlace mágico, etc.)
            botones = form.find_elements(By.TAG_NAME, 'button')
            botones_texto = [boton.text.lower() for boton in botones]
            alternativas = ['biométrico', 'huella', 'reconocimiento facial', 'pin', 'enlace mágico', 'sin contraseña']

            autenticacion_alternativas = []

            for alternativa in alternativas:
                if any(alternativa in texto for texto in botones_texto):
                    autenticacion_alternativa_encontrada = True
                    autenticacion_alternativas.append(alternativa)
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(0, 6, txt=f"  - Método de autenticación alternativa encontrado: {alternativa.capitalize()}")

            # Verificar si el formulario tiene captcha complejo (indicador de autenticación difícil)
            if any('captcha' in elem.get_attribute('class').lower() for elem in form.find_elements(By.XPATH, ".//*[contains(@class, 'captcha')]")):
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, txt="  - Advertencia: Se encontró un CAPTCHA, podría dificultar la autenticación.")

            # Capturar la imagen del formulario de autenticación
            form_location = form.location
            form_size = form.size
            screenshot_path = os.path.join(auth_dir, "captura_completa.png")
            driver.save_screenshot(screenshot_path)
            
            # Recortar la imagen del formulario
            with Image.open(screenshot_path) as img:
                left = form_location['x']
                top = form_location['y']
                right = left + form_size['width']
                bottom = top + form_size['height']
                region_recortada = img.crop((left, top, right, bottom))
                captura_form = os.path.join(auth_dir, f"formulario_autenticacion_{form_index}.png")
                region_recortada.save(captura_form)

                # Filtrar imágenes según el tamaño y contenido útil
                if form_size['width'] < 800 and form_size['height'] < 600:  # Filtrar solo formularios de tamaño adecuado
                    if not is_mostly_black(captura_form):
                        pdf.image(captura_form, x=15, y=None)  # Añadir la captura al PDF manteniendo su tamaño original
                    else:
                        print(f"La captura {captura_form} fue descartada por ser mayoritariamente negra.")
                        os.remove(captura_form)  # Eliminar la captura si no es útil

            # Añadir información sobre los métodos de autenticación encontrados al PDF
            if autenticacion_alternativas:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, txt=f"  - Métodos de autenticación alternativa disponibles: {', '.join(autenticacion_alternativas)}")

    # Si no se encontraron alternativas a pruebas cognitivas difíciles
    if not autenticacion_alternativa_encontrada:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, txt="- Advertencia: No se encontraron métodos de autenticación alternativos que no dependan de la función cognitiva.")

    # Guardar el PDF con los resultados
   

    # Cerrar el navegador
    driver.quit()

    # Eliminar el directorio de capturas al finalizar
    if os.path.exists(capturas_dir):
        shutil.rmtree(capturas_dir)

def is_mostly_black(image_path, threshold=0.9):
    """ Verifica si la imagen tiene más de `threshold` porcentaje de píxeles negros """
    with Image.open(image_path) as img:
        img = img.convert('L')  # Convertir a escala de grises
        num_pixels = img.width * img.height
        num_black_pixels = sum(1 for pixel in img.getdata() if pixel < 30)  # Umbral para considerar un píxel "negro"
        black_ratio = num_black_pixels / num_pixels
        return black_ratio >= threshold
    
def verificar_autenticacion_facil(url):
    # Configurar Selenium con Chrome en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless=old")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Configurar directorios
    capturas_dir = "capturas_selenium"
    auth_dir = os.path.join(capturas_dir, "authentication")
    os.makedirs(auth_dir, exist_ok=True)

    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Verificación de Métodos de Autenticación en la UI", ln=True, align='L')

    # Navegar a la URL
    driver.get(url)

    # Verificar si existen métodos de autenticación que no dependan únicamente de pruebas cognitivas
    autenticacion_alternativa_encontrada = False

    # Buscar formularios de autenticación
    forms = driver.find_elements(By.TAG_NAME, 'form')
    for form_index, form in enumerate(forms, start=1):
        # Verificar si el formulario parece ser de autenticación (verificar campos relacionados con usuario/contraseña)
        input_elements = form.find_elements(By.TAG_NAME, 'input')
        campos_usuario = [elem for elem in input_elements if 'user' in elem.get_attribute('name').lower() or 'email' in elem.get_attribute('name').lower()]
        campos_contraseña = [elem for elem in input_elements if 'pass' in elem.get_attribute('name').lower()]

        if campos_usuario and campos_contraseña:
            # Encontró un formulario de autenticación
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, txt=f"- Formulario de autenticación común encontrado (Formulario #{form_index}).")
            
            # Verificar si hay métodos alternativos (ej.: opciones biométricas, enlace mágico, etc.)
            botones = form.find_elements(By.TAG_NAME, 'button')
            botones_texto = [boton.text.lower() for boton in botones]
            alternativas = ['biométrico', 'huella', 'reconocimiento facial', 'pin', 'enlace mágico', 'sin contraseña']

            autenticacion_alternativas = []

            for alternativa in alternativas:
                if any(alternativa in texto for texto in botones_texto):
                    autenticacion_alternativa_encontrada = True
                    autenticacion_alternativas.append(alternativa)
                    pdf.set_font("Arial", size=8)
                    pdf.set_x(15)
                    pdf.multi_cell(0, 6, txt=f"  - Método de autenticación alternativa encontrado: {alternativa.capitalize()}")

            # Verificar si el formulario tiene captcha complejo (indicador de autenticación difícil)
            if any('captcha' in elem.get_attribute('class').lower() for elem in form.find_elements(By.XPATH, ".//*[contains(@class, 'captcha')]")):
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, txt="  - Advertencia: Se encontró un CAPTCHA, podría dificultar la autenticación.")

            # Capturar la imagen del formulario de autenticación
            form_location = form.location
            form_size = form.size
            screenshot_path = os.path.join(auth_dir, "captura_completa.png")
            driver.save_screenshot(screenshot_path)
            
            # Recortar la imagen del formulario
            with Image.open(screenshot_path) as img:
                left = form_location['x']
                top = form_location['y']
                right = left + form_size['width']
                bottom = top + form_size['height']
                region_recortada = img.crop((left, top, right, bottom))
                captura_form = os.path.join(auth_dir, f"formulario_autenticacion_{form_index}.png")
                region_recortada.save(captura_form)

                # Filtrar imágenes según el tamaño y contenido útil
                if form_size['width'] < 800 and form_size['height'] < 600:  # Filtrar solo formularios de tamaño adecuado
                    if not is_mostly_black(captura_form):
                        pdf.image(captura_form, x=15, y=None)  # Añadir la captura al PDF manteniendo su tamaño original
                    else:
                        print(f"La captura {captura_form} fue descartada por ser mayoritariamente negra.")
                        os.remove(captura_form)  # Eliminar la captura si no es útil

            # Añadir información sobre los métodos de autenticación encontrados al PDF
            if autenticacion_alternativas:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, txt=f"  - Métodos de autenticación alternativa disponibles: {', '.join(autenticacion_alternativas)}")

    # Si no se encontraron alternativas a pruebas cognitivas difíciles
    if not autenticacion_alternativa_encontrada:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, txt="- Advertencia: No se encontraron métodos de autenticación alternativos que no dependan de la función cognitiva.")

    # Guardar el PDF con los resultados
   

    # Cerrar el navegador
    driver.quit()

    # Eliminar el directorio de capturas al finalizar
    if os.path.exists(capturas_dir):
        shutil.rmtree(capturas_dir)

def is_mostly_black(image_path, threshold=0.9):
    """ Verifica si la imagen tiene más de `threshold` porcentaje de píxeles negros """
    with Image.open(image_path) as img:
        img = img.convert('L')  # Convertir a escala de grises
        num_pixels = img.width * img.height
        num_black_pixels = sum(1 for pixel in img.getdata() if pixel < 30)  # Umbral para considerar un píxel "negro"
        black_ratio = num_black_pixels / num_pixels
        return black_ratio >= threshold
  
def validate_input_targets(url):
    """Valida si los botones y enlaces cumplen con el tamaño mínimo recomendado."""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    pdf.set_font("Arial", size=14)
    pdf.ln(10)
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(200, 10, txt="Criterio: Validación de Accesibilidad", ln=True, align='C')
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Validación de Tamaño de Objetivos de Entrada", ln=True, align='L')


    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        elements = driver.find_elements(By.XPATH, "//button | //a")
        total_elements = len(elements)
        small_elements = [element for element in elements if element.size['width'] < 44 or element.size['height'] < 44]

        total_small_elements = len(small_elements)

        # Resumen consolidado
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, f"Total de objetivos de entrada analizados: {total_elements}")
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, f"Objetivos que no cumplen con el tamaño mínimo de 44x44 píxeles: {total_small_elements}")

        if total_small_elements > 0:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"Porcentaje de elementos que no cumplen: {(total_small_elements / total_elements) * 100:.2f}%")
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página NO CUMPLE con el criterio de accesibilidad en objetivos de entrada.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página CUMPLE con el criterio de accesibilidad en objetivos de entrada.")

    except TimeoutException:
        print("- Error: La página tardó demasiado en cargar.")
    except Exception as e:
        print(f"- Error inesperado: {str(e)}")
    finally:
        driver.quit()

def detect_blinking_content(url):
    """Detecta contenido que podría parpadear más de tres veces por segundo."""

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Detección de Contenidos que Parpadean", ln=True, align='L')


    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Seleccionar elementos potencialmente problemáticos
        animated_elements = driver.find_elements(By.XPATH, "//*[contains(@style, 'animation') or contains(@style, 'blink')]")
        
        if not animated_elements:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron elementos que parpadeen o tengan animaciones.")
            return
        
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, f"- Total de elementos animados o con posible parpadeo: {len(animated_elements)}")

        high_frequency_count = 0
        for element in animated_elements:
            try:
                # Verificar estilo de animación
                style = element.get_attribute("style")
                if "animation-duration" in style or "animation" in style:
                    animation_duration = extract_animation_duration(style)
                    if animation_duration and animation_duration < 0.33:
                        high_frequency_count += 1
            except Exception as e:
                print(f"- Error al analizar un elemento: {str(e)}")
        
        if high_frequency_count > 0:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- Se encontraron {high_frequency_count} elementos que podrían parpadear más de 3 veces por segundo.")
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página NO CUMPLE con el criterio de accesibilidad para prevenir contenido que parpadee.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- Todos los elementos animados cumplen con el criterio de accesibilidad.")
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página CUMPLE con el criterio de accesibilidad para contenido parpadeante.")

    except TimeoutException:
        print("- Error: La página tardó demasiado en cargar.")
    except Exception as e:
        print(f"- Error inesperado: {str(e)}")
    finally:
        driver.quit()

def extract_animation_duration(style):
    """Extrae la duración de la animación desde el atributo style."""
    try:
        duration_str = [s for s in style.split(';') if 'animation-duration' in s]
        if duration_str:
            duration_value = duration_str[0].split(':')[1].strip()
            if 's' in duration_value:
                return float(duration_value.replace('s', ''))
    except Exception as e:
        print(f"- Error al extraer duración de animación: {str(e)}")
    return None

def verificar_pestanas_navegacion(url):
    """Verifica que las pestañas de navegación estén en la parte superior y sean clickeables."""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Ubicación y Clicabilidad de las Pestañas de Navegación en la Parte Superior", ln=True, align='L')



    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Buscar la barra de navegación superior
        nav_bar = driver.find_element(By.XPATH, "//nav")

        # Verificar ubicación de la barra de navegación
        nav_bar_location = nav_bar.location['y']
        if nav_bar_location <= 200:  # En la parte superior de la página
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La barra de navegación está ubicada en la parte superior de la página.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La barra de navegación NO está ubicada en la parte superior de la página.")

        # Verificar que las pestañas dentro de la barra de navegación sean clickeables
        nav_items = nav_bar.find_elements(By.XPATH, ".//a | .//button")
        total_items = len(nav_items)
        clickeable_items = 0

        for item in nav_items:
            if item.is_displayed() and item.is_enabled():
                clickeable_items += 1

        if total_items > 0:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- Total de pestañas detectadas: {total_items}.")
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- Total de pestañas clickeables: {clickeable_items}.")
            if total_items == clickeable_items:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, "- Todas las pestañas de navegación son clickeables.")
            else:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, "- No todas las pestañas de navegación son clickeables.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron pestañas de navegación en la barra.")

    except NoSuchElementException:
        print("- No se encontró una barra de navegación.")
    except TimeoutException:
        print("- La página tardó demasiado en cargar.")
    except Exception as e:
        print(f"- Error inesperado: {str(e)}")
    finally:
        driver.quit()

def extract_color_value(style):
    """Extrae valores de color del atributo de estilo en formato RGB o HEX."""
    try:
        match_rgb = re.search(r'rgb\((\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3})\)', style)
        match_hex = re.search(r'#([a-fA-F0-9]{6})', style)
        if match_rgb:
            return tuple(map(int, match_rgb.groups()))
        elif match_hex:
            return match_hex.group(0)
    except Exception as e:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, f"Error extrayendo el color: {str(e)}")
    return None

def verificar_errores_de_entrada(url):
    """Verifica que los errores de entrada estén destacados visualmente y acompañados de mensajes claros."""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Verificación de Errores de Entrada")

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Buscar mensajes de error junto a inputs
        error_inputs = driver.find_elements(By.XPATH, "//input[@aria-invalid='true'] | //input[contains(@class, 'error')]")
        error_messages = driver.find_elements(By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert') or contains(@role, 'alert')]")

        total_errors = len(error_inputs)
        total_messages = len(error_messages)

        # Verificar mensajes y colores de fondo
        highlighted_errors = 0
        for input_element in error_inputs:
            style = input_element.get_attribute("style")
            color = extract_color_value(style)
            if color:
                highlighted_errors += 1

        # Resultados
        if total_errors > 0:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- Total de campos con errores detectados: {total_errors}")
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- Total de mensajes de error claros encontrados: {total_messages}")
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- Campos con errores visualmente destacados: {highlighted_errors} de {total_errors}")
            
            if highlighted_errors == total_errors and total_messages >= total_errors:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, "- La página CUMPLE con el criterio de visualización de errores.")
            else:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, "- La página NO CUMPLE con el criterio de visualización de errores.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron errores de entrada en el formulario.")

    except TimeoutException:
        print("- Error: La página tardó demasiado en cargar.")
    except Exception as e:
        print(f"- Error inesperado: {str(e)}")
    finally:
        driver.quit()


def verificar_orden_de_enfoque(url):
    """Verifica que el orden de enfoque sea lógico y secuencial en la página."""

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Verificación de Orden de Enfoque Lógico", ln=True, align='L')

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Obtener todos los elementos con tabindex o foco por defecto
        focusable_elements = driver.find_elements(By.XPATH, "//*[@tabindex or self::a or self::button or self::input or self::textarea]")

        if not focusable_elements:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron elementos con orden de enfoque.")
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página NO CUMPLE con el criterio de enfoque lógico.")
            return

        # Verificar el orden lógico de tabindex
        sequential_tabindex = True
        previous_index = -1
        tab_sequence = []

        for element in focusable_elements:
            tabindex = element.get_attribute("tabindex")
            if tabindex is not None:
                tab_index = int(tabindex)
                tab_sequence.append((element.tag_name, tab_index))
                if tab_index < previous_index:
                    sequential_tabindex = False
                previous_index = tab_index
            else:
                tab_sequence.append((element.tag_name, "default"))

        # Resumen
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, f"- Total de elementos focuseables detectados: {len(focusable_elements)}.")
        if sequential_tabindex:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- El orden de enfoque es lógico y secuencial.")
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página CUMPLE con el criterio de orden de enfoque lógico.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- El orden de enfoque no es lógico.")
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página NO CUMPLE con el criterio de enfoque lógico.")
        
        

    except TimeoutException:
        print("- Error: La página tardó demasiado en cargar.")
    except Exception as e:
        print(f"- Error inesperado: {str(e)}")
    finally:
        driver.quit()

def verificar_alternativas_gestos(url):
    """Verifica si las funciones con gestos complejos tienen alternativas accesibles."""

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Verificación de Alternativas a Gestos Multipunto", ln=True, align='L')


    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Buscar elementos que puedan requerir gestos complejos
        elementos_gestos = driver.find_elements(By.XPATH, "//*[@ondrag or @onpinch or @ontouchmove or @onmousedown]")

        if not elementos_gestos:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron elementos que requieran gestos complejos.")
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página CUMPLE con el criterio de accesibilidad para gestos simplificados.")
            return

        # Verificar alternativas accesibles (tabindex para navegación por teclado)
        elementos_con_alternativa = 0
        for elemento in elementos_gestos:
            tabindex = elemento.get_attribute("tabindex")
            aria_role = elemento.get_attribute("role")
            if tabindex is not None or aria_role in ["button", "link"]:
                elementos_con_alternativa += 1

        total_elementos = len(elementos_gestos)
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, f"- Total de elementos que requieren gestos complejos: {total_elementos}.")
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(0, 6, f"- Total de elementos con alternativas accesibles: {elementos_con_alternativa} de {total_elementos}.")

        if elementos_con_alternativa == total_elementos:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página CUMPLE con el criterio de accesibilidad para gestos complejos.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página NO CUMPLE con el criterio de accesibilidad para gestos complejos.")

    except TimeoutException:
        print("- Error: La página tardó demasiado en cargar.")
    except Exception as e:
        print(f"- Error inesperado: {str(e)}")
    finally:
        driver.quit()

def extract_color_value(style):
    """Extrae valores de color del atributo de estilo en formato RGB o HEX."""
    try:
        match_rgb = re.search(r'rgb\((\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3})\)', style)
        match_hex = re.search(r'#([a-fA-F0-9]{6})', style)
        if match_rgb:
            return tuple(map(int, match_rgb.groups()))
        elif match_hex:
            return match_hex.group(0)
    except Exception as e:
        print(f"Error extrayendo el color: {str(e)}")
    return None

def verificar_errores_de_entrada(url):
    """Verifica que los errores de entrada estén destacados visualmente y acompañados de mensajes claros."""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Verificación de Errores de Entrada", ln=True, align='L')


    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Buscar mensajes de error junto a inputs
        error_inputs = driver.find_elements(By.XPATH, "//input[@aria-invalid='true'] | //input[contains(@class, 'error')]")
        error_messages = driver.find_elements(By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert') or contains(@role, 'alert')]")

        total_errors = len(error_inputs)
        total_messages = len(error_messages)

        # Verificar mensajes y colores de fondo
        highlighted_errors = 0
        for input_element in error_inputs:
            style = input_element.get_attribute("style")
            color = extract_color_value(style)
            if color:
                highlighted_errors += 1

        # Resultados
        if total_errors > 0:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- Total de campos con errores detectados: {total_errors}")
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- Total de mensajes de error claros encontrados: {total_messages}")
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- Campos con errores visualmente destacados: {highlighted_errors} de {total_errors}")
            
            if highlighted_errors == total_errors and total_messages >= total_errors:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, "- La página CUMPLE con el criterio de visualización de errores.")
            else:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, "- La página NO CUMPLE con el criterio de visualización de errores.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron errores de entrada en el formulario.")

    except TimeoutException:
        print(Fore.RED + " Error: La página tardó demasiado en cargar.")
    except Exception as e:
        print(Fore.RED + f" Error inesperado: {str(e)}")
    finally:
        driver.quit()

# Prueba la función con una URL de prueba
# verificar_errores_de_entrada("https://www.mercadolibre.cl")  # Cambia a una URL de prueba
def extract_color_value(style):
    """Extrae valores de color del atributo de estilo en formato RGB o HEX."""
    try:
        match_rgb = re.search(r'rgb\((\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3})\)', style)
        match_hex = re.search(r'#([a-fA-F0-9]{6})', style)
        if match_rgb:
            return tuple(map(int, match_rgb.groups()))
        elif match_hex:
            return match_hex.group(0)
    except Exception as e:
        print(f"Error extrayendo el color: {str(e)}")
    return None

def verificar_errores_de_entrada(url):
    """Verifica que los errores de entrada estén destacados visualmente y acompañados de mensajes claros."""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Verificación de Errores de Entrada", ln=True, align='L')


    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Buscar mensajes de error junto a inputs
        error_inputs = driver.find_elements(By.XPATH, "//input[@aria-invalid='true'] | //input[contains(@class, 'error')]")
        error_messages = driver.find_elements(By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert') or contains(@role, 'alert')]")

        total_errors = len(error_inputs)
        total_messages = len(error_messages)

        # Verificar mensajes y colores de fondo
        highlighted_errors = 0
        for input_element in error_inputs:
            style = input_element.get_attribute("style")
            color = extract_color_value(style)
            if color:
                highlighted_errors += 1

        # Resultados
        if total_errors > 0:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- Total de campos con errores detectados: {total_errors}")
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- Total de mensajes de error claros encontrados: {total_messages}")
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- Campos con errores visualmente destacados: {highlighted_errors} de {total_errors}")
            
            if highlighted_errors == total_errors and total_messages >= total_errors:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, "La página CUMPLE con el criterio de visualización de errores.")
            else:
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(0, 6, "La página NO CUMPLE con el criterio de visualización de errores.")
        else:
            pdf.set_font("Arial", size=8)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "No se encontraron errores de entrada en el formulario.")

    except TimeoutException:
        print(Fore.RED + " Error: La página tardó demasiado en cargar.")
    except Exception as e:
        print(Fore.RED + f" Error inesperado: {str(e)}")
    finally:
        driver.quit()

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

def hdu_dos_dos(url):
    pdf.ln(10)
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(200, 10, txt="Criterio: Retroalimentación de Acciones", ln=True, align='C')

    # Agrega un título
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Mensajes de Confirmación:", ln=True, align='L')

    # Configurar el driver de Selenium en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-position=-2400,-2400")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Crear directorio para capturas de pantalla
    screenshots_dir = "fotosSelenium"
    os.makedirs(screenshots_dir, exist_ok=True)

    # Navegar a la URL
    driver.get(url)

    # --- Criterio 1: Verificar mensajes de confirmación ---
    try:
        mensajes_confirmacion = driver.find_elements(By.CSS_SELECTOR, '.alert, .message, .notification, .success, .error')
        if mensajes_confirmacion:
            for idx, mensaje in enumerate(mensajes_confirmacion, start=1):
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 6, f"- Mensaje de confirmación encontrado: {mensaje.text.strip()}")
                mensaje.screenshot(os.path.join(screenshots_dir, f"mensaje_confirmacion_{idx}.png"))
                print(f"Captura guardada: mensaje_confirmacion_{idx}.png")
        else:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 6, f"- No se encontraron mensajes de confirmación en la página.")

    except Exception as e:
        print(f"Error al verificar mensajes de confirmación: {e}")

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Indicadores de progreso:", ln=True, align='L')
    # --- Criterio 2: Verificar indicadores de proceso ---
    try:
        indicadores_proceso = driver.find_elements(By.CSS_SELECTOR, '.loading, .spinner, .progress, .loader')
        if indicadores_proceso:
            for idx, indicador in enumerate(indicadores_proceso, start=1):
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 6, f"- Indicador de proceso encontrado: {obtener_nombre_elemento(indicador, idx)}")
                indicador.screenshot(os.path.join(screenshots_dir, f"indicador_proceso_{idx}.png"))
                print(f"Captura guardada: indicador_proceso_{idx}.png")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- No se encontraron indicadores de proceso en la página.")
    except Exception as e:
        print(f"Error al verificar indicadores de proceso: {e}")

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Retorno Visual:", ln=True, align='L')

    # --- Criterio 3: Verificar retorno visual inmediato ---
    try:
        clickable_elements = driver.find_elements(By.CSS_SELECTOR, 'button, a')
        for idx, element in enumerate(clickable_elements, start=1):
            nombre_elemento = obtener_nombre_elemento(element, idx)
            if element.is_displayed() and element.is_enabled():
                initial_style = element.get_attribute('style')

                # Captura de pantalla antes de intentar hacer clic
                element.screenshot(os.path.join(screenshots_dir, f"{nombre_elemento}_antes.png"))
                print(f"Captura guardada: {nombre_elemento}_antes.png")

                try:
                    element.click()
                    time.sleep(1)  # Esperar para observar cambios visuales

                    # Captura de pantalla después de hacer clic
                    element.screenshot(os.path.join(screenshots_dir, f"{nombre_elemento}_despues.png"))
                    print(f"Captura guardada: {nombre_elemento}_despues.png")

                    # Intentar reubicar el elemento después del clic para comparar su estilo
                    clickable_elements = driver.find_elements(By.CSS_SELECTOR, 'button, a')
                    element = clickable_elements[idx - 1]  # Reubicar por índice
                    new_style = element.get_attribute('style')

                    if initial_style != new_style:
                        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                        pdf.multi_cell(0, 6, f"- {nombre_elemento} cambió visualmente al hacer clic.")
                    else:
                        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                        pdf.multi_cell(0, 6, f"- Advertencia: {nombre_elemento} no cambió visualmente al hacer clic.")
                except StaleElementReferenceException:
                        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                        pdf.multi_cell(0, 6, f"- El click en el elemento: {nombre_elemento}, provocó un cambio en el DOM (Retorno visual detectado).")
            else:
                        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                        pdf.multi_cell(0, 6, f"- {nombre_elemento} no es clickeable o visible.")
    except Exception as e:
        pass
    
    # Cerrar el driver
    driver.quit()

def hdu_dos_tres(url):
    # Configurar el driver de Selenium en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-position=-2400,-2400")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    pdf.ln(10)
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(200, 10, txt="Criterio: Facilidad de Navegación", ln=True, align='C')

    # Crear directorio para capturas de pantalla
    screenshots_dir = "capturas_navegacion"
    os.makedirs(screenshots_dir, exist_ok=True)

    # Navegar a la URL
    driver.get(url)
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Menús de Navegación:", ln=True, align='L')
    # --- Criterio 1: Verificar menús de navegación claros ---
    try:
        menus = driver.find_elements(By.CSS_SELECTOR, 'nav, .menu, .navbar')
        if menus:
            for idx, menu in enumerate(menus, start=1):
                pdf.set_font("Arial", size=8)  # Establecemos la fuente
                pdf.set_x(15)  # Ajuste de sangría
                pdf.multi_cell(0, 6, f"- Menú de navegación encontrado. Capturando menú {idx}.")
                
                # Guardar la captura de pantalla
                screenshot_path = os.path.join(screenshots_dir, f"menu_navegacion_{idx}.png")
                menu.screenshot(screenshot_path)
                print(f"Captura guardada: menu_navegacion_{idx}.png")
                
                # Añadir la imagen justo debajo del texto
                current_y = pdf.get_y()  # Obtener la posición vertical actual
                pdf.image(screenshot_path, x=15, y=current_y + 2, w=90)  # Ajustar 'w' según el ancho necesario
                
                # Mover la posición vertical del cursor debajo de la imagen para continuar el texto de manera ordenada
                pdf.set_y(current_y + 20)  # Ajusta este valor según el tamaño de la imagen para evitar solapamientos

        else:
            pdf.set_font("Arial", size=8)  # Establecemos la fuente
            pdf.set_x(15)  # Ajuste de sangría
            pdf.multi_cell(0, 6, "- No se encontraron menús de navegación claros.")

    except Exception as e:
        print(f"Error al verificar menús de navegación: {e}")

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Scroll Vertical:", ln=True, align='L')
    # --- Criterio 2: Verificar scroll vertical no excesivo y secciones claras ---
    try:
        body_height = driver.execute_script("return document.body.scrollHeight")
        window_height = driver.execute_script("return window.innerHeight")
        if body_height > window_height * 3:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Advertencia: El scroll vertical es excesivo. Altura del documento: {body_height}px")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Scroll vertical dentro del rango aceptable. Altura del documento: {body_height}px")
        
        pdf.set_font("Arial", "I", size=10)
        pdf.cell(200, 10, txt="Secciones Claramente Separadas:", ln=True, align='L')
        # Verificar que las secciones estén claramente separadas
        secciones = driver.find_elements(By.CSS_SELECTOR, 'section, .content, .main-section')
        if secciones:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Se encontraron {len(secciones)} secciones claramente separadas.")
            for idx, section in enumerate(secciones, start=1):
                section.screenshot(os.path.join(screenshots_dir, f"seccion_{idx}.png"))
                print(f"Captura guardada: seccion_{idx}.png")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- No se encontraron secciones claramente separadas.")
    except Exception as e:
        pass
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Enlaces identificables:", ln=True, align='L')
    # --- Criterio 3: Verificar enlaces identificables ---
    try:
        enlaces = driver.find_elements(By.CSS_SELECTOR, 'a')
        total_enlaces = len(enlaces)
        enlaces_identificables = 0
        
        for enlace in enlaces:
            if enlace.value_of_css_property('text-decoration').find('underline') != -1 or enlace.value_of_css_property('color') != 'initial':
                enlaces_identificables += 1

        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- {enlaces_identificables} de los {total_enlaces} enlaces son fácilmente identificables.")
        if enlaces_identificables < total_enlaces:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Advertencia: {total_enlaces - enlaces_identificables} enlaces no son fácilmente identificables.")
    except Exception as e:
        print(f"Error al verificar enlaces identificables: {e}")


    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Mapa del sitio accesible:", ln=True, align='L')
    # --- Criterio 4: Verificar mapa del sitio accesible ---
    try:
        mapa_sitio = driver.find_element(By.LINK_TEXT, 'Mapa del sitio')
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- Mapa del sitio accesible desde la página.")
        mapa_sitio.screenshot(os.path.join(screenshots_dir, "mapa_sitio.png"))
        print("Captura guardada: mapa_sitio.png")
    except NoSuchElementException:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- No se encontró el enlace al mapa del sitio.")
    except Exception as e:
        pass

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Menús Complejos:", ln=True, align='L')
    # --- Criterio 5: Evitar menús desplegables complejos ---
    try:
        menues_desplegables = driver.find_elements(By.CSS_SELECTOR, 'ul ul, .dropdown-menu, .submenu')
        if menues_desplegables:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Advertencia: Se encontraron {len(menues_desplegables)} menú/s desplegables complejos.")
            for idx, menu in enumerate(menues_desplegables, start=1):
                menu.screenshot(os.path.join(screenshots_dir, f"menu_desplegable_{idx}.png"))
                print(f"Captura guardada: menu_desplegable_{idx}.png")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- No se encontraron menús desplegables complejos.")
    except Exception as e:
        pass

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Navegación Consistente:", ln=True, align='L')
    # --- Criterio 6: Verificar consistencia de estructura de navegación ---
    try:
        enlaces_pagina = driver.find_elements(By.CSS_SELECTOR, 'a')
        driver.refresh()
        enlaces_refrescados = driver.find_elements(By.CSS_SELECTOR, 'a')
        if len(enlaces_pagina) == len(enlaces_refrescados):
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- La estructura de navegación es consistente en todas las páginas.")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Advertencia: La estructura de navegación no es consistente.")
    except Exception as e:
        pass

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Retroalimentación Visual:", ln=True, align='L')
    # --- Criterio 7: Retroalimentación visual al interactuar con elementos de navegación ---
    try:
        botones_enlaces = driver.find_elements(By.CSS_SELECTOR, 'button, a')
        for idx, elemento in enumerate(botones_enlaces, start=1):
            if elemento.is_displayed() and elemento.is_enabled():
                initial_style = elemento.get_attribute('style')
                elemento.click()
                time.sleep(1)
                new_style = elemento.get_attribute('style')
                if initial_style != new_style:
                    pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                    pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                    pdf.multi_cell(0, 6, f"- El elemento de navegación {idx} mostró retroalimentación visual.")
                else:
                    pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                    pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                    pdf.multi_cell(0, 6, f"- Advertencia: El elemento de navegación {idx} no mostró retroalimentación visual.")
    except Exception as e:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- No se encontraron elementos que ameriten retrolimentación visual.")

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Botón de Retroceso:", ln=True, align='L')
    # --- Criterio 8: Verificar botón de retroceso del navegador ---
    try:
        driver.back()
        time.sleep(1)
        if driver.current_url == url:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- El botón de retroceso del navegador funciona correctamente.")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Advertencia: El botón de retroceso del navegador no devolvió a la página esperada.")
    except Exception as e:
        pass

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Ventanas Emergentes o PopUps:", ln=True, align='L')
    # --- Criterio 9: Verificar ausencia de ventanas emergentes o anuncios intrusivos ---
    try:
        popups = driver.find_elements(By.CSS_SELECTOR, '.popup, .modal, .advertisement')
        if popups:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Advertencia: Se encontraron {len(popups)} ventanas emergentes o anuncios intrusivos.")
            for idx, popup in enumerate(popups, start=1):
                popup.screenshot(os.path.join(screenshots_dir, f"popup_{idx}.png"))
                print(f"Captura guardada: popup_{idx}.png")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- No se encontraron ventanas emergentes o anuncios intrusivos.")
    except Exception as e:
        pass

    # Cerrar el driver
    driver.quit()

def rgb_to_hex(rgb_string):
    # Si el color ya está en formato hexadecimal, devolverlo tal cual
    if rgb_string.startswith("#"):
        return rgb_string

    # Extraer valores RGB de la cadena como 'rgb(r, g, b)' o 'rgba(r, g, b, a)'
    rgb_values = re.findall(r'\d+', rgb_string)
    r, g, b = map(int, rgb_values[:3])  # Solo los tres primeros valores

    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def get_font_properties(driver, element):
    # Extraer estilos de fuente y otros atributos
    font_size = element.value_of_css_property('font-size')
    font_family = element.value_of_css_property('font-family')
    line_height = element.value_of_css_property('line-height')
    color = element.value_of_css_property('color')
    background_color = element.value_of_css_property('background-color')
    
    # Convertir colores a hexadecimal
    color_hex = rgb_to_hex(color)
    background_color_hex = rgb_to_hex(background_color)
    
    return {
        'font_size': font_size,
        'font_family': font_family,
        'line_height': line_height,
        'color': color_hex,
        'background_color': background_color_hex
    }

def check_contrast(color1, color2):
    # Convertir hex a RGB
    color1 = [int(color1[i:i+2], 16) for i in (1, 3, 5)]
    color2 = [int(color2[i:i+2], 16) for i in (1, 3, 5)]
    
    # Calcular luminancia
    def luminance(color):
        r, g, b = [x / 255.0 for x in color]
        
        # Aplicar corrección gamma para cada canal de color
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    # Calcular luminancia de ambos colores
    L1 = luminance(color1)
    L2 = luminance(color2)

    # Calcular el ratio de contraste
    contrast_ratio = (max(L1, L2) + 0.05) / (min(L1, L2) + 0.05)
    return contrast_ratio

def is_sans_serif(font_family):
    # Verifica si la fuente es sans-serif
    sans_serif_fonts = ['Arial', 'Verdana', 'Helvetica', 'Tahoma', 'Geneva', 'sans-serif']
    return any(font in font_family for font in sans_serif_fonts)

def hdu_dos_cuatro(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-position=-2400,-2400")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.get(url)
    
    # Encuentra el cuerpo del texto
    text_element = driver.find_element(By.TAG_NAME, 'body')
    
    font_properties = get_font_properties(driver, text_element)
    pdf.ln(10)
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(200, 10, txt="Criterio: Legibilidad del Texto", ln=True, align='C')
    # Agrega un título
    # Verificar tamaño de la fuente
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Tamaño de la Fuente:", ln=True, align='L')
    font_size = float(font_properties['font_size'].replace('px', ''))
    if font_size >= 16:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- Tamaño de la fuente es adecuado: {font_size}px")
    else:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- Tamaño de la fuente es menor a 16px: {font_size}px")

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Tipo de Fuente:", ln=True, align='L')
    # Verificar tipo de fuente
    font_family = font_properties['font_family']
    if is_sans_serif(font_family):
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, "- La fuente es sans-serif: {}".format(font_family))
    else:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, "- La fuente no es sans-serif: {}".format(font_family))
    
    # Verificar contraste
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Contraste:", ln=True, align='L')
    text_color = font_properties['color']
    background_color = font_properties['background_color']
    contrast_ratio = check_contrast(text_color, background_color)
    if contrast_ratio >= 4.5:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, "- Contraste cumple con WCAG AA: {:.2f}".format(contrast_ratio))
    else:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, "- Contraste no cumple con WCAG AA: {:.2f}".format(contrast_ratio))
    
    # Verificar espaciado entre líneas
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Espaciado:", ln=True, align='L')
    line_height = font_properties['line_height']
    if line_height == 'normal':
        line_height = 1.2 * font_size  # Asume 1.2x si es 'normal'
    else:
        line_height = float(line_height.replace('px', ''))
    
    if line_height / font_size >= 1.5:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, "- El espaciado entre líneas es adecuado: {:.2f}".format(line_height / font_size))
    else:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, "- El espaciado entre líneas es insuficiente: {:.2f}".format(line_height / font_size))

    driver.quit()

def ejecutar_con_timeout(func, timeout, *args, **kwargs):
    resultado = [None]

    def func_wrapper():
        resultado[0] = func(*args, **kwargs)

    thread = threading.Thread(target=func_wrapper)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        print(f"La función {func.__name__} no se completó dentro del límite de tiempo de {timeout} segundos.")
        return None
    else:
        return resultado[0]

def hdu_dos_cinco(url):
        # Inicializar Selenium WebDriver
        start_time = time.time()  # Medir el tiempo de inicio
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Ejecutar en modo sin cabeza para que no abra el navegador
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option("prefs", {"profile.default_content_setting_values.cookies": 2})  # Deshabilitar cookies para evitar redireccionamientos
        options.add_argument('--disable-popup-blocking')
        options.add_argument("--window-position=-2400,-2400")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        pdf.ln(10)
        pdf.set_font("Arial", "B", size=14)
        pdf.cell(200, 10, txt="Criterio: Interacción con Elementos Clickables", ln=True, align='C')

        # Crear la carpeta 'capturas' si no existe
        if not os.path.exists('capturasSelenium'):
            os.makedirs('capturasSelenium')
        
        try:
            # Abrir la página web
            driver.get(url)
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))  # Esperar a que se cargue la página
            page_source = driver.page_source

            # Usar BeautifulSoup para analizar el código fuente de la página
            soup = BeautifulSoup(page_source, 'html.parser')

            # Encontrar todos los enlaces y botones en la página
            elementos = soup.find_all(['a', 'button'])
            textos_visitados = set()

            botones_pequenos = []
            espaciado_insuficiente = []
            botones_no_atenuados = []
            sin_cambio_visual = []

            # Filtrar los elementos relevantes antes de iterar
            elementos_filtrados = [el for el in elementos if el.text.strip() and el.name in ['a', 'button']]

            # Verificar cambios visuales en los elementos encontrados
            for idx, elemento in enumerate(elementos_filtrados):
                # Obtener el texto del elemento
                texto_elemento = elemento.text.strip()

                # Saltar elementos con texto duplicado
                if texto_elemento in textos_visitados:
                    continue
                textos_visitados.add(texto_elemento)

                # Encontrar el elemento en Selenium por el texto
                try:
                    if elemento.name == 'a':
                        selenium_elemento = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.LINK_TEXT, texto_elemento))
                        )
                    elif elemento.name == 'button':
                        selenium_elemento = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, f"//button[contains(text(), '{texto_elemento}')]"))
                        )
                    else:
                        continue
                except:
                    # Si no se puede encontrar el elemento, continuar con el siguiente
                    continue

                # Verificar si el elemento es visible
                if not selenium_elemento.is_displayed():
                    continue

                # Crear una lista de tareas para procesar en paralelo
                tasks = [
                    (verificar_tamaño_elemento, selenium_elemento, texto_elemento),
                    (verificar_espaciado_elementos, driver, selenium_elemento, texto_elemento),
                    (verificar_boton_desactivado, driver, selenium_elemento, texto_elemento),
                    (verificar_cambio_visual, driver, selenium_elemento, texto_elemento, idx)
                ]

                # Procesar cada tarea secuencialmente y almacenar el resultado
                for task in tasks:
                    func = task[0]
                    args = task[1:]
                    result = func(*args)
                    if result:
                        if func == verificar_tamaño_elemento:
                            botones_pequenos.append(result)
                        elif func == verificar_espaciado_elementos:
                            espaciado_insuficiente.append(result)
                        elif func == verificar_boton_desactivado:
                            botones_no_atenuados.append(result)
                        elif func == verificar_cambio_visual:
                            sin_cambio_visual.append(result)

            # Imprimir resultados en orden
            imprimir_resultados(botones_pequenos, espaciado_insuficiente, botones_no_atenuados, sin_cambio_visual)

        finally:
            # Cerrar el navegador
            driver.quit()
            end_time = time.time()  # Medir el tiempo de finalización
            elapsed_time = (end_time - start_time)/60
            print(f"Tiempo total de ejecución: {elapsed_time:.2f} minutos")


def verificar_tamaño_elemento(selenium_elemento, texto_elemento):
    # Verificar si el tamaño del elemento es válido (no debe ser 0 de ancho o alto)
    tamaño = selenium_elemento.size
    if tamaño['width'] == 0 or tamaño['height'] == 0:
        return None

    # Verificar si el botón cumple con el tamaño mínimo de 44x44 píxeles
    if tamaño['width'] < 44 or tamaño['height'] < 44:
        return f"El botón con texto '{texto_elemento}' no cumple con el tamaño mínimo de 44x44 píxeles. Tamaño actual: {tamaño['width']}x{tamaño['height']}"
    return None


def verificar_espaciado_elementos(driver, selenium_elemento, texto_elemento):
    # Verificar el espaciado mínimo entre elementos clickeables (mínimo de 8 píxeles)
    try:
        location = selenium_elemento.location
        otros_elementos = driver.find_elements(By.XPATH, "//*[self::a or self::button]")
        for otro_elemento in otros_elementos:
            if otro_elemento == selenium_elemento:
                continue
            try:
                location_otro = otro_elemento.location
                distancia_horizontal = abs(location['x'] - location_otro['x'])
                distancia_vertical = abs(location['y'] - location_otro['y'])
                if distancia_horizontal < 8 and distancia_vertical < 8:
                    return f"El elemento con texto '{texto_elemento}' no cumple con el espaciado mínimo de 8 píxeles con respecto a otros elementos clickeables."
            except:
                # Ignorar errores de obtención de propiedades de otros elementos
                continue
    except:
        # Ignorar errores de verificación del espaciado
        pass
    return None


def verificar_boton_desactivado(driver, selenium_elemento, texto_elemento):
    try:
        # Comparar el estilo del botón desactivado con un botón activo
        color_fondo_desactivado = selenium_elemento.value_of_css_property('background-color')

        # Encontrar un botón similar que no esté desactivado
        botones_activados = driver.find_elements(By.XPATH, "//button[not(@disabled)]")
        for boton_activo in botones_activados:
            if boton_activo.text.strip() != "":
                color_fondo_activo = boton_activo.value_of_css_property('background-color')
                break
        else:
            color_fondo_activo = None

        # Comparar el contraste de color (simplificado para RGB)
        if color_fondo_activo and color_fondo_desactivado:
            color_activo = [int(x) for x in color_fondo_activo.strip('rgba()').split(',')[:3]]
            color_desactivado = [int(x) for x in color_fondo_desactivado.strip('rgba()').split(',')[:3]]
            diferencia_contraste = np.mean(np.abs(np.array(color_activo) - np.array(color_desactivado)))
            porcentaje_atenuacion = (1 - (diferencia_contraste / 255)) * 100
            if porcentaje_atenuacion < 50:  # Ajustar el umbral según sea necesario
                return f"El botón con texto '{texto_elemento}' no está suficientemente atenuado. Diferencia de contraste: {diferencia_contraste:.2f}, Porcentaje de atenuación: {porcentaje_atenuacion:.2f}%"
    except:
        # Ignorar errores al verificar el contraste del botón desactivado
        pass
    return None


def verificar_cambio_visual(driver, selenium_elemento, texto_elemento, idx):
    try:
        # Desplazar el elemento a la vista
        driver.execute_script("arguments[0].scrollIntoView(true);", selenium_elemento)
        WebDriverWait(driver, 5).until(EC.visibility_of(selenium_elemento))  # Esperar a que el elemento esté visible

        # Tomar una captura de pantalla del elemento antes del clic
        area_antes = selenium_elemento.screenshot_as_png

        # Mantener el clic sobre el elemento para provocar un posible cambio visual sin redireccionar
        action = ActionChains(driver)
        action.click_and_hold(selenium_elemento).perform()
        WebDriverWait(driver, 1).until(EC.visibility_of(selenium_elemento))  # Esperar un momento para que el cambio visual tenga lugar

        # Tomar una captura de pantalla del elemento mientras se mantiene el clic
        area_despues = selenium_elemento.screenshot_as_png

        # Liberar el clic
        action.release().perform()

        # Comparar las dos imágenes para detectar cambios visuales
        img_antes = Image.open(BytesIO(area_antes))
        img_despues = Image.open(BytesIO(area_despues))

        # Verificar si las imágenes tienen el mismo tamaño
        if img_antes.size != img_despues.size:
            img_despues = img_despues.resize(img_antes.size, Image.LANCZOS)

        # Calcular la diferencia
        diferencia = np.mean(np.abs(np.array(img_antes) - np.array(img_despues)))
        umbral_cambio = 20  # Ajustar el umbral según sea necesario

        if diferencia <= umbral_cambio:
            # Guardar las capturas de aquellos elementos que no cumplen la condición
            with open(f'capturasSelenium/elemento_{idx}_antes.png', 'wb') as file:
                file.write(area_antes)
            with open(f'capturasSelenium/elemento_{idx}_despues.png', 'wb') as file:
                file.write(area_despues)
            return f"El elemento con texto '{texto_elemento}' no tiene un cambio visual perceptible después del clic."
    except:
        # Ignorar errores al comparar las imágenes
        pass
    return None


def imprimir_resultados(botones_pequenos, espaciado_insuficiente, botones_no_atenuados, sin_cambio_visual):
    print("\nResultados de la verificación:")

    print("\nBotones que no cumplen con el tamaño mínimo de 44x44 píxeles:")
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Tamaño Elementos:", ln=True, align='L')
    for mensaje in botones_pequenos:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"-{mensaje}")

    print("\nElementos con espaciado insuficiente:")
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Espaciado Entre Elementos:", ln=True, align='L')
    for mensaje in espaciado_insuficiente:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"-{mensaje}")


    print("\nBotones desactivados que no están suficientemente atenuados:")
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Contraste:", ln=True, align='L')
    for mensaje in botones_no_atenuados:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"-{mensaje}")


    print("\nElementos que no tienen un cambio visual perceptible después del clic:")
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Cambio Visual:", ln=True, align='L')
    for mensaje in sin_cambio_visual:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"-{mensaje}")



# Configuración para Chrome en modo headless
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-position=-2400,-2400")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# Función principal para analizar la usabilidad
def hdu_dos_seis(url):
    driver = setup_driver()
    pdf.ln(10)
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(200, 10, txt="Criterio: Carga Cognitiva y Organización Visual", ln=True, align='C')
    # Navegar a la URL
    driver.get(url)
    pdf.ln(10)
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(200, 10, txt="Carga Cognitiva y Organización Visual", ln=True, align='C')
    # Esperar a que la página se cargue completamente
    time.sleep(3)
    # Agrega un título
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Encabezados:", ln=True, align='L')

    # Criterio 1: Verificar encabezados H1, H2, H3
    try:
        h1_elements = driver.find_elements(By.TAG_NAME, "h1")
        h2_elements = driver.find_elements(By.TAG_NAME, "h2")
        h3_elements = driver.find_elements(By.TAG_NAME, "h3")
        
        if h1_elements:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Se encontraron {len(h1_elements)} encabezados H1.")
        if h2_elements:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Se encontraron {len(h2_elements)} encabezados H2.")
        if h3_elements:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Se encontraron {len(h3_elements)} encabezados H3.")

    except Exception as e:
        print(f"Error en la verificación de encabezados: {str(e)}")

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Paleta de Colores:", ln=True, align='L')
    # Criterio 2: Verificación de la paleta de colores limitada
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body_color = body.value_of_css_property("background-color")
        body_rgb = get_rgb_from_color_string(body_color)
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- Color de fondo del cuerpo: {body_rgb}")
    except Exception as e:
        print(f"Error al analizar la paleta de colores: {str(e)}")


    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Animaciones y Elementos en Movimiento:", ln=True, align='L')
    # Criterio 3: Verificación de animaciones y elementos en movimiento
    try:
        animated_elements = driver.find_elements(By.CSS_SELECTOR, "*[style*='animation']")
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- Se encontraron {len(animated_elements)} elementos con animación.")
    except Exception as e:
        print(f"Error al analizar animaciones: {str(e)}")

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Tamaño de Títulos:", ln=True, align='L')
    # Criterio 4: Verificación del tamaño de los títulos
    try:
        for h1 in h1_elements:
            font_size = float(h1.value_of_css_property("font-size").replace("px", ""))
            if font_size < 24:
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 6, f"- Advertencia: El tamaño de la fuente H1 ('{h1.text}') es menor a 24px: {font_size}px")
        for h2 in h2_elements:
            font_size = float(h2.value_of_css_property("font-size").replace("px", ""))
            if not (18 <= font_size <= 22):
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 6, f"- Advertencia: El tamaño de la fuente H2 ('{h2.text}') está fuera del rango de 18-22px: {font_size}px")
        for h3 in h3_elements:
            font_size = float(h3.value_of_css_property("font-size").replace("px", ""))
            if not (18 <= font_size <= 22):
                pdf.set_font("Arial", size=8) # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                pdf.multi_cell(0, 6, f"- Advertencia: El tamaño de la fuente H3 ('{h3.text}') está fuera del rango de 18-22px: {font_size}px")
    except Exception as e:
        print(f"Error en la verificación de tamaño de títulos: {str(e)}")

    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Opciones Interactivas:", ln=True, align='L')
    # Criterio 5: Verificación de opciones interactivas
    try:
        interactive_elements = driver.find_elements(By.CSS_SELECTOR, "a, button, input[type='submit'], input[type='button']")
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- Se encontraron {len(interactive_elements)} elementos interactivos.")
    except Exception as e:
        pdf.set_font("Arial", size=8) # Añadimos un salto de línea
        pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
        pdf.multi_cell(0, 6, f"- Error en la verificación de opciones interactivas: {str(e)}")

    # Cerrar el driver al final
    driver.quit()

# Utilidad para convertir color en formato rgba/rgb a tupla de enteros
def get_rgb_from_color_string(color_string):
    rgb_match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', color_string)
    if rgb_match:
        return tuple(map(int, rgb_match.groups()))
    else:
        return None

# Función para verificar iconos de ayuda visibles
def verificar_iconos_ayuda(driver):
    try:
        help_icons = driver.find_elements(By.XPATH, "//a[contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'help') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ayuda') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'support') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'faq') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'assist') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'hilfe') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ajuda') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'assistance')] | //a[contains(@aria-label, 'help') or contains(@aria-label, 'ayuda') or contains(@aria-label, 'support') or contains(@aria-label, 'faq') or contains(@aria-label, 'assist') or contains(@aria-label, 'hilfe') or contains(@aria-label, 'ajuda') or contains(@aria-label, 'assistance')] | //a[contains(@title, 'help') or contains(@title, 'ayuda') or contains(@title, 'support') or contains(@title, 'faq') or contains(@title, 'assist') or contains(@title, 'hilfe') or contains(@title, 'ajuda') or contains(@title, 'assistance')] | //*[@class='help-icon' or contains(@class, 'tooltip')]")
        if help_icons:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Se encontraron {len(help_icons)} iconos de ayuda visibles.")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- No se encontraron iconos de ayuda visibles.")
    except Exception as e:
        print(f"Error en la verificación de iconos de ayuda: {str(e)}")

# Función para verificar lenguaje sencillo en la ayuda
def verificar_lenguaje_sencillo(driver):
    try:
        help_texts = driver.find_elements(By.XPATH, "//*[contains(@class, 'help-text') or contains(@class, 'tooltip') or @role='tooltip' or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'help') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ayuda') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'support') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'faq') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'assist') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'hilfe') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ajuda') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'assistance')]")
        
        for help_text in help_texts:
            # Limpiar el texto de saltos de línea y espacios innecesarios
            text = help_text.text.replace('\n', ' ').strip().lower()
            
            if text and any(word in text for word in ["complejo", "difícil", "técnico", "complicado", "schwierig", "tecnológico"]):
                pdf.set_font("Arial", size=8)  # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                help_text_clean = help_text.text.replace('\n', ' ').strip()
                pdf.multi_cell(0, 6, f"- Advertencia: El texto de ayuda contiene lenguaje complejo: ' {help_text_clean}'")
            elif text:
                pdf.set_font("Arial", size=8)  # Añadimos un salto de línea
                pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
                help_text_clean = help_text.text.replace('\n', ' ').strip()
                pdf.multi_cell(0, 6, f"- Texto de ayuda verificado: '{help_text_clean}'")
    
    except Exception as e:
        print(f"Error en la verificación del lenguaje de la ayuda: {str(e)}")

# Función para verificar acceso a tutoriales o videos explicativos
def verificar_acceso_tutoriales(driver):
    try:
        tutorial_links = driver.find_elements(By.XPATH, "//a[contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'tutorial') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'video') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'guide') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'guia') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'how-to') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'anleitung') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'instrucao') or contains(translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'explicativo')]")
        if tutorial_links:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- Se encontraron {len(tutorial_links)} enlaces a tutoriales o videos explicativos.")
        else:
            pdf.set_font("Arial", size=8) # Añadimos un salto de línea
            pdf.set_x(15)  # Aquí es donde se establece la sangría (20 puntos hacia la derecha)
            pdf.multi_cell(0, 6, f"- No se encontraron enlaces a tutoriales o videos explicativos.")
    except Exception as e:
        print(f"Error en la verificación de tutoriales o videos explicativos: {str(e)}")

# Función principal para ejecutar las verificaciones
def hdu_dos_siete(url):
    driver = setup_driver()

    # Navegar a la URL
    driver.get(url)
    pdf.ln(10)
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(200, 10, txt="Criterio: Ayuda Contextual", ln=True, align='C')
    # Esperar a que la página se cargue completamente
    time.sleep(3)

    # Verificar los diferentes criterios
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Iconos de Ayuda:", ln=True, align='L')
    verificar_iconos_ayuda(driver)
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Lenguaje Sencillo:", ln=True, align='L')
    verificar_lenguaje_sencillo(driver)
    pdf.set_font("Arial", "I", size=10)
    pdf.cell(200, 10, txt="Acceso a Tutoriales:", ln=True, align='L')
    verificar_acceso_tutoriales(driver)

    # Cerrar el driver al final
    driver.quit()

for categoria in categorias:
    if categoria == "Retroalimentacion de Acciones":
        hdu_dos_dos(url)
    elif categoria == "Facilidad de Navegacion":
        hdu_dos_tres(url)
    elif categoria ==  "Legibilidad del Texto":
        hdu_dos_cuatro(url)
    elif categoria ==   "Interaccion con Elementos Clickables":
        hdu_dos_cinco(url)
    elif categoria ==  "Cognitiva y Organizacion Visual":
        hdu_dos_seis(url)
    elif categoria ==   "Ayuda Contextual":
        hdu_dos_siete(url)
    elif categoria == "Página de Inicio":
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

    elif categoria == "Validación de Accesibilidad Visual":
        verificar_accesibilidad_teclado(url)
        verificar_accesibilidad_errores(url)    
        verificar_contraste_accesibilidad(url)
        verificar_indicador_ubicacion(url)
        verificar_claridad_enlaces(url)
        verificar_visibilidad_enfoque(url)
        verificar_categorias_visibles(url)
        verificar_contraste_hipertextos(url)
        medir_espacio_blanco(url)
        verificar_posicion_caja_busqueda(url)   
        verificar_estructura_contenido(url)
    elif categoria == "Validación de Accesibilidad Cognitiva":
        check_ui_flow(url)
        check_feedback(url)
        check_error_messages(url)
        hdu_cuatro(url)
        verificar_autenticacion_facil(url)
        crawl_site(url)
        perform_search(url)
        check_navigation_feedback(url)
        verificar_enlaces_coherencia_titulo(url)
        verificar_enlaces_genericos(url)
    elif categoria == "Validación de Accesibilidad Motora":
        validate_input_targets(url)
        detect_blinking_content(url)
        verificar_pestanas_navegacion(url)
        verificar_errores_de_entrada(url)
        verificar_orden_de_enfoque(url)
        verificar_alternativas_gestos(url)  

# Ejemplo de uso
#hdu_dos_dos('https://www.mercadolibre.cl')
#hdu_dos_tres('https://www.mercadolibre.cl')
#hdu_dos_cuatro('https://www.mercadolibre.cl')
#hdu_dos_cinco('https://www.gov.uk/')
#hdu_dos_seis('https://www.mercadolibre.cl') 
#hdu_dos_siete('https://www.mercadolibre.cl')

# Añadir la portada del documento

# Inicializa Firebase
cred = credentials.Certificate('src\components\config\iatu-pmv-firebase-adminsdk-my9kl-4321b8a185.json')
initialize_app(cred, {'storageBucket': 'iatu-pmv.appspot.com'})

# Usar BytesIO para guardar el PDF en memoria
pdf_stream = BytesIO()
# Guardar el contenido del PDF en el flujo de bytes usando el parámetro dest='S'
pdf_output = pdf.output(dest='S').encode('latin1', 'replace')  # En FPDF, el formato de salida es string, lo convertimos a bytes
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


shutil.rmtree('capturas')
shutil.rmtree('output_evaluated_images')
# shutil.rmtree('capturas_navegacion')
# shutil.rmtree('capturasSelenium')
# shutil.rmtree('fotosSelenium')
# shutil.rmtree('output_cingoz')
# shutil.rmtree('output_icon')
# shutil.rmtree('output_pb')
# shutil.rmtree('output_images')
