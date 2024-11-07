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

CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com/",
    api_key="bUyMUjRY0TGSKrbNpksy"
)

def draw_bounding_boxes(frame, predictions):
    """
    Dibuja las bounding boxes sobre el fotograma basado en las predicciones.

    :param frame: El fotograma sobre el cual se dibujarán las bounding boxes.
    :param predictions: Lista de predicciones del modelo YOLO.
    :return: El fotograma con las bounding boxes dibujadas.
    """
    for prediction in predictions:
        x0 = int(prediction['x'] - prediction['width'] / 2)
        y0 = int(prediction['y'] - prediction['height'] / 2)
        x1 = int(prediction['x'] + prediction['width'] / 2)
        y1 = int(prediction['y'] + prediction['height'] / 2)

        # Dibujar la bounding box
        cv2.rectangle(frame, (x0, y0), (x1, y1), (0, 255, 0), 2)

        # Agregar el label y la confianza sobre la bounding box
        label = f"{prediction['class']} ({prediction['confidence']:.2f})"
        cv2.putText(frame, label, (x0, y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return frame


def are_images_similar(image1, image2, threshold=0.9):
    """
    Compara dos imágenes utilizando SSIM (Structural Similarity Index).
    Retorna True si las imágenes son similares por encima del umbral dado.
    """
    # Convertir las imágenes a escala de grises
    gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray_image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    # Redimensionar imágenes si tienen diferentes tamaños
    if gray_image1.shape != gray_image2.shape:
        gray_image2 = cv2.resize(gray_image2, (gray_image1.shape[1], gray_image1.shape[0]))

    # Calcular el SSIM entre las dos imágenes
    score, _ = ssim(gray_image1, gray_image2, full=True)
    return score >= threshold

def progressBarDetect(image_dir, output_dir, model_id, class_of_interest, similarity_threshold=0.9):
    # Crear el directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)

    progressBar_flag = False
    progressbar_count = 1  # Contador para los nombres de las bounding boxes guardadas
    saved_images = []  # Lista para guardar las imágenes únicas (bounding boxes)

    # Recorrer todas las imágenes en el directorio
    for image_filename in os.listdir(image_dir):
        if image_filename.endswith(('.jpg', '.jpeg', '.png')):  # Filtrar solo las imágenes
            image_path = os.path.join(image_dir, image_filename)

            # Cargar la imagen con OpenCV
            frame = cv2.imread(image_path)

            # Realizar la inferencia en la imagen actual
            result = CLIENT.infer(image_path, model_id=model_id)

            # Filtrar las predicciones para mantener solo la clase de interés
            filtered_results = [
                pred for pred in result['predictions']
                if pred['class'] == class_of_interest
            ]

            # Si se detectó la clase 'ProgressBar', guardar las bounding boxes
            if filtered_results:
                progressBar_flag = True
                for i, prediction in enumerate(filtered_results):
                    # Extraer las coordenadas de la bounding box
                    x0 = int(prediction['x'] - prediction['width'] / 2)
                    y0 = int(prediction['y'] - prediction['height'] / 2)
                    x1 = int(prediction['x'] + prediction['width'] / 2)
                    y1 = int(prediction['y'] + prediction['height'] / 2)

                    # Recortar la región de la bounding box para guardarla como una imagen separada
                    cropped_image = frame[y0:y1, x0:x1]

                    # Comparar la imagen recortada con las imágenes ya guardadas
                    similar_found = False
                    for saved_image in saved_images:
                        if are_images_similar(cropped_image, saved_image, threshold=similarity_threshold):
                            similar_found = True
                            break

                    # Si no se encontró una imagen similar, guardarla
                    if not similar_found:
                        output_image_name = f"progressBar_{progressbar_count}_{i + 1}.jpg"
                        output_image_path = os.path.join(output_dir, output_image_name)

                        # Guardar la imagen recortada
                        cv2.imwrite(output_image_path, cropped_image)
                        print(f"Bounding box guardada: {output_image_path}")

                        # Añadir la imagen a la lista de imágenes guardadas
                        saved_images.append(cropped_image)

                progressbar_count += 1  # Incrementar el contador para el siguiente conjunto de bounding boxes

    print("Proceso de detección de bounding boxes completado.")
    return progressBar_flag

def cingozDetect(image_dir, output_dir, model_id, excluded_class, similarity_threshold=0.9):
    # Crear el directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)

    saved_images_by_class = {}  # Diccionario para guardar las imágenes únicas por clase
    c = 0
    # Recorrer todas las imágenes en el directorio
    for image_filename in os.listdir(image_dir):
        if image_filename.endswith(('.jpg', '.jpeg', '.png')):  # Filtrar solo las imágenes
            image_path = os.path.join(image_dir, image_filename)

            # Cargar la imagen con OpenCV
            frame = cv2.imread(image_path)

            # Realizar la inferencia en la imagen actual
            result = CLIENT.infer(image_path, model_id=model_id)

            # Filtrar las predicciones para excluir la clase 'icon'
            filtered_results = [
                pred for pred in result['predictions']
                if pred['class'] != excluded_class
            ]

            # Procesar y guardar las bounding boxes para cada clase detectada
            for prediction in filtered_results:
                class_name = prediction['class']

                # Crear un subdirectorio para la clase si no existe
                class_output_dir = os.path.join(output_dir, class_name)
                os.makedirs(class_output_dir, exist_ok=True)

                # Extraer las coordenadas de la bounding box
                x0 = int(prediction['x'] - prediction['width'] / 2)
                y0 = int(prediction['y'] - prediction['height'] / 2)
                x1 = int(prediction['x'] + prediction['width'] / 2)
                y1 = int(prediction['y'] + prediction['height'] / 2)

                # Recortar la región de la bounding box para guardarla como una imagen separada
                cropped_image = frame[y0:y1, x0:x1]

                # Verificar si la clase ya tiene imágenes guardadas
                if class_name not in saved_images_by_class:
                    saved_images_by_class[class_name] = []

                # Comparar la imagen recortada con las imágenes ya guardadas para esa clase
                similar_found = False
                for saved_image in saved_images_by_class[class_name]:
                    if are_images_similar(cropped_image, saved_image, threshold=similarity_threshold):
                        similar_found = True
                        c += 1
                        break

                # Si no se encontró una imagen similar, guardarla
                if not similar_found:
                    output_image_name = f"{class_name}_{os.path.splitext(image_filename)[0]}.jpg"
                    output_image_path = os.path.join(class_output_dir, output_image_name)

                    # Guardar la imagen recortada
                    cv2.imwrite(output_image_path, cropped_image)
                    print(f"Bounding box de clase '{class_name}' guardada en: {output_image_path}")

                    # Añadir la imagen a la lista de imágenes guardadas para esa clase
                    saved_images_by_class[class_name].append(cropped_image)
    print(f"Se encontraron {c} imagenes similares")
    print("Proceso de detección de bounding boxes completado.")

def appIconDetect(image_dir, output_dir, model_id):
    """
    Detecta todas las clases en las imágenes de un directorio, crea un directorio por clase y guarda las imágenes con
    las bounding boxes correspondientes a cada clase.

    :param image_dir: Directorio que contiene las imágenes a analizar.
    :param output_dir: Directorio base donde se guardarán las imágenes separadas por clase.
    :param model_id: ID del modelo de Roboflow a usar.
    """
    # Crear el directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    saved_frame_count = 1  # Contador para los nombres de las imágenes guardadas

    # Recorrer todas las imágenes en el directorio
    for image_filename in os.listdir(image_dir):
        if image_filename.endswith(('.jpg', '.jpeg', '.png')):  # Filtrar solo las imágenes
            image_path = os.path.join(image_dir, image_filename)

            # Cargar la imagen con OpenCV
            frame = cv2.imread(image_path)

            # Realizar la inferencia en la imagen actual
            result = CLIENT.infer(image_path, model_id=model_id)

            # Obtener las predicciones (todas las clases)
            predictions = result['predictions']

            # Procesar las predicciones para cada clase detectada
            class_bboxes = {}
            for prediction in predictions:
                class_name = prediction['class']
                if class_name not in class_bboxes:
                    class_bboxes[class_name] = []
                class_bboxes[class_name].append(prediction)

            # Crear una imagen por cada clase con sus bounding boxes
            for class_name, class_predictions in class_bboxes.items():
                # Crear un subdirectorio para la clase si no existe
                class_output_dir = os.path.join(output_dir, class_name)
                os.makedirs(class_output_dir, exist_ok=True)

                # Dibujar las bounding boxes solo para esta clase
                frame_copy = frame.copy()
                frame_with_boxes = draw_bounding_boxes(frame_copy, class_predictions)

                # Guardar la imagen con las bounding boxes de esta clase
                output_image_path = os.path.join(class_output_dir, f"{class_name}_{saved_frame_count}.jpg")
                cv2.imwrite(output_image_path, frame_with_boxes)
                print(f"Imagen guardada con bounding boxes de clase '{class_name}' en: {output_image_path}")

            saved_frame_count += 1  # Incrementar el contador para la siguiente imagen

    print("Proceso de detección y guardado de bounding boxes por clase completado.")

model_id = "progressbar-iptbc/6"  # Reemplaza con el ID de tu modelo de Roboflow
class_of_interest = "ProgressBar"  # Clase que deseas detectar


image_dir = "capturas"  # Reemplaza con la ruta de tu video
output_dir = "output_pb"
os.makedirs(output_dir, exist_ok=True)
progressBar_flag = progressBarDetect(image_dir, output_dir, model_id, class_of_interest)
if progressBar_flag:
    print("ProgressBar detectado en el video.")
else:
    print("ProgressBar no detectado en el video.")



model_id = "cingoz8/1"  # Reemplaza con el ID de tu modelo de Roboflow
excluded_class = "icon"  # Clase que deseas detectar


image_dir = "capturas"  # Reemplaza con la ruta de tu video
output_dir = "output_cingoz"
os.makedirs(output_dir, exist_ok=True)
cingozDetect(image_dir, output_dir, model_id, excluded_class)


model_id = "app-icon/45"  # Reemplaza con el ID de tu modelo de Roboflow


video_path = "capturas"  # Reemplaza con la ruta de tu video
output_dir = "output_icon"
os.makedirs(output_dir, exist_ok=True)
appIconDetect(image_dir, output_dir, model_id) 


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

# Crea un objeto PDF
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
title = "Revisión de Criterios Usabilidad Web"
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

# Agrega una página
pdf.add_page()

# Establece la fuente (tipografía y tamaño)
pdf.set_font("Arial", size=14)# Crea un objeto PDF
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

# Agrega una página
pdf.add_page()

# Establece la fuente (tipografía y tamaño)
pdf.set_font("Arial", size=14)
pdf.ln(10)
pdf.set_font("Arial", "B", size=14)
pdf.cell(200, 10, txt="Criterio: Validación de Accesibilidad Visual", ln=True, align='C')
def verificar_accesibilidad_lectores_pantalla(url):
    # Agrega un título
    pdf.set_font("Arial", "I", size=10)
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

def verificar_accesibilidad_teclado(url):
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
    pdf.cell(200, 10, txt="Validación de Mensajes de Error Claros y Directivos", ln=True, align='L')

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
                pdf.set_x(15)
                pdf.multi_cell(0, 6, f"   - {msg.text.strip()}")
        else:
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron mensajes de error en la UI.")

        # Verificar instrucciones claras para corregir el error
        if instructions:
            pdf.set_x(15)
            pdf.multi_cell(0, 6, f"- {len(instructions)} instrucciones para corregir errores encontradas:")
            for instr in instructions:
                pdf.set_x(15)
                pdf.multi_cell(0, 6, f"   - {instr.text.strip()}")
        else:
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- No se encontraron instrucciones claras para corregir errores.")

        # Comprobación final
        if error_messages and instructions:
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página CUMPLE con el criterio de mensajes de error claros y directivos.")
        else:
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- La página NO CUMPLE con el criterio de mensajes de error claros y directivos.")

    except TimeoutException:
        pdf.set_x(15)
        pdf.multi_cell(0, 6, "- La página tardó demasiado en cargar o no contiene elementos esperados.")
    except Exception as e:
        pdf.set_x(15)
        pdf.multi_cell(0, 6, f"- Error inesperado: {str(e)}")
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
    pdf.cell(200, 10, txt="Verificación de Métodos de Autenticación en la UI", ln=True, align='C')

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
            pdf.multi_cell(200, 10, txt=f"- Formulario de autenticación común encontrado (Formulario #{form_index}).")
            
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
                    pdf.multi_cell(200, 10, txt=f"  - Método de autenticación alternativa encontrado: {alternativa.capitalize()}")

            # Verificar si el formulario tiene captcha complejo (indicador de autenticación difícil)
            if any('captcha' in elem.get_attribute('class').lower() for elem in form.find_elements(By.XPATH, ".//*[contains(@class, 'captcha')]")):
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200, 10, txt="  - Advertencia: Se encontró un CAPTCHA, podría dificultar la autenticación.")

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
                pdf.multi_cell(200, 10, txt=f"  - Métodos de autenticación alternativa disponibles: {', '.join(autenticacion_alternativas)}")

    # Si no se encontraron alternativas a pruebas cognitivas difíciles
    if not autenticacion_alternativa_encontrada:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200, 10, txt="- Advertencia: No se encontraron métodos de autenticación alternativos que no dependan de la función cognitiva.")

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
    pdf.cell(200, 10, txt="Verificación de Métodos de Autenticación en la UI", ln=True, align='C')

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
            pdf.multi_cell(200, 10, txt=f"- Formulario de autenticación común encontrado (Formulario #{form_index}).")
            
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
                    pdf.multi_cell(200, 10, txt=f"  - Método de autenticación alternativa encontrado: {alternativa.capitalize()}")

            # Verificar si el formulario tiene captcha complejo (indicador de autenticación difícil)
            if any('captcha' in elem.get_attribute('class').lower() for elem in form.find_elements(By.XPATH, ".//*[contains(@class, 'captcha')]")):
                pdf.set_font("Arial", size=8)
                pdf.set_x(15)
                pdf.multi_cell(200, 10, txt="  - Advertencia: Se encontró un CAPTCHA, podría dificultar la autenticación.")

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
                pdf.multi_cell(200, 10, txt=f"  - Métodos de autenticación alternativa disponibles: {', '.join(autenticacion_alternativas)}")

    # Si no se encontraron alternativas a pruebas cognitivas difíciles
    if not autenticacion_alternativa_encontrada:
        pdf.set_font("Arial", size=8)
        pdf.set_x(15)
        pdf.multi_cell(200, 10, txt="- Advertencia: No se encontraron métodos de autenticación alternativos que no dependan de la función cognitiva.")

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
    
