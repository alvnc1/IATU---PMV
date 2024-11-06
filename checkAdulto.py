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
title = "Revisión de Criterios Adulto Mayor"
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