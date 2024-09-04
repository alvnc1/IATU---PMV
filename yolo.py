from IPython.display import display, Image
import os
import subprocess
import cv2
from inference_sdk import InferenceHTTPClient
from dataclasses import dataclass

CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="FCbLovxwSDWFYTwaMuQi"
)
# Directorio con las imágenes de entrada
input_dir = "/content/test_images"  # Cambia esta ruta a la ubicación de tu directorio de imágenes
output_base_dir = "output_evaluated_images"  # Directorio base para guardar los resultados
os.makedirs(output_base_dir, exist_ok=True)

dic_clases = {}
@dataclass
class Elemento:
  cantidad: int = 0
  confianza_promedio: float = 0.0
  cobertura_promedio: float = 0.0
# Procesar cada imagen en el directorio de entrada
for image_filename in os.listdir(input_dir):
    if image_filename.endswith(('.jpg', '.jpeg', '.png')):  # Filtrar solo las imágenes
        image_path = os.path.join(input_dir, image_filename)

        # Realizar la inferencia en la imagen
        result = CLIENT.infer(image_path, model_id="cingoz8/1")

        # Crear un subdirectorio específico para esta imagen en la salida
        image_output_dir = os.path.join(output_base_dir, os.path.splitext(image_filename)[0])
        os.makedirs(image_output_dir, exist_ok=True)

        # Crear subdirectorios para las bounding boxes y los archivos de texto
        bboxes_dir = os.path.join(image_output_dir, "bboxes")
        os.makedirs(bboxes_dir, exist_ok=True)

        # Cargar la imagen usando OpenCV
        image = cv2.imread(image_path)
        original_height, original_width, _ = image.shape

        # Procesar los resultados y guardar cada bounding box como una imagen separada y sus propiedades
        for i, prediction in enumerate(result['predictions']):
            if prediction['class'] == "icon": #NO SE CONSIDERAN LOS ICONOS PARA ESTE MODELO YA QUE APP-ICON EN MEJOR
              continue
            # Extraer las coordenadas y el tamaño de la bounding box
            x0 = int(prediction['x'] - prediction['width'] / 2)
            y0 = int(prediction['y'] - prediction['height'] / 2)
            x1 = int(prediction['x'] + prediction['width'] / 2)
            y1 = int(prediction['y'] + prediction['height'] / 2)

            # Dibujar la bounding box en la imagen original
            cv2.rectangle(image, (x0, y0), (x1, y1), color=(0, 255, 0), thickness=2)

            # Poner el label encima de la bounding box
            label = f"{prediction['class']} ({prediction['confidence']:.2f})"
            cv2.putText(image, label, (x0, y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Recortar la región de la bounding box para guardarla como imagen separada
            cropped_image = image[y0:y1, x0:x1]

            # Generar el nombre de archivo para la imagen recortada
            output_image_name = f"bbox_{i+1}.jpg"
            output_image_path = os.path.join(bboxes_dir, output_image_name)

            # Guardar la imagen recortada
            cv2.imwrite(output_image_path, cropped_image)

            # Obtener propiedades adicionales
            bbox_width = x1 - x0
            bbox_height = y1 - y0
            bbox_area = bbox_width * bbox_height
            aspect_ratio = bbox_width / bbox_height
            center_x = (x0 + x1) / 2
            center_y = (y0 + y1) / 2
            coverage_percentage = (bbox_area / (original_width * original_height)) * 100
            gray_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
            average_brightness = gray_image.mean()
            contrast = gray_image.max() - gray_image.min()
            std_dev_brightness = gray_image.std()
            perimeter = 2 * (bbox_width + bbox_height)

            if prediction['class'] not in dic_clases:
              dic_clases[prediction['class']] = Elemento()
            elemento = dic_clases[prediction['class']]
            elemento.cantidad += 1
            elemento.confianza_promedio = (elemento.confianza_promedio * (elemento.cantidad - 1) + float(prediction['confidence'])) / elemento.cantidad
            elemento.cobertura_promedio = (elemento.confianza_promedio * (elemento.cantidad - 1) + coverage_percentage) / elemento.cantidad

            # Guardar las propiedades en un archivo .txt
            output_txt_path = os.path.join(bboxes_dir, f"bbox_{i+1}.txt")
            with open(output_txt_path, 'w') as f:
                f.write(f"Bounding Box {i+1}:\n")
                f.write(f" - Clase: {prediction['class']}\n")
                f.write(f" - Confianza: {prediction['confidence']:.2f}\n")
                f.write(f" - Dimensiones: {bbox_width}x{bbox_height} píxeles\n")
                f.write(f" - Área de la bounding box: {bbox_area} píxeles cuadrados\n")
                f.write(f" - Relación de aspecto: {aspect_ratio:.2f}\n")
                f.write(f" - Centro de la bounding box: ({center_x}, {center_y})\n")
                f.write(f" - Cobertura en la imagen original: {coverage_percentage:.2f}%\n")
                f.write(f" - Brillo promedio: {average_brightness:.2f}\n")
                f.write(f" - Contraste: {contrast}\n")
                f.write(f" - Desviación estándar del brillo: {std_dev_brightness:.2f}\n")
                f.write(f" - Perímetro de la bounding box: {perimeter} píxeles\n")

        # Guardar la imagen original con todas las bounding boxes dibujadas en el directorio de salida
        output_image_path = os.path.join(image_output_dir, os.path.basename(image_path))
        cv2.imwrite(output_image_path, image)
print("Proceso completado para todas las imágenes.")