for categoria in categorias:
    if categoria == "Validación de Accesibilidad Visual":
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

# Ejemplo de uso
#hdu_dos_dos('https://www.mercadolibre.cl')
#hdu_dos_tres('https://www.mercadolibre.cl')
#hdu_dos_cuatro('https://www.mercadolibre.cl')
#hdu_dos_cinco('https://www.gov.uk/')
#hdu_dos_seis('https://www.mercadolibre.cl') 
#hdu_dos_siete('https://www.mercadolibre.cl')

# Añadir la portada del documento

# Parte 1: Añadir las imágenes de las clases 'icon' e 'image'
output_icon_dir = "output_icon"  # Directorio con las imágenes de Icon e Image
for class_dir in ['icon', 'image']:
    class_path = os.path.join(output_icon_dir, class_dir)

    if os.path.isdir(class_path):
        class_images = [img for img in os.listdir(class_path) if img.endswith(('.jpg', '.jpeg', '.png'))]

        if class_images:
            # Añadir una nueva página para cada clase y su conteo
            pdf.add_page()
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"Capturas con los elementos '{class_dir}' destacados", ln=True)
            pdf.ln(10)

            # Añadir las imágenes (máximo 2 por página)
            image_counter = 0
            for i, image_file in enumerate(class_images, 1):
                if image_counter == 2:
                    # Añadir nueva página si alcanzamos el límite de 2 imágenes
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 12)
                    pdf.cell(0, 10, f"Capturas con los elementos '{class_dir}' destacados (continuación)", ln=True)
                    pdf.ln(10)
                    image_counter = 0

                # Añadir la imagen de la clase
                image_path = os.path.join(class_path, image_file)
                try:
                    with Image.open(image_path) as img:
                        original_image_width, original_image_height = img.size

                    # Calcular las dimensiones para el PDF
                    pdf_width, pdf_height = pdf.w - 20, pdf.h - 40  # Ajustar para margen
                    aspect_ratio = original_image_width / original_image_height

                    # Ajustar el tamaño de la imagen manteniendo su aspecto
                    if original_image_width > pdf_width:
                        img_width = pdf_width
                        img_height = pdf_width / aspect_ratio
                    else:
                        img_width = original_image_width
                        img_height = original_image_height

                    # Limitar la altura para asegurar que no se salga de la página
                    if img_height > pdf_height / 2:
                        img_height = pdf_height / 2
                        img_width = img_height * aspect_ratio

                    # Verificar si hay suficiente espacio para la imagen
                    if pdf.get_y() + img_height > pdf.h - 20:
                        pdf.add_page()

                    # Calcular la posición centrada de la imagen
                    x_image = (pdf.w - img_width) / 2
                    y_image = pdf.get_y()

                    # Insertar la imagen
                    pdf.image(image_path, x=x_image, y=y_image, w=img_width, h=img_height)

                    # Dibujar el borde alrededor de la imagen
                    pdf.set_draw_color(0, 0, 0)
                    pdf.rect(x_image, y_image, img_width, img_height)

                    # Ajustar el offset en Y para la siguiente imagen
                    pdf.ln(img_height + 10)
                    image_counter += 1
                except Exception as e:
                    print(f"Error al procesar la imagen {image_file}: {e}")

# Parte 2: Añadir las imágenes de las demás clases
y_offset = None  # Reiniciar el offset en Y para la siguiente clase
current_x = 10  # Posición X inicial
spacing_x = 10  # Espacio entre las imágenes
margin = 10  # Margen entre las imágenes y los bordes
max_image_height = 0
add_page_flag = True  # Controla si es necesario añadir una nueva página al comenzar

output_cingoz_dir = "output_cingoz"  # Directorio principal para otras clases
for class_dir in os.listdir(output_cingoz_dir):
    class_path = os.path.join(output_cingoz_dir, class_dir)

    if os.path.isdir(class_path) and class_dir not in ['icon', 'image']:
        class_images = [img for img in os.listdir(class_path) if img.endswith(('.jpg', '.jpeg', '.png'))]

        if class_images:
            if add_page_flag:
                pdf.add_page()
                add_page_flag = False

            # Añadir el conteo de imágenes reconocidas para cada clase
            pdf.set_font("Arial", "B", 12)
            class_count = len(class_images)
            pdf.cell(0, 10, f"Numero de elementos de la clase '{class_dir}' encontrados: {class_count}", ln=True)
            pdf.ln(10)

            # Añadir las imágenes en una lista (una sobre otra)
            for i, image_file in enumerate(class_images, 1):
                image_path = os.path.join(class_path, image_file)
                try:
                    with Image.open(image_path) as img:
                        original_width, original_height = img.size

                    original_width_mm = original_width * 0.264583
                    original_height_mm = original_height * 0.264583

                    # Verificar si se requiere una nueva página antes de añadir la imagen
                    if pdf.get_y() + original_height_mm > pdf.h - 20:
                        pdf.add_page()
                        pdf.set_font("Arial", "B", 12)
                        pdf.cell(0, 10, f"Numero de elementos de la clase '{class_dir}' encontrados (continuación):", ln=True)
                        pdf.ln(10)

                    y_pos = pdf.get_y()
                    pdf.set_draw_color(0, 0, 0)
                    pdf.rect(10 - 1, y_pos - 1, original_width_mm + 2, original_height_mm + 2)
                    pdf.image(image_path, x=10, y=y_pos, w=original_width_mm)
                    pdf.ln(original_height_mm + 10)
                except Exception as e:
                    print(f"Error al procesar la imagen {image_file}: {e}")

# Parte 3: Añadir las imágenes de ProgressBar
output_pb_dir = "output_pb"  # Asegúrate de que este directorio exista
progressbar_images = [img for img in os.listdir(output_pb_dir) if img.endswith(('.jpg', '.jpeg', '.png'))]

if progressbar_images:
    if current_x != 10:  # Si aún hay espacio en la página actual, continuamos
        pdf.ln(max_image_height + 10)
    else:
        pdf.add_page()

    pdf.set_font("Arial", "B", 12)
    progressbar_count = len(progressbar_images)
    pdf.cell(0, 10, f"Barras de progreso encontradas: {progressbar_count}", ln=True)
    pdf.ln(10)

    # Añadir las imágenes de ProgressBar con el mismo formato
y_offset = None
current_x = 10
max_image_height = 0

for i, image_file in enumerate(progressbar_images, 1):
    image_path = os.path.join(output_pb_dir, image_file)
    try:
        with Image.open(image_path) as img:
            original_width, original_height = img.size

        original_width_mm = original_width * 0.264583
        original_height_mm = original_height * 0.264583

        # Verificar si se requiere una nueva página antes de añadir la imagen
        if pdf.get_y() + original_height_mm > pdf.h - 20:
            pdf.add_page()
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Barras de progreso encontradas (continuación):", ln=True)
            pdf.ln(10)
            current_x = 10
            max_image_height = 0

        y_pos = pdf.get_y()
        pdf.set_draw_color(0, 0, 0)
        pdf.rect(10 - 1, y_pos - 1, original_width_mm + 2, original_height_mm + 2)
        pdf.image(image_path, x=10, y=y_pos, w=original_width_mm)
        pdf.ln(original_height_mm + 10)
    except Exception as e:
        print(f"Error al procesar la imagen {image_file}: {e}")


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


# shutil.rmtree('capturas')
# shutil.rmtree('output_evaluated_images')
# shutil.rmtree('capturas_navegacion')
# shutil.rmtree('capturasSelenium')
# shutil.rmtree('fotosSelenium')
# shutil.rmtree('output_cingoz')
# shutil.rmtree('output_icon')
# shutil.rmtree('output_pb')
# shutil.rmtree('output_images')
