# Configurar el entorno para que Chrome se ejecute en modo headless
import os
os.environ['PATH'] += ":/usr/lib/chromium-browser/"

# Importar las librerías necesarias
from requests_html import AsyncHTMLSession
import nest_asyncio
import asyncio
import colorsys
import time
import re
import requests
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



# Aplicar parche al bucle de eventos existente
nest_asyncio.apply()

# Crear una sesión asíncrona HTML
asession = AsyncHTMLSession()

# Función para obtener y renderizar la página
async def get_page(url):
    response = await asession.get(url)
    await response.html.arender(sleep=5, timeout=60)  # Aumentar tiempo de espera si es necesario
    return response

def rgb_or_rgba_to_tuple(color_str):
    # Remover 'rgb(' o 'rgba(' y cerrar paréntesis
    color_str = color_str.replace('rgb(', '').replace('rgba(', '').replace(')', '')
    # Dividir los valores y convertirlos a enteros
    color_tuple = tuple(int(c) for c in color_str.split(',')[:3])  # Tomar solo los primeros tres valores
    return color_tuple

def calculate_contrast(color1, color2):
    # Calcular la luminancia relativa para ambos colores
    l1 = colorsys.rgb_to_hls(*color1)[1]
    l2 = colorsys.rgb_to_hls(*color2)[1]
    return abs(l1 - l2)

#----------------------------------------------------------------
# Función principal para realizar análisis de la página
def hdu_uno(url):
    # Extraer componentes usando requests_html
    response = asyncio.get_event_loop().run_until_complete(get_page(url))

    # --- Criterios de Usabilidad ---

    # 1. Búsqueda de campos de búsqueda con diferentes atributos y validaciones adicionales
    # Configurar Selenium con Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Navegar a la URL
    driver.get(url)

    # 1. Búsqueda de campos de búsqueda con diferentes atributos y validaciones adicionales
    search_fields = driver.find_elements(By.CSS_SELECTOR, 'input[type="search"], input[name*="search"], input[placeholder*="search"], input[type="text"][name*="search"], input[type="text"][placeholder*="search"], form[action*="search"] input')

    # Inicializar un contador de campos de búsqueda válidos
    valid_search_fields_count = 0

    if search_fields:
        for field in search_fields:
            issues = []

            # Verificar si el campo de búsqueda tiene atributos de accesibilidad
            aria_label = field.get_attribute('aria-label')
            title_attr = field.get_attribute('title')
            if not (aria_label or title_attr):
                issues.append("No tiene atributos de accesibilidad ('aria-label' o 'title').")

            # Verificar visibilidad y tamaño
            if not field.is_displayed() or field.size['width'] <= 100:
                issues.append("Podría no ser visible o su tamaño es insuficiente.")
            else:
                # Obtener la posición del campo de búsqueda
                location = field.location
                if location['y'] >= 600:  # Supongamos que la cabecera esté en los primeros 600px
                    issues.append(f"Ubicación inusual para un campo de búsqueda (posicionada en y={location['y']}).")

            # Comprobar si el campo de búsqueda está dentro de un contenedor de cabecera
            parent_header = field.find_elements(By.XPATH, "ancestor::header")
            if not parent_header:
                issues.append("No está ubicado dentro de la cabecera.")

            if issues:
                print(f"Problemas encontrados en un campo de búsqueda ({field.get_attribute('name')} o '{aria_label or title_attr}'): " + " // ".join(issues))
            else:
                valid_search_fields_count += 1

        if valid_search_fields_count > 0:
            print(f"{valid_search_fields_count} campo(s) de búsqueda válido(s) y bien posicionado(s) detectado(s).")
    else:
        print("Campo de búsqueda NO detectado.")


    # Cerrar el driver
    driver.quit()



    # 2. Verificación de palabras clave en enlaces
    # Parámetro N: cantidad mínima de veces que una palabra debe aparecer para ser considerada
    N = 3

    # Función para filtrar palabras no vacías y contar su frecuencia
    def obtener_palabras_clave_frecuentes(texto, min_frecuencia):
        palabras = re.findall(r'\b\w+\b', texto.lower())
        palabras_filtradas = [palabra for palabra in palabras if len(palabra) > 3]  # Filtrar palabras con más de 3 caracteres
        contador_palabras = Counter(palabras_filtradas)
        # Filtrar palabras que aparecen al menos 'min_frecuencia' veces
        palabras_clave_frecuentes = {palabra: frecuencia for palabra, frecuencia in contador_palabras.items() if frecuencia >= min_frecuencia}
        return palabras_clave_frecuentes

    # Extraer todo el texto de los enlaces en la página
    todo_el_texto = ' '.join([link.text.strip() for link in response.html.find('a')])

    # Obtener las palabras clave más frecuentes que aparecen al menos N veces
    palabras_clave_frecuentes = obtener_palabras_clave_frecuentes(todo_el_texto, N)

    enlaces_con_palabras_clave = []
    palabras_usadas = set()  # Para asegurarnos de que no se repitan las palabras clave

    # Iterar sobre todos los enlaces encontrados en la página
    for link in response.html.find('a'):
        texto_enlace = link.text.strip().lower()

        if texto_enlace:
            # Verificar si alguna de las palabras clave frecuentes aparece en el enlace
            for palabra in palabras_clave_frecuentes:
                if palabra in texto_enlace and palabra not in palabras_usadas:
                    enlaces_con_palabras_clave.append(f"Enlace: '{texto_enlace}' contiene la palabra clave: '{palabra}'. Podría ser un enlace relevante para entender de que trata el sitio.")
                    palabras_usadas.add(palabra)
                    break  # Salir del bucle para evitar agregar el mismo enlace varias veces

        # Verificar si el enlace contiene una imagen o icono con alt o aria-label relevante
        elif link.find('img'):
            alt_text = link.find('img')[0].attrs.get('alt', '').lower()
            for palabra in palabras_clave_frecuentes:
                if palabra in alt_text and palabra not in palabras_usadas:
                    enlaces_con_palabras_clave.append(f"Imagen con alt: '{alt_text}' contiene la palabra clave: '{palabra}'. Podría ser un enlace relevante para entender de que trata el sitio.")
                    palabras_usadas.add(palabra)
                    break

        elif link.attrs.get('aria-label'):
            aria_label = link.attrs.get('aria-label', '').lower()
            for palabra in palabras_clave_frecuentes:
                if palabra in aria_label and palabra not in palabras_usadas:
                    enlaces_con_palabras_clave.append(f"Enlace con aria-label: '{aria_label}' contiene la palabra clave: '{palabra}'. Podría ser un enlace relevante para entender de que trata el sitio.")
                    palabras_usadas.add(palabra)
                    break

    # Evaluación del resultado
    if enlaces_con_palabras_clave:
        print("Enlaces que contienen palabras clave frecuentes:")
        for detalle in enlaces_con_palabras_clave:
            print(detalle)
    else:
        print(f"No se encontraron enlaces que contengan palabras clave que aparezcan al menos {N} veces.")

    # 3. Verificación de imágenes genéricas.
    nlp = spacy.load("en_core_web_md")

    # Palabras clave negativas
    palabras_clave_negativas = [
        'clipart', 'generic', 'placeholder', 'dummy', 'image1', 'stock',
        'shutterstock', 'getty', 'example', 'lorem', 'ipsum', 'filler', 'template'
    ]

    # Lista para almacenar mensajes de advertencia
    mensajes_advertencia = []
    conteo_errores_imagenes = 0

    # Verificación de imágenes y su texto alternativo
    for img in response.html.find('img'):
        alt_text = img.attrs.get('alt', '').strip().lower()
        src = img.attrs.get('src', '').strip().lower()
        problema_detectado = False

        # Validar que la imagen tenga texto alternativo significativo
        if not alt_text:
            mensajes_advertencia.append(f"Imagen sin descripción adecuada. Fuente: {src}")
            problema_detectado = True
        else:
            # Verificar si el texto alternativo o el src contienen términos genéricos o problemáticos
            if any(negativa in alt_text for negativa in palabras_clave_negativas) or any(negativa in src for negativa in palabras_clave_negativas):
                mensajes_advertencia.append(f"Imagen genérica o de baja calidad detectada. Fuente: {src} con descripción '{alt_text}'")
                problema_detectado = True

        # Comprobación de tamaño de imagen
        try:
            width = int(img.attrs.get('width', 0))
            height = int(img.attrs.get('height', 0))
            aspect_ratio = width / height if height > 0 else 0

            if width < 50 or height < 50:
                mensajes_advertencia.append(f"Imagen muy pequeña detectada. Fuente: {src}")
                problema_detectado = True
            elif aspect_ratio < 0.5 or aspect_ratio > 2:
                mensajes_advertencia.append(f"Imagen con dimensiones inusuales detectada. Fuente: {src}")
                problema_detectado = True

            # Verificación de compresión excesiva
            if not problema_detectado:  # Solo verificar compresión si no se detectó otro problema grave
                try:
                    image_url = src if src.startswith('http') else f"https://{src}"
                    image_response = requests.get(image_url)
                    image_response.raise_for_status()
                    image = Image.open(BytesIO(image_response.content))

                    file_size_kb = len(image_response.content) / 1024  # Tamaño del archivo en KB
                    pixel_count = width * height
                    compression_ratio = file_size_kb / pixel_count if pixel_count > 0 else 0

                    if compression_ratio < 0.1:
                        mensajes_advertencia.append(f"Imagen de baja calidad detectada (muy comprimida). Fuente: {src}")
                        problema_detectado = True

                except requests.exceptions.RequestException:
                    mensajes_advertencia.append(f"Problema al cargar la imagen. Fuente: {src}")
                    problema_detectado = True

        except ValueError:
            mensajes_advertencia.append(f"No se pudieron verificar las dimensiones de la imagen. Fuente: {src}")
            problema_detectado = True

        # Verificar si el nombre del archivo de la imagen en el src indica que podría ser genérica
        if re.search(r'\b(?:img|image|placeholder|stock)\b', src):
            mensajes_advertencia.append(f"Nombre del archivo sugiere que la imagen podría ser genérica. Fuente: {src}")
            problema_detectado = True

        # Verificación semántica del texto alternativo usando NLP
        if alt_text and not problema_detectado:  # Solo verificar semántica si no hay otros problemas
            alt_doc = nlp(alt_text)
            page_content = nlp(" ".join([p.text for p in response.html.find('p')])) if response.html.find('p') else None

            if alt_doc and page_content:
                if alt_doc.vector_norm and page_content.vector_norm:
                    similarity = alt_doc.similarity(page_content)
                    if similarity < 0.2:
                        mensajes_advertencia.append(f"Descripción de la imagen no relevante para el contenido. Fuente: {src}")
                else:
                    mensajes_advertencia.append(f"No se pudo verificar la relevancia de la descripción para la imagen. Fuente: {src}")
            else:
                mensajes_advertencia.append("No se pudo realizar la verificación semántica del texto alternativo.")

        # Incrementar el conteo de errores si se detectó un problema
        if problema_detectado:
            conteo_errores_imagenes += 1

    # Evaluación final
    if mensajes_advertencia:
        for mensaje in mensajes_advertencia:
            print(mensaje)

        if conteo_errores_imagenes >= 5:
            print(f"Se encontraron {conteo_errores_imagenes} problemas con las imágenes del sitio. Esto podría indicar un mantenimiento deficiente o el uso de contenido desactualizado.")
    else:
        print("Validación de imágenes completada sin problemas.")


    # 4. Optimización del título para buscadores
    nlp = spacy.load("en_core_web_md")
    title_tag = response.html.find('title', first=True)
    mensajes_advertencia = []

    if title_tag:
        title_text = title_tag.text.strip()

        # Verificación de la longitud del título
        if 50 <= len(title_text) <= 60:
            print("Título con longitud óptima para buscadores:", title_text)
        elif len(title_text) < 50:
            mensajes_advertencia.append(f"Advertencia: El título es demasiado corto ({len(title_text)} caracteres): {title_text}")
        else:
            mensajes_advertencia.append(f"Advertencia: El título es demasiado largo ({len(title_text)} caracteres): {title_text}")

        # Análisis de palabras clave en el título
        title_doc = nlp(title_text)

        # Obtener el contenido de la página para comparar
        page_content = " ".join([p.text for p in response.html.find('p')])
        page_doc = nlp(page_content)

        # Extraer palabras clave del contenido de la página
        keywords = [token.text for token in page_doc if token.is_alpha and not token.is_stop and len(token.text) > 3]
        common_keywords = [token.text for token in title_doc if token.text in keywords]

        if common_keywords:
            print(f"Palabras clave relevantes encontradas en el título: {', '.join(common_keywords)}")
        else:
            mensajes_advertencia.append(f"Advertencia: El título no contiene palabras clave relevantes o bien no se vuelve a mencionar el título en el resto del sitio.: {title_text}.")

        # Evaluación de la relevancia semántica del título
        title_similarity = title_doc.similarity(page_doc)
        if title_similarity < 0.2:  # Ajustar el umbral según las necesidades
            mensajes_advertencia.append(f"Advertencia: El título '{title_text}' puede no ser relevante para el contenido de la página o bien no se vuelve a mencionar en el resto del sitio.")
        else:
            print(f"El título es semánticamente relevante con una similitud de {title_similarity:.2f} con el contenido de la página.")
    else:
        mensajes_advertencia.append("Error crítico: No se encontró un título en la página.")

    # Evaluación final
    if mensajes_advertencia:
        for mensaje in mensajes_advertencia:
            print(mensaje)
    else:
        print("Validación del título completada sin problemas.")

    # 5. Información corporativa en la página (considerando inglés y español)
    # Ampliar la lista de palabras clave para detectar información corporativa
    palabras_clave_corporativas = [
        "acerca de", "sobre nosotros", "about", "about us", "empresa", "quiénes somos",
        "compañía", "our company", "our team", "our story", "historia", "nuestra empresa", "contacto", "contact us"
    ]

    # Buscar secciones relevantes en el pie de página o divs específicos
    about_sections = response.html.find('footer, div')
    corporate_info_detectada = False

    for section in about_sections:
        section_text = section.text.lower()

        # Verificar si la sección contiene alguna de las palabras clave corporativas
        if any(keyword in section_text for keyword in palabras_clave_corporativas):
            print("Información corporativa detectada correctamente. Los visitantes entenderán quién está detrás del sitio.")
            corporate_info_detectada = True
            break  # Si se detecta, no necesitamos seguir buscando

    # Evaluación final
    if corporate_info_detectada != True:
        print("Información corporativa NO detectada.")

    # 6. URL sencilla y fácil de recordar.
    # Extraer y analizar la URL de la página
    url_parts = urlparse(url)
    path = url_parts.path.strip('/')
    path_segments = path.split('/')
    query = url_parts.query

    # Evaluar la simplicidad de la URL
    url_simple = True
    mensajes_advertencia = []

    # Verificar la presencia de parámetros en la URL
    if query:
        url_simple = False
        mensajes_advertencia.append(f"URL compleja: contiene parámetros en la cadena de consulta: '{query}'")

    # Verificar la longitud de la URL
    if len(url) > 100:  # Umbral ajustable para considerar una URL demasiado larga
        url_simple = False
        mensajes_advertencia.append(f"URL demasiado larga: {len(url)} caracteres")

    # Verificar la cantidad de subdirectorios y su simplicidad
    if len(path_segments) > 2:  # Umbral ajustable para la cantidad de subdirectorios
        url_simple = False
        mensajes_advertencia.append(f"URL con múltiples subdirectorios: {'/'.join(path_segments)}")

    # Verificar la presencia de identificadores crípticos o poco memorables
    if any(segment.isdigit() for segment in path_segments):
        url_simple = False
        mensajes_advertencia.append(f"URL con identificadores numéricos en la ruta: {'/'.join(path_segments)}")

    # Evaluación final
    if url_simple:
        print("La URL es sencilla y fácil de recordar:", url)
    else:
        for mensaje in mensajes_advertencia:
            print(mensaje)

def hdu_dos(url):
    response = asyncio.get_event_loop().run_until_complete(get_page(url))
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920x1080')

    # Usar `webdriver-manager` para manejar `ChromeDriver`
    service = Service(ChromeDriverManager().install())

    # Iniciar WebDriver con el servicio y las opciones configuradas
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Navegar a la página deseada
    driver.get(url)

    # Recuento de recursos innecesarios.
    # Recuento y análisis de scripts
    scripts = driver.find_elements(By.TAG_NAME, 'script')
    large_scripts = [script for script in scripts if script.get_attribute('src') and len(script.get_attribute('src')) > 0]
    print(f"Se encontró {len(scripts)} script{'s' if len(scripts) != 1 else ''} en la página.")
    if large_scripts:
        print(f"Script{'s' if len(large_scripts) != 1 else ''} con fuente externa: {len(large_scripts)}")

    # Recuento y análisis de videos
    videos = driver.find_elements(By.TAG_NAME, 'video')
    print(f"Se encontró {len(videos)} video{'s' if len(videos) != 1 else ''} en la página.")
    for video in videos:
        video_size = int(video.get_attribute('size')) if video.get_attribute('size') else 0
        if video_size > 5000000:  # Umbral ajustable, por ejemplo, 5MB
            print(f"Advertencia: Video grande detectado con tamaño {video_size / 1000000:.2f}MB")

    # Recuento y análisis de imágenes
    imagenes = driver.find_elements(By.TAG_NAME, 'img')
    print(f"Se encontró {len(imagenes)} imagen{'es' if len(imagenes) != 1 else ''} en la página.")
    for img in imagenes:
        img_size = int(img.get_attribute('size')) if img.get_attribute('size') else 0
        if img_size > 2000000:  # Umbral ajustable, por ejemplo, 2MB
            print(f"Advertencia: Imagen grande detectada con tamaño {img_size / 1000000:.2f}MB")

    # Recuento y análisis de archivos de audio
    audios = driver.find_elements(By.TAG_NAME, 'audio')
    print(f"Se encontró {len(audios)} archivo{'s de audio' if len(audios) != 1 else ' de audio'} en la página.")
    for audio in audios:
        audio_size = int(audio.get_attribute('size')) if audio.get_attribute('size') else 0
        if audio_size > 10000000:  # Umbral ajustable, por ejemplo, 10MB
            print(f"Advertencia: Archivo de audio grande detectado con tamaño {audio_size / 1000000:.2f}MB")

    # Recuento y análisis de applets (poco comunes pero posibles)
    applets = driver.find_elements(By.TAG_NAME, 'applet')
    print(f"Se encontró {len(applets)} applet{'s' if len(applets) != 1 else ''} en la página.")
    if applets:
        print("Advertencia: Uso de applets detectado. Esto podría afectar la compatibilidad y rendimiento de la página.")

    # Evaluación final
    total_resources = len(scripts) + len(videos) + len(imagenes) + len(audios) + len(applets)
    if total_resources > 50:  # Umbral ajustable para cantidad total de recursos
        print(f"Advertencia: Se cargaron {total_resources} recursos en la página, lo que puede afectar el rendimiento.")
    else:
        print(f"Cantidad total de recursos cargado{'s' if total_resources != 1 else ''} en la página: {total_resources}")

    # Detección de barreras innecesarias.
    # 1. Detección de formularios de registro
    try:
        registration_forms = driver.find_elements(By.CSS_SELECTOR, 'form[action*="register"], form[action*="signup"], form[action*="subscribe"]')
        if registration_forms:
            for form in registration_forms:
                if form.is_displayed():
                    print(f"Formulario de registro detectado: {form.get_attribute('action')}")
                else:
                    print(f"Formulario de registro no visible: {form.get_attribute('action')}")
        else:
            print("No se encontraron formularios de registro visibles en la página.")
    except NoSuchElementException:
        print("Error al buscar formularios de registro.")

    # 2. Detección de ventanas modales de suscripción
    try:
        modals = driver.find_elements(By.CSS_SELECTOR, '[class*="modal"], [class*="popup"], [class*="subscribe"], [class*="signup"]')
        modal_detected = False
        for modal in modals:
            if modal.is_displayed():
                modal_text = modal.text.lower()
                if any(keyword in modal_text for keyword in ['registrarse', 'suscribirse', 'register', 'sign up', 'subscribe']):
                    print(f"Ventana modal de suscripción detectada con contenido relevante: {modal_text[:100]}...")
                    modal_detected = True
                else:
                    print(f"Ventana modal detectada, pero no parece relacionada con el registro o suscripción: {modal_text[:100]}...")
        if not modal_detected:
            print("No se encontraron ventanas modales de suscripción que bloqueen el acceso al contenido.")
    except NoSuchElementException:
        print("Error al buscar ventanas modales de suscripción.")

    # 3. Verificación de posibilidad de cierre de modales
    try:
        close_buttons = driver.find_elements(By.CSS_SELECTOR, '[class*="close"], button[class*="close"], button[class*="cancel"]')
        for button in close_buttons:
            if button.is_displayed() and button.is_enabled():
                print("Botón de cierre de ventana modal detectado y habilitado.")
            else:
                print("Advertencia: Botón de cierre de ventana modal no disponible o no visible.")
    except NoSuchElementException:
        print("Error al buscar botones de cierre para ventanas modales.")

    # Cantidad de ventanas que se abren por navegación.
    # Obtener el número inicial de ventanas/pestañas abiertas
    initial_window_handles = driver.window_handles
    initial_window_count = len(initial_window_handles)
    print(f"Cantidad inicial de ventanas/pestañas abiertas: {initial_window_count}")

    # Inicializar current_window_count
    current_window_count = initial_window_count

    # Ejecutar una serie de acciones que podrían abrir nuevas ventanas/pestañas
    try:
        # Ejemplo: clic en un enlace que podría abrir una nueva ventana/pestaña
        potential_link = driver.find_element(By.CSS_SELECTOR, 'a[target="_blank"]')
        potential_link_text = potential_link.text or potential_link.get_attribute('href')
        print(f"Se hizo clic en el enlace que potencialmente abre nueva pestaña: '{potential_link_text}'")

        potential_link.click()

        # Esperar un momento para permitir la apertura de la nueva pestaña
        time.sleep(2)

        # Comprobar el número de ventanas/pestañas después de la acción
        current_window_handles = driver.window_handles
        current_window_count = len(current_window_handles)

        if current_window_count > initial_window_count:
            print(f"Se abrió(eron) {current_window_count - initial_window_count} nueva(s) ventana(s)/pestaña(s) al hacer clic en el enlace: '{potential_link_text}'.")
        else:
            print(f"No se abrió ninguna nueva ventana/pestaña al hacer clic en el enlace: '{potential_link_text}'.")
    except NoSuchElementException:
        print("No se encontró un enlace que abra una nueva ventana o pestaña.")

    # Evaluación final
    if current_window_count > initial_window_count:
        print(f"Advertencia: Durante la navegación se abrió(eron) {current_window_count - initial_window_count} nueva(s) ventana(s)/pestaña(s), lo que podría afectar la experiencia del usuario.")
    else:
        print("Navegación sin apertura de ventanas/pestañas adicionales innecesarias.")

    # Longitud y cantidad de clicks.
    # 1. Medición de la longitud de la página
    page_height = driver.execute_script("return document.body.scrollHeight")
    print(f"Altura total de la página: {page_height} píxeles")

    # Evaluación de la longitud de la página
    if page_height > 3000:  # Ajuste según el umbral esperado para la longitud de la página
        print("Advertencia: La página es demasiado larga, lo que podría afectar la navegación eficiente.")
    else:
        print("Longitud de la página dentro del rango aceptable.")

    # 2. Análisis de la cantidad de clics para completar una tarea clave (sección corporativa/contacto)

    # Definir las palabras clave corporativas a buscar
    palabras_clave_corporativas = [
        "acerca de", "sobre nosotros", "about", "about us", "empresa", "quiénes somos",
        "compañía", "our company", "our team", "our story", "historia", "nuestra empresa", "contacto", "contact us"
    ]

    # Inicializar contador de clics y bandera para detección de secciones corporativas
    click_count = 0
    seccion_encontrada = False

    # 1. Búsqueda en enlaces
    for palabra in palabras_clave_corporativas:
        try:
            enlace_corporativo = driver.find_element(By.PARTIAL_LINK_TEXT, palabra)
            if enlace_corporativo.is_displayed():
                enlace_corporativo.click()
                click_count += 1
                seccion_encontrada = True
                print(f"Sección '{palabra}' encontrada en un enlace y accedida con {click_count} clic(s).")
                break
        except NoSuchElementException:
            continue

    # 2. Si no se encuentra en enlaces, buscar en otros elementos de la página
    if not seccion_encontrada:
        for palabra in palabras_clave_corporativas:
            try:
                # Buscar en otros elementos comunes como divs, spans, párrafos
                secciones = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{palabra}')]")
                for seccion in secciones:
                    if seccion.is_displayed():
                        seccion_encontrada = True
                        print(f"Sección '{palabra}' encontrada en un elemento no enlazado.")
                        break
                if seccion_encontrada:
                    break
            except NoSuchElementException:
                continue

    # Evaluación final
    if seccion_encontrada and click_count > 0:
        if click_count > 3:  # Ajuste según el umbral aceptable de clics para completar una tarea
            print(f"Advertencia: Se requieren {click_count} clics para acceder a la sección corporativa.")
        else:
            print(f"La sección corporativa fue accesible con {click_count} clic(s), dentro del rango aceptable.")
    elif seccion_encontrada and click_count == 0:
        print("Sección corporativa encontrada sin necesidad de clics adicionales.")
    else:
        print("No se encontró ninguna sección corporativa utilizando las palabras clave especificadas.")

    # 3. Verificación de la profundidad de navegación

    # Ejemplo: Medición de la profundidad del menú de navegación
    menus = driver.find_elements(By.CSS_SELECTOR, 'nav, ul, ol')
    depth_counts = []

    for menu in menus:
        depth = len(menu.find_elements(By.CSS_SELECTOR, 'ul ul'))  # Contar submenús anidados
        depth_counts.append(depth)

    if depth_counts:
        max_depth = max(depth_counts)
        print(f"Profundidad máxima de navegación detectada: {max_depth} niveles.")
        if max_depth > 2:  # Ajuste según el umbral aceptable para la profundidad
            print("Advertencia: La estructura de navegación es demasiado profunda.")
        else:
            print("La estructura de navegación es aceptablemente profunda.")
    else:
        print("No se detectaron menús con subniveles.")


    # Un click en formularios.

    # 1. Búsqueda de formularios y verificación de autocompletar
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
                break  # Solo necesitamos un botón de este tipo para considerar el formulario

    # Evaluación de los formularios encontrados
    if formularios_con_autocompletar:
        print(f"Se encontraron {len(formularios_con_autocompletar)} formularios con autocompletar habilitado (Podrían ser barras de búsqueda).")
    else:
        print("No se encontraron formularios con autocompletar habilitado.")

    if formularios_con_un_click:
        print(f"Se encontraron {len(formularios_con_un_click)} formularios con botones de acción rápida (un-click).")
    else:
        print("No se encontraron formularios con botones de acción rápida (un-click).")

    # Evaluación final
    if not formularios_con_autocompletar and not formularios_con_un_click:
        print("No se encontraron formularios con autocompletar ni con botones de acción rápida, podría considerarse una oportunidad de mejora en la usabilidad.")

def hdu_tres(url):
    response = asyncio.get_event_loop().run_until_complete(get_page(url))
    # Configurar Selenium con Chrome en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Navegar a la URL
    driver.get(url)

        # 7. Verificación de menús de navegación y enlaces visibles
    selectors = ['nav', 'ul', 'ol', '.menu', '.navbar', '.navigation']
    navigation_menus = []
    for selector in selectors:
        navigation_menus.extend(driver.find_elements(By.CSS_SELECTOR, selector))

    # Evaluación de la existencia de menús de navegación
    if navigation_menus:
        print(f"Se encontraron {len(navigation_menus)} menús de navegación.")
        for index, menu in enumerate(navigation_menus, start=1):
            items = menu.find_elements(By.TAG_NAME, 'li')
            visible_items = [item for item in items if item.is_displayed()]
            print(f"Menú {index} con {len(visible_items)} elementos visibles.")

            # Verificación de enlaces dentro del menú
            links = menu.find_elements(By.TAG_NAME, 'a')
            visible_links = [link for link in links if link.is_displayed()]
            if visible_links:
                print(f"Menú {index} tiene {len(visible_links)} enlaces visibles y clickeables.")
            else:
                print(f"Advertencia: Menú {index} no tiene enlaces visibles y clickeables.")
    else:
        print("No se encontraron menús de navegación.")

    # 2. Verificación de un enlace para regresar a la página de inicio
    try:
        home_link = driver.find_element(By.CSS_SELECTOR, 'a[href="/"], a[rel="home"], a[class*="home"], a[href^="/index"]')
        if home_link.is_displayed():
            print("Enlace para regresar a la página de inicio detectado y visible.")
        else:
            print("Advertencia: El enlace para regresar a la página de inicio no es visible.")
    except NoSuchElementException:
        print("No se encontró un enlace para regresar a la página de inicio.")

    # 1. Búsqueda de menús de navegación y análisis de su estructura
    navigation_menus = driver.find_elements(By.CSS_SELECTOR, 'nav, ul, ol, .menu, .navbar, .navigation')
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
        print(f"Se encontraron un total de {total_items} elementos en los menús de navegación.")
        if deep_menus_count > 0:
            print(f"Se encontraron {deep_menus_count} menús de navegación profundos con una profundidad máxima de {max_depth} niveles.")
        else:
            print("Todos los menús de navegación son amplios (sin niveles profundos).")
    else:
        print("No se encontraron menús de navegación en la página.")

    # 9. Verificación de la ubicación y clicabilidad de las pestañas de navegación
    tabs = driver.find_elements(By.CSS_SELECTOR, 'nav a, header a, .menu a, .navbar a')
    tabs_at_top = [tab for tab in tabs if tab.location['y'] < 200]

    if tabs_at_top:
        clickeable_tabs = [tab for tab in tabs_at_top if tab.is_displayed() and tab.is_enabled()]
        if clickeable_tabs:
            print(f"Se encontraron {len(clickeable_tabs)} pestañas de navegación en la parte superior, todas clickeables.")
            for index, tab in enumerate(clickeable_tabs, start=1):
                print(f"Pestaña {index}: Texto='{tab.text}', Posición Y={tab.location['y']}px")
                tab.screenshot(f"pestana_{index}_captura.png")
        else:
            print("Se encontraron pestañas en la parte superior, pero ninguna es clickeable.")
    else:
        print("No se encontraron pestañas de navegación en la parte superior.")

    top_containers = driver.find_elements(By.CSS_SELECTOR, 'header, .top-menu, .navbar, .top-navigation')
    for container in top_containers:
        if container.location['y'] < 200:
            container_tabs = container.find_elements(By.TAG_NAME, 'a')
            if container_tabs:
                print(f"Contenedor de navegación superior encontrado con {len(container_tabs)} pestañas.")
                container.screenshot(f"contenedor_superior_captura.png")
            else:
                print(f"Contenedor de navegación superior encontrado, pero sin pestañas clickeables.")

    # 10. Verificación de la accesibilidad del contenido desde múltiples enlaces
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
            print(f"Ruta '{ruta}' accesible desde {len(links)} enlaces diferentes.")
            # Guardar la captura de pantalla solo para una de las rutas
            if rutas_con_multiples_enlaces == 1:
                links[0].screenshot(f"multiple_links_{ruta.strip('/').replace('/', '_')}.png")
        else:
            rutas_unicas += 1

    # Evaluación final
    if rutas_con_multiples_enlaces > 0:
        print(f"Se encontraron {rutas_con_multiples_enlaces} rutas accesibles desde múltiples enlaces.")
    else:
        print("No se encontraron rutas accesibles desde múltiples enlaces.")

    print(f"Total de rutas únicas: {rutas_unicas}")

    # 11. Verificación de enlaces diferenciados para acciones especiales (descargas, nuevas ventanas)
    action_links = driver.find_elements(By.CSS_SELECTOR, 'a[target="_blank"], a[download], a[href^="javascript"], a[rel*="noopener"], a[rel*="noreferrer"], a[href*="file"], a[href*="download"], a[href*="pdf"]')

    if action_links:
        print(f"Se encontraron {len(action_links)} enlaces que ejecutan acciones especiales (descargas, abrir nuevas ventanas).")
        for link in action_links:
            link_text = link.text.strip()
            href = link.get_attribute('href')

            if not link_text:
                print(f"Advertencia: Enlace de acción especial sin texto visible. Enlace: {href}")
            else:
                print(f"Enlace de acción especial encontrado: {link_text} - Enlace: {href}")

            title_attr = link.get_attribute('title')
            aria_label = link.get_attribute('aria-label')
            if title_attr or aria_label:
                print(f"Enlace mejorado con atributos de accesibilidad: title='{title_attr}', aria-label='{aria_label}'")
    else:
        print("No se encontraron enlaces con acciones especiales diferenciadas.")

    download_links = [link for link in action_links if link.get_attribute('download')]
    new_window_links = [link for link in action_links if link.get_attribute('target') == '_blank']
    javascript_links = [link for link in action_links if link.get_attribute('href').startswith('javascript')]

    print(f"Enlaces de descarga detectados: {len(download_links)}")
    print(f"Enlaces que abren nuevas ventanas detectados: {len(new_window_links)}")
    print(f"Enlaces que ejecutan JavaScript detectados: {len(javascript_links)}")

    # 12. Verificación de enlaces "Logo" y "Inicio" para regresar a la página principal
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
                print("El logo y el botón de Inicio no llevan al usuario de vuelta a la página principal de manera consistente.")

            driver.get(logo_link.get_attribute('href'))
            if driver.current_url == logo_link.get_attribute('href'):
                print("El logo lleva correctamente a la página principal.")
            else:
                print("El logo NO lleva correctamente a la página principal.")

            driver.get(home_link.get_attribute('href'))
            if driver.current_url == home_link.get_attribute('href'):
                print("El botón de Inicio lleva correctamente a la página principal.")
            else:
                print("El botón de Inicio NO lleva correctamente a la página principal.")
        else:
            if not logo_link:
                print("No se encontró el logo que lleve a la página principal.")
            if not home_link:
                print("No se encontró el botón de Inicio que lleve a la página principal.")

    except NoSuchElementException:
        print("No se encontró el elemento de logo o botón de Inicio.")
    except Exception as e:
        print(f"Error inesperado durante la verificación: {str(e)}")

    # 13. Verificación de consistencia en la ubicación de instrucciones, preguntas y mensajes
    try:
        instruction_elements = driver.find_elements(By.CSS_SELECTOR, '.instruction, .help-text, .error-message, .hint, .validation-message')

        if instruction_elements:
            locations = set((elem.location['x'], elem.location['y']) for elem in instruction_elements)

            if len(locations) == 1:
                print("Las instrucciones, preguntas y mensajes están ubicados consistentemente en el mismo lugar en cada página.")
            else:
                print(f"Advertencia: Se encontraron {len(locations)} ubicaciones distintas para instrucciones, preguntas y mensajes.")

            for elem in instruction_elements:
                print(f"Elemento de instrucción encontrado en posición relativa X: {elem.location['x']} Y: {elem.location['y']}.")
        else:
            print("No se encontraron elementos de instrucciones, preguntas o mensajes en la página.")
    except Exception as e:
        print(f"Error al verificar la consistencia de ubicación: {str(e)}")

    # 14. Verificación de la existencia de páginas de ayuda y mensajes de error detallados
    try:
        help_pages = driver.find_elements(By.LINK_TEXT, 'Ayuda') + driver.find_elements(By.PARTIAL_LINK_TEXT, 'Help')
        error_pages = driver.find_elements(By.CSS_SELECTOR, '.error-message, .error-page, .alert-danger, .validation-error')

        if help_pages:
            print(f"Se encontraron {len(help_pages)} páginas de ayuda disponibles.")
        else:
            print("No se encontraron páginas de ayuda.")

        if error_pages:
            print(f"Se encontraron {len(error_pages)} mensajes de error detallados.")
        else:
            print("No se encontraron mensajes de error detallados.")
    except Exception as e:
        print(f"Error al verificar páginas de ayuda o mensajes de error: {str(e)}")

    # Cerrar el driver
    driver.quit()

    # --- Nuevos Criterios ---

def hdu_cuatro(url):
    response = asyncio.get_event_loop().run_until_complete(get_page(url))
    # Configurar Selenium con Chrome en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

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
            print(f"Campo de entrada '{field_name}' de tipo '{field_type}' con valor predeterminado: '{default_value}'")

            # Validar longitud del valor predeterminado
            if len(default_value) < 3 or len(default_value) > 255:
                print(f"Advertencia: El valor predeterminado para el campo '{field_name}' tiene una longitud inusual: {len(default_value)} caracteres.")

            # Validar estructura dependiendo del tipo de campo
            if field_type == 'email':
                if not re.match(r"[^@]+@[^@]+\.[^@]+", default_value):
                    print(f"Advertencia: El valor predeterminado para el campo de correo electrónico '{field_name}' no tiene una estructura válida.")

            elif field_type == 'tel':
                if not re.match(r"^\+?\d{10,15}$", default_value):
                    print(f"Advertencia: El valor predeterminado para el campo de teléfono '{field_name}' no tiene una estructura válida.")

            elif field_type == 'number':
                try:
                    float(default_value)
                except ValueError:
                    print(f"Advertencia: El valor predeterminado para el campo numérico '{field_name}' no es un número válido.")

            elif field_type == 'text' and ('date' in field_name.lower() or 'date' in field_placeholder.lower()):
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", default_value):
                    print(f"Advertencia: El valor predeterminado para el campo de fecha '{field_name}' no sigue el formato YYYY-MM-DD.")

            elif field_type == 'text' and ('currency' in field_name.lower() or 'currency' in field_placeholder.lower()):
                if not re.match(r"^\$?\d+(\.\d{2})?$", default_value):
                    print(f"Advertencia: El valor predeterminado para el campo de moneda '{field_name}' no tiene un formato de moneda válido.")

            elif field_type == 'url':
                if not re.match(r"^(https?|ftp)://[^\s/$.?#].[^\s]*$", default_value):
                    print(f"Advertencia: El valor predeterminado para el campo de URL '{field_name}' no tiene una estructura válida.")

            elif field_type == 'password':
                if len(default_value) < 8:
                    print(f"Advertencia: El valor predeterminado para el campo de contraseña '{field_name}' es demasiado corto (menor a 8 caracteres).")

            elif field_type == 'checkbox' or field_type == 'radio':
                if default_value not in ['on', 'off']:
                    print(f"Advertencia: El valor predeterminado para el campo de selección '{field_name}' tiene un valor inusual: '{default_value}'")

            # Validación adicional: campos que deberían estar vacíos
            if field_type == 'password' or field_type == 'hidden':
                if default_value:
                    print(f"Advertencia: El campo '{field_name}' de tipo '{field_type}' no debería tener un valor predeterminado visible.")
        else:
            print(f"Campo de entrada '{field_name}' de tipo '{field_type}' no tiene valor predeterminado.")

        # Verificación adicional: uso de placeholders en lugar de valores predeterminados
        if field_placeholder:
            print(f"Campo de entrada '{field_name}' con placeholder: '{field_placeholder}'")
            # Validación de longitud y formato según el placeholder
            if 'phone' in field_placeholder.lower() and not re.match(r"^\+?\d{10,15}$", default_value):
                print(f"Advertencia: El valor del placeholder '{field_placeholder}' en el campo '{field_name}' no coincide con un formato de teléfono válido.")
            elif 'date' in field_placeholder.lower() and not re.match(r"^\d{4}-\d{2}-\d{2}$", default_value):
                print(f"Advertencia: El valor del placeholder '{field_placeholder}' en el campo '{field_name}' no sigue el formato YYYY-MM-DD.")

    invalid_fields = [field for field in input_fields if not field.get_attribute('value') and not field.get_attribute('placeholder')]
    if invalid_fields:
        print(f"Advertencia: Se encontraron {len(invalid_fields)} campos de entrada sin valores predeterminados ni placeholders útiles.")

    # 16. Verificación de formateo automático de datos
    for field in input_fields:
        field_name = field.get_attribute('name')
        field_type = field.get_attribute('type')
        pattern = field.get_attribute('pattern')
        input_mode = field.get_attribute('inputmode')
        placeholder = field.get_attribute('placeholder')
        autocomplete = field.get_attribute('autocomplete')

        if pattern or input_mode:
            print(f"Campo '{field_name}' con formateo automático detectado (pattern: {pattern}, inputmode: {input_mode})")

        elif field_type == 'text' and ('currency' in (field_name or '').lower() or 'price' in (placeholder or '').lower()):
            print(f"Advertencia: El campo de moneda '{field_name}' podría beneficiarse de un patrón o inputmode para facilitar el formateo.")

        elif field_type == 'number' and not pattern:
            print(f"Advertencia: El campo numérico '{field_name}' no tiene un patrón definido para garantizar un formateo adecuado.")

        if input_mode:
            if input_mode == 'numeric' and field_type == 'text':
                print(f"Campo '{field_name}' utiliza 'inputmode=numeric' para facilitar la entrada de datos numéricos.")
            elif input_mode == 'decimal' and field_type == 'text':
                print(f"Campo '{field_name}' utiliza 'inputmode=decimal' para facilitar la entrada de números decimales.")
            else:
                print(f"Advertencia: El campo '{field_name}' tiene un inputmode '{input_mode}' que puede no ser consistente con el tipo de dato esperado.")

        if autocomplete:
            print(f"Campo '{field_name}' tiene habilitado el autocompletado con 'autocomplete={autocomplete}'.")

    critical_fields = [field for field in input_fields if 'currency' in (field.get_attribute('name') or '').lower() or 'phone' in (field.get_attribute('name') or '').lower()]
    if critical_fields:
        print(f"Se encontraron {len(critical_fields)} campos críticos que requieren formateo automático.")
        for field in critical_fields:
            pattern = field.get_attribute('pattern')
            if not pattern:
                print(f"Advertencia: El campo crítico '{field.get_attribute('name')}' no tiene un patrón definido para formateo.")

    # 17. Detección de Etiquetas para Campos Requeridos y Opcionales
    palabras_clave_requerido = ['required', 'obligatorio', 'necesario', '*', 'must', 'mandatory']
    palabras_clave_opcional = ['optional', 'opcional']
    labels = driver.find_elements(By.CSS_SELECTOR, 'label')
    for label in labels:
        text = label.text.lower()

        if any(palabra in text for palabra in palabras_clave_requerido):
            print(f"Etiqueta de campo requerido detectada: {text}")
        elif any(palabra in text for palabra in palabras_clave_opcional):
            print(f"Etiqueta de campo opcional detectada: {text}")
        else:
            for_attr = label.get_attribute('for')
            associated_input = driver.find_element(By.ID, for_attr) if for_attr else None

            if associated_input:
                if associated_input.get_attribute('required'):
                    print(f"Campo asociado a la etiqueta '{text}' es requerido basado en el atributo 'required'.")
                elif associated_input.get_attribute('aria-required') == 'true':
                    print(f"Campo asociado a la etiqueta '{text}' es requerido basado en 'aria-required=true'.")
                else:
                    print(f"Campo asociado a la etiqueta '{text}' no indica si es requerido u opcional.")
            else:
                print(f"Advertencia: No se encontró un campo asociado para la etiqueta '{text}'.")

    input_fields = driver.find_elements(By.CSS_SELECTOR, 'input, textarea, select')
    for field in input_fields:
        aria_label = field.get_attribute('aria-label')
        placeholder = field.get_attribute('placeholder')
        field_name = field.get_attribute('name')

        if field.get_attribute('required') or field.get_attribute('aria-required') == 'true':
            if aria_label:
                print(f"Campo '{aria_label}' es requerido basado en atributos ARIA.")
            elif placeholder:
                print(f"Campo con placeholder '{placeholder}' es requerido basado en atributos HTML.")
            else:
                print(f"Campo '{field_name}' es requerido pero no tiene una etiqueta visible asociada.")
        elif 'optional' in (aria_label or '').lower() or 'optional' in (placeholder or '').lower():
            print(f"Campo '{aria_label or placeholder}' es opcional.")

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
            print(f"Campo de tipo {field_type} con tamaño adecuado ({size}px de ancho).")
        else:
            print(f"Advertencia: Campo de tipo {field_type} con tamaño insuficiente ({size}px de ancho).")

        if max_length:
            print(f"Campo de tipo {field_type} tiene un 'maxlength' de {max_length}.")
        if min_length:
            print(f"Campo de tipo {field_type} tiene un 'minlength' de {min_length}.")

        default_value = field.get_attribute('value') or ''
        if len(default_value) > 0 and size < len(default_value) * 8:
            print(f"Advertencia: El valor predeterminado podría no ser completamente visible en el campo ({size}px de ancho).")

        if placeholder and size < len(placeholder) * 8:
            print(f"Advertencia: El placeholder '{placeholder}' podría no ser completamente visible en el campo ({size}px de ancho).")

    print("Verificación del tamaño de las cajas de texto completada.")

    # 19. Verificación de uso de listas de opciones, botones de radio y casillas en lugar de cajas de texto
    select_fields = driver.find_elements(By.TAG_NAME, 'select')
    radio_buttons = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
    checkboxes = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')

    if select_fields:
        print(f"Se encontraron {len(select_fields)} listas de opciones.")
    else:
        print("No se encontraron listas de opciones.")

    if radio_buttons:
        print(f"Se encontraron {len(radio_buttons)} botones de radio.")
    else:
        print("No se encontraron botones de radio.")

    if checkboxes:
        print(f"Se encontraron {len(checkboxes)} casillas de verificación.")
    else:
        print("No se encontraron casillas de verificación.")

    if not select_fields and not radio_buttons and not checkboxes:
        print("Advertencia: No se encontraron listas de opciones, botones de radio o casillas de verificación, revisa si se está utilizando adecuadamente cajas de texto.")

    # 20. Verificación de posición automática del cursor en el campo adecuado
    focused_element = driver.switch_to.active_element
    if focused_element:
        field_name = focused_element.get_attribute('name') or focused_element.get_attribute('id')
        field_type = focused_element.get_attribute('type')

        form_elements = driver.find_elements(By.CSS_SELECTOR, 'input, select, textarea')
        first_relevant_element = form_elements[0] if form_elements else None

        if first_relevant_element and first_relevant_element == focused_element:
            print(f"El cursor está correctamente posicionado en el primer campo relevante: {field_name} de tipo {field_type}.")
        else:
            print(f"Advertencia: El cursor está en el campo: {field_name}, pero podría no ser el primer campo relevante.")
    else:
        print("No se detectó que el cursor esté posicionado automáticamente en un campo.")

    # 21. Verificación de formatos claramente indicados en campos de entrada
    for field in input_fields:
        placeholder = field.get_attribute('placeholder')
        pattern = field.get_attribute('pattern')
        input_mode = field.get_attribute('inputmode')
        title = field.get_attribute('title')
        aria_label = field.get_attribute('aria-label')

        if placeholder:
            print(f"Campo con formato sugerido mediante placeholder: {placeholder}")

        if pattern:
            print(f"Campo con validación mediante patrón: {pattern}")

        if input_mode:
            print(f"Campo con sugerencia de input mode: {input_mode}")

        if title:
            print(f"Campo con formato descrito en el título: {title}")

        if aria_label:
            print(f"Campo con indicación de formato en aria-label: {aria_label}")

        if not any([placeholder, pattern, input_mode, title, aria_label]):
            print(f"Advertencia: El campo {field.get_attribute('name') or field.get_attribute('id')} no tiene una indicación clara de formato.")

    # 22. Validación automática de formularios
    forms = driver.find_elements(By.TAG_NAME, 'form')
    for form in forms:
        if not form.get_attribute('novalidate'):
            form_id_or_name = form.get_attribute('id') or form.get_attribute('name')
            if form_id_or_name:
                print(f"Formulario con validación automática detectado: {form_id_or_name}")
            else:
                print("Formulario sin ID o nombre específico detectado, pero con validación automática.")
        else:
            print("Formulario sin validación automática detectado.")

    # 23. Verificación de validación en tiempo real de los campos de entrada
    for field in input_fields:
        outer_html = field.get_attribute('outerHTML')
        if any(event in outer_html for event in ['oninput', 'onchange', 'onblur']) or \
          any(attr in field.get_attribute('outerHTML') for attr in ['pattern', 'required', 'maxlength']):
            field_name_or_id = field.get_attribute('name') or field.get_attribute('id')
            if field_name_or_id:
                print(f"Campo con validación en tiempo real detectado: {field_name_or_id}")
            else:
                print("Campo sin ID o nombre específico detectado, pero con validación en tiempo real.")

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

                    print(f"Etiqueta '{label.text}' está a {vertical_distance}px verticalmente y a {horizontal_distance}px horizontalmente de su campo asociado.")
                else:
                    print(f"Campo asociado con ID '{associated_field_id}' no está visible.")
            except NoSuchElementException:
                print(f"No se encontró el campo con ID '{associated_field_id}' asociado a la etiqueta '{label.text}'.")
        else:
            print(f"La etiqueta '{label.text}' no está asociada con ningún campo.")

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
                            print(f"El campo '{field_name_or_id}' permite cambiar el valor predeterminado.")
                        else:
                            print(f"El campo '{field_name_or_id}' NO permite cambiar el valor predeterminado, cambio fallido.")
                    else:
                        print(f"El campo '{field_name_or_id}' no es un tipo de campo editable (tipo {field.get_attribute('type')}).")
                except Exception as interaction_error:
                    print(f"Hubo un problema al intentar cambiar el valor del campo '{field_name_or_id}': {interaction_error}")

                # Intentar restaurar el valor original si fue cambiado
                try:
                    if field.get_attribute('type') in ['text', 'email', 'password', 'search', 'tel', 'url']:
                        field.clear()
                        field.send_keys(original_value)
                except Exception as restore_error:
                    print(f"Hubo un problema al intentar restaurar el valor original del campo '{field_name_or_id}': {restore_error}")
            else:
                print(f"El campo '{field_name_or_id}' está deshabilitado, es de solo lectura, no es visible, o no es un campo de entrada.")
        except Exception as e:
            print(f"Hubo un problema al interactuar con el campo '{field_name_or_id}': {e}")



    # Cerrar el driver
    driver.quit()

    ################################ Aqui va el C.A 1 de la H.U 1.5 ##########################################

def hdu_cinco(url):
    response = asyncio.get_event_loop().run_until_complete(get_page(url))
    # Configurar Selenium con Chrome en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Navegar a la URL
    driver.get(url)

    # 27. Detección de anuncios y pop-ups
    driver.implicitly_wait(5)

    # Selección ampliada para detectar varios tipos de anuncios y pop-ups
    ads_selectors = [
        '[class*="ad"]', '[id*="ad"]', '[class*="pop"]', '[id*="pop"]',
        '[class*="banner"]', '[id*="banner"]', '[class*="promo"]', '[id*="promo"]',
        '[class*="modal"]', '[id*="modal"]', '[class*="overlay"]', '[id*="overlay"]',
        '[class*="sponsor"]', '[id*="sponsor"]'
    ]
    ads = []

    for selector in ads_selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for element in elements:
            if element.is_displayed():
                ads.append(element)

    # Cambio de contexto para buscar en iframes si es necesario
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    for iframe in iframes:
        driver.switch_to.frame(iframe)
        for selector in ads_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed():
                    ads.append(element)
        driver.switch_to.default_content()

    # Resultado de la detección
    if ads:
        print(f"Se detectaron {len(ads)} anuncios o pop-ups en la página.")
    else:
        print("No se detectaron anuncios ni pop-ups.")

    # 28. Verificación de la presencia del logo en cada página
    logo_selectors = [
        'a.logo', 'img[alt*="logo"]', '[class*="logo"]', '[id*="logo"]',
        'img[src*="logo"]', '[class*="header-logo"]', '[class*="site-logo"]', '[class*="brand-logo"]'
    ]

    logo_elements = []
    for selector in logo_selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for element in elements:
            if element.is_displayed():
                logo_elements.append(element)

    # Cambio de contexto para buscar logos en iframes si es necesario
    for iframe in iframes:
        driver.switch_to.frame(iframe)
        for selector in logo_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed():
                    logo_elements.append(element)
        driver.switch_to.default_content()

    # Resultado de la verificación
    if logo_elements:
        print("El logo de la marca aparece en la página.")
    else:
        print("El logo de la marca NO aparece en la página.")

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

    if found_errors:
        print(f"Se detectaron errores tipográficos u ortográficos: {found_errors}")
    else:
        print("No se detectaron errores tipográficos u ortográficos.")


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
        print(f"Se encontraron {len(lists)} listas (viñetas, numeradas o de definiciones) en la página.")
    else:
        print("No se encontraron listas en la página, posible uso excesivo de texto narrativo.")


    # 31. Evaluación de la Jerarquía del Contenido mediante Encabezados (H1, H2, etc.)
    headers = driver.find_elements(By.CSS_SELECTOR, 'h1, h2, h3, h4, h5, h6')
    if headers:
        last_level = 0
        hierarchy_correct = True
        for header in headers:
            header_text = header.text.strip()
            if header.is_displayed() and header_text:
                current_level = int(header.tag_name[1])
                print(f"Encabezado {header.tag_name.upper()} encontrado: {header_text}")

                # Verificar jerarquía
                if current_level > last_level + 1:
                    print(f"Advertencia: El encabezado {header.tag_name.upper()} parece estar fuera de orden jerárquico.")
                    hierarchy_correct = False

                last_level = current_level
            else:
                print(f"Encabezado {header.tag_name.upper()} encontrado, pero está vacío o no es visible.")

        if hierarchy_correct:
            print("La jerarquía de encabezados está presente y parece correcta.")
        else:
            print("Se detectaron posibles problemas en la jerarquía de encabezados.")
    else:
        print("No se encontraron encabezados, posible falta de estructura jerárquica en el contenido.")


    # 32. Análisis de la Estructura de las Páginas para Mejorar la Legibilidad
    large_titles = driver.find_elements(By.CSS_SELECTOR, 'h1')
    subtitles = driver.find_elements(By.CSS_SELECTOR, 'h2, h3, h4')
    paragraphs = driver.find_elements(By.CSS_SELECTOR, 'p')

    # Verificar la presencia y cantidad de elementos
    if large_titles and subtitles and paragraphs:
        # Verificar la longitud de los párrafos
        long_paragraphs = [p for p in paragraphs if len(p.text.split()) > 100]  # Umbral de 100 palabras por párrafo

        if long_paragraphs:
            print(f"Se detectaron {len(long_paragraphs)} párrafos largos. Considera dividirlos para mejorar la legibilidad.")
        else:
            print("Los párrafos son cortos y adecuados para la legibilidad.")

        print("La página contiene títulos grandes, subtítulos y párrafos cortos, lo que mejora la legibilidad.")
    else:
        print("La estructura de la página podría no estar optimizada para la legibilidad.")


    # 33. Análisis de la Longitud y Descriptividad de Títulos y Subtítulos
    # Análisis de títulos
    for title in large_titles:
        title_length = len(title.text)
        if title_length > title_threshold:
            print(f"Título largo detectado: {title.text} (longitud: {title_length} caracteres).")
        elif not is_descriptive(title.text):
            print(f"Título genérico o poco descriptivo detectado: {title.text}")
        else:
            print(f"Título descriptivo adecuado: {title.text}")

    # Análisis de subtítulos
    for subtitle in subtitles:
        subtitle_length = len(subtitle.text)
        if subtitle_length > title_threshold:
            print(f"Subtítulo largo detectado: {subtitle.text} (longitud: {subtitle_length} caracteres).")
        elif not is_descriptive(subtitle.text):
            print(f"Subtítulo genérico o poco descriptivo detectado: {subtitle.text}")
        else:
            print(f"Subtítulo descriptivo adecuado: {subtitle.text}")

    # 34. Detección de Listas Numeradas para Verificar que Comienzan en "1"
    numbered_lists = driver.find_elements(By.CSS_SELECTOR, 'ol')
    for ol in numbered_lists:
        if ol.get_attribute('start') and ol.get_attribute('start') != '1':
            print(f"Lista numerada que no comienza en 1 detectada: {ol.get_attribute('start')}")
        else:
            print("Todas las listas numeradas comienzan en 1.")

    # Cerrar el driver
    driver.quit()

def hdu_seis(url):
    response = asyncio.get_event_loop().run_until_complete(get_page(url))
    # Configurar Selenium con Chrome en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Navegar a la URL
    driver.get(url)

    # 35. Detección de Listas y Viñetas
    lists = driver.find_elements(By.CSS_SELECTOR, 'ul, ol')
    if lists:
        print(f"Se encontraron {len(lists)} listas (viñetas o numeradas) en la página.")
    else:
        print("No se encontraron listas en la página, posible uso excesivo de texto narrativo.")

    # 36. Evaluación de la Jerarquía del Contenido mediante Encabezados (H1, H2, etc.)
    headers = driver.find_elements(By.CSS_SELECTOR, 'h1, h2, h3, h4, h5, h6')
    if headers:
        for header in headers:
            print(f"Encabezado {header.tag_name.upper()} encontrado: {header.text}")
        print("La jerarquía de encabezados está presente.")
    else:
        print("No se encontraron encabezados, posible falta de estructura jerárquica en el contenido.")

    # 37. Análisis de la Estructura de las Páginas para Mejorar la Legibilidad
    large_titles = driver.find_elements(By.CSS_SELECTOR, 'h1')
    subtitles = driver.find_elements(By.CSS_SELECTOR, 'h2, h3')
    paragraphs = driver.find_elements(By.CSS_SELECTOR, 'p')

    if large_titles and subtitles and paragraphs:
        print("La página contiene títulos grandes, subtítulos y párrafos cortos, lo que mejora la legibilidad.")
    else:
        print("La estructura de la página podría no estar optimizada para la legibilidad.")

    # 38. Análisis de la Longitud y Descriptividad de Títulos y Subtítulos
    for title in large_titles:
        if len(title.text) > 60:
            print(f"Título largo detectado: {title.text} (longitud: {len(title.text)} caracteres).")
        else:
            print(f"Título descriptivo adecuado: {title.text}")

    for subtitle in subtitles:
        if len(subtitle.text) > 60:
            print(f"Subtítulo largo detectado: {subtitle.text} (longitud: {len(subtitle.text)} caracteres).")
        else:
            print(f"Subtítulo descriptivo adecuado: {subtitle.text}")

    # Cerrar el driver
    driver.quit()

def hdu_siete(url):
    response = asyncio.get_event_loop().run_until_complete(get_page(url))
    # Configurar Selenium con Chrome en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Navegar a la URL
    driver.get(url)

    # 40. Consistencia en el Uso de Fuentes
    fonts = driver.find_elements(By.CSS_SELECTOR, '*[style*="font-family"]')
    font_families = {font.value_of_css_property('font-family') for font in fonts}
    if len(font_families) > 1:
        print(f"Se encontraron múltiples fuentes utilizadas en el sitio: {', '.join(font_families)}")
    else:
        print(f"Uso consistente de la fuente: {next(iter(font_families), 'No se encontraron fuentes especificadas')}")

    # 41. Verificación de Desplazamiento Horizontal
    body = driver.find_element(By.TAG_NAME, 'body')
    body_width = body.size['width']
    viewport_width = driver.execute_script("return window.innerWidth")

    if body_width > viewport_width:
        print("Se requiere desplazamiento horizontal, lo cual no es deseado.")

        # Identificación de elementos que causan desbordamiento
        elements = driver.find_elements(By.XPATH, "//*[self::div or self::section or self::img or self::table]")
        for element in elements:
            if element.size['width'] > viewport_width:
                print(f"Elemento desbordante detectado: {element.tag_name}, tamaño: {element.size['width']}px")
    else:
        print("No se requiere desplazamiento horizontal.")

    # 42. Detección de Enlaces Subrayados o con Indicación Visual Clara
    links = driver.find_elements(By.TAG_NAME, 'a')
    for link in links:
        link_text = link.text.strip()
        if link.is_displayed() and link_text:
            text_decoration = link.value_of_css_property('text-decoration')
            font_weight = link.value_of_css_property('font-weight')
            color = link.value_of_css_property('color')
            border_bottom = link.value_of_css_property('border-bottom')

            # Verificar si el enlace tiene una indicación visual clara
            if 'underline' in text_decoration or int(font_weight) >= 700 or 'solid' in border_bottom:
                print(f"Enlace con indicación visual clara: {link_text}")
            else:
                print(f"Enlace sin indicación visual clara: {link_text}")
        else:
            print("Enlace vacío o no visible encontrado.")

    # 43. Revisión de la Legibilidad de las Fuentes (Tamaño y Contraste)
    text_elements = driver.find_elements(By.CSS_SELECTOR, 'body *')
    for elem in text_elements:
        font_size = elem.value_of_css_property('font-size')
        color = elem.value_of_css_property('color')
        background_color = elem.value_of_css_property('background-color')
        print(f"Elemento con tamaño de fuente {font_size}, color {color}, fondo {background_color}")

    # 44. Análisis del Uso de Mayúsculas Mejorado
    def es_acronimo_o_sigla(texto):
        # Filtra palabras que podrían ser acrónimos o siglas comunes
        return all(c.isupper() for c in texto) and len(texto) <= 5  # Suponemos que un acrónimo tiene <= 5 letras

    capitalized_texts = driver.find_elements(By.XPATH, "//*[text()[contains(.,' ')] and string-length(text()) > 10 and translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ') = text()]")
    textos_sospechosos = []

    if capitalized_texts:
        for elem in capitalized_texts:
            texto = elem.text.strip()

            # Filtrar títulos o encabezados
            if elem.tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong']:
                print(f"Título o encabezado en mayúsculas detectado (posiblemente aceptable): {texto}")

            # Filtrar siglas o acrónimos
            elif any(es_acronimo_o_sigla(palabra) for palabra in texto.split()):
                print(f"Posible uso correcto de mayúsculas para acrónimo/sigla detectado: {texto}")

            # Verificar el contexto del uso de mayúsculas
            elif len(texto) > 20 and len(texto.split()) > 3:  # Suponiendo que el abuso puede ser más largo
                textos_sospechosos.append(texto)
            else:
                print(f"Texto en mayúsculas detectado: {texto}")

        # Evaluar la frecuencia del uso de mayúsculas
        if len(textos_sospechosos) > 3:  # Si se detectan más de 3 casos, podría ser un abuso
            print(f"Advertencia: Se detectaron múltiples casos de textos en mayúsculas que podrían indicar un abuso: {textos_sospechosos}")
        else:
            print("No se detectaron abusos en el uso de mayúsculas.")
    else:
        print("No se detectaron abusos en el uso de mayúsculas.")

    # 45. Consistencia en el Uso de Patrones de Color
    color_elements = driver.find_elements(By.CSS_SELECTOR, '*[style*="background-color"], *[style*="color"]')
    colors_text = {elem.value_of_css_property('color') for elem in color_elements if elem.value_of_css_property('color')}
    colors_background = {elem.value_of_css_property('background-color') for elem in color_elements if elem.value_of_css_property('background-color')}

    # Combinación de colores de texto y de fondo
    all_colors = colors_text.union(colors_background)

    if len(all_colors) > 3:  # Ajustar según el número esperado de colores consistentes
        print(f"Se encontraron múltiples patrones de color en el sitio: {', '.join(all_colors)}")
    else:
        print(f"Uso consistente de colores: {', '.join(all_colors)}")

    # 46. Análisis del Uso de Cursiva y Subrayado
    italic_elements = driver.find_elements(By.CSS_SELECTOR, 'i, em, *[style*="italic"]')
    underlined_elements = driver.find_elements(By.CSS_SELECTOR, 'u, *[style*="underline"]')

    if italic_elements:
        for elem in italic_elements:
            print(f"Elemento en cursiva detectado: {elem.tag_name} con texto '{elem.text}'")

    if underlined_elements:
        for elem in underlined_elements:
            if elem.tag_name != 'a':  # Evitar confusión con enlaces
                print(f"Advertencia: Elemento subrayado detectado que no es un enlace: {elem.tag_name} con texto '{elem.text}'")

    # 47. Medición de la Longitud de las Líneas de Texto
    paragraphs = driver.find_elements(By.CSS_SELECTOR, 'p')

    for paragraph in paragraphs:
        line_lengths = [len(line.strip()) for line in paragraph.text.split('\n')]
        for line_length in line_lengths:
            if 50 <= line_length <= 100:
                print(f"Línea de texto con longitud adecuada: {line_length} caracteres")
            else:
                print(f"Advertencia: Línea de texto con longitud inadecuada: {line_length} caracteres")

    # 48. Análisis de la Alineación de Ítems en el Diseño
    elements = driver.find_elements(By.CSS_SELECTOR, 'body *')

    for elem in elements:
        text_align = elem.value_of_css_property('text-align')
        vertical_align = elem.value_of_css_property('vertical-align')
        display_type = elem.value_of_css_property('display')

        print(f"Elemento con alineación: horizontal - {text_align}, vertical - {vertical_align}, display - {display_type}")

        # Evaluar si hay desalineación basada en las posiciones absolutas
        pos_x = elem.location['x']
        pos_y = elem.location['y']
        if pos_x % 10 != 0 or pos_y % 10 != 0:  # Suponiendo que debería estar alineado en múltiplos de 10px
            print(f"Advertencia: Elemento desalineado en posición ({pos_x}, {pos_y})")

    # 49. Verificación de la Interactividad de Elementos Clickeables
    clickable_elements = driver.find_elements(By.CSS_SELECTOR, 'button, a, input[type="submit"], input[type="button"]')
    for elem in clickable_elements:
        if elem.is_enabled():
            print(f"Elemento clickeable detectado: {elem.tag_name} con texto {elem.text} está interactuable.")
        else:
            print(f"Elemento clickeable detectado: {elem.tag_name} con texto {elem.text} NO está interactuable.")

    # 50. Análisis del Uso de Negrita en el Texto
    bold_elements = driver.find_elements(By.CSS_SELECTOR, 'b, strong, *[style*="bold"]')
    if bold_elements:
        print(f"Se encontraron {len(bold_elements)} elementos en negrita.")

    # 51. Análisis del Contraste de Colores y Combinación
    elements = driver.find_elements(By.CSS_SELECTOR, 'body *')
    for elem in elements:
        color = elem.value_of_css_property('color')
        background_color = elem.value_of_css_property('background-color')

        # Convertir los colores a tuplas RGB
        if color.startswith('rgb'):
            color = rgb_or_rgba_to_tuple(color)
        if background_color.startswith('rgb'):
            background_color = rgb_or_rgba_to_tuple(background_color)

        # Calcular el contraste si ambos colores están en formato RGB
        if isinstance(color, tuple) and isinstance(background_color, tuple):
            contrast = calculate_contrast(color, background_color)
            print(f"Elemento con color {color} y fondo {background_color} tiene un contraste de {contrast:.2f}")
        else:
            print(f"No se pudo calcular el contraste para el elemento con color {color} y fondo {background_color}")

    # Cerrar el driver
    driver.quit()

def hdu_ocho(url):
    response = asyncio.get_event_loop().run_until_complete(get_page(url))
    # Configurar Selenium con Chrome en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Navegar a la URL
    driver.get(url)

    # 52. Confirmación de Términos de Búsqueda y Opciones de Edición
    try:
        search_terms = driver.find_element(By.CSS_SELECTOR, '.search-terms')
        if search_terms.is_displayed():
            print(f"Términos de búsqueda mostrados: {search_terms.text}")
            edit_button = driver.find_element(By.CSS_SELECTOR, '.edit-search')
            if edit_button.is_displayed():
                try:
                    edit_button.click()
                    print("Opción para editar y reenviar los criterios de búsqueda disponible y funcional.")
                except Exception as e:
                    print(f"Advertencia: El botón de edición no respondió al clic. Error: {e}")
        else:
            print("Advertencia: Los términos de búsqueda no son visibles.")
    except NoSuchElementException:
        print("Los términos de búsqueda no se muestran o no hay opción para editar y reenviar.")

    # 53. Evaluación de la Clasificación de Resultados por Relevancia
    try:
        results = driver.find_elements(By.CSS_SELECTOR, '.search-result')
        if results:
            for i, result in enumerate(results):
                print(f"Resultado {i+1}: {result.text[:50]}...")  # Mostrar parte del resultado para identificar
            print(f"Resultados clasificados por relevancia: {len(results)} resultados encontrados.")
        else:
            print("No se encontraron resultados clasificados por relevancia.")
    except NoSuchElementException:
        print("No se encontraron resultados clasificados por relevancia.")

    # 54. Comprobación del Número Total de Resultados y Configuración de Resultados por Página
    try:
        total_results = driver.find_element(By.CSS_SELECTOR, '.total-results')
        if total_results.is_displayed():
            print(f"Número total de resultados mostrado: {total_results.text}")
            per_page_options = driver.find_element(By.CSS_SELECTOR, '.results-per-page')
            if per_page_options.is_displayed():
                try:
                    per_page_options.click()
                    print("Opción para configurar el número de resultados por página disponible y funcional.")
                except Exception as e:
                    print(f"Advertencia: La opción para configurar los resultados por página no respondió al clic. Error: {e}")
            else:
                print("Advertencia: La opción para configurar los resultados por página no es visible.")
        else:
            print("Advertencia: El número total de resultados no es visible.")
    except NoSuchElementException:
        print("No se muestra el número total de resultados o no hay opción para configurar los resultados por página.")

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
            print("El motor de búsqueda maneja correctamente las búsquedas sin entrada, mostrando un mensaje adecuado.")
        else:
            print("Advertencia: El motor de búsqueda no maneja adecuadamente las búsquedas sin entrada.")
    except NoSuchElementException:
        print("El motor de búsqueda no maneja correctamente las búsquedas sin entrada o elementos no encontrados.")

    # 56. Comprobación del Etiquetado Claro de la Caja de Búsqueda y Controles
    try:
        search_box_label = driver.find_element(By.CSS_SELECTOR, 'label[for="search-box"], [aria-label="search"]')

        if search_box_label.is_displayed():
            print(f"Caja de búsqueda claramente etiquetada: {search_box_label.text or search_box_label.get_attribute('aria-label')}")
        else:
            print("Advertencia: La etiqueta de la caja de búsqueda no es visible.")
    except NoSuchElementException:
        print("La caja de búsqueda o sus controles no están claramente etiquetados.")

    # 57. Verificación de Opciones para Encontrar Contenido Relacionado
    try:
        related_content = driver.find_element(By.CSS_SELECTOR, '.related-searches')

        if related_content.is_displayed():
            related_links = related_content.find_elements(By.TAG_NAME, 'a')
            print(f"Opciones para encontrar contenido relacionado disponibles: {len(related_links)} enlaces encontrados.")
        else:
            print("Advertencia: Las opciones para encontrar contenido relacionado no son visibles.")
    except NoSuchElementException:
        print("No se ofrecen opciones para encontrar contenido relacionado.")

    # 58. Evaluación de Opciones de Navegación y Búsqueda
    try:
        navigation_menu = driver.find_element(By.CSS_SELECTOR, '.navigation-menu')
        search_box = driver.find_element(By.CSS_SELECTOR, '.search-box')

        if navigation_menu.is_displayed() and search_box.is_displayed():
            print("El sitio ofrece opciones tanto para la navegación como para la búsqueda.")
        else:
            print("Advertencia: Las opciones de navegación o búsqueda no son visibles.")
    except NoSuchElementException:
        print("El sitio no ofrece opciones adecuadas para la navegación o la búsqueda.")

    # 59. Verificación de la Ausencia de Resultados Duplicados o Similares
    try:
        result_titles = [result.text for result in driver.find_elements(By.CSS_SELECTOR, '.result-title')]
        duplicates = [title for title in result_titles if result_titles.count(title) > 1]

        if duplicates:
            print(f"Advertencia: Resultados duplicados encontrados: {', '.join(set(duplicates))}")
        else:
            print("No se encontraron resultados duplicados o muy similares.")
    except NoSuchElementException:
        print("No se pudo verificar la existencia de resultados duplicados o similares.")

    # Cerrar el driver
    driver.quit()

def hdu_nueve(url):
    response = asyncio.get_event_loop().run_until_complete(get_page(url))
    # Configurar Selenium con Chrome en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Medición del tiempo de carga de la página
    start_time = time.time()
    driver.get(url)
    load_time = time.time() - start_time
    if load_time <= 5:
        print(f"La página se cargó en {load_time:.2f} segundos, dentro del límite aceptable.")
    else:
        print(f"Advertencia: La página tardó {load_time:.2f} segundos en cargar, excediendo el límite de 5 segundos.")

    # 61. Comprobación del Tamaño de la Caja de Búsqueda
    try:
        search_box = driver.find_element(By.CSS_SELECTOR, '.search-box')
        search_box_width = search_box.size['width']

        if search_box_width >= 300:
            print(f"La caja de búsqueda es lo suficientemente grande: {search_box_width}px de ancho.")
        else:
            print(f"Advertencia: La caja de búsqueda es pequeña: {search_box_width}px de ancho.")
    except NoSuchElementException:
        print("No se pudo encontrar la caja de búsqueda para verificar su tamaño.")

    # 62. Verificación del Espaciado y Tamaño de los Elementos Clickeables
    clickable_elements = driver.find_elements(By.CSS_SELECTOR, 'button, a, input[type="submit"], input[type="button"]')
    for elem in clickable_elements:
        size = elem.size
        location = elem.location
        if size['width'] >= 44 and size['height'] >= 44:
            print(f"Elemento clickeable de tamaño adecuado: {elem.tag_name} con tamaño {size['width']}x{size['height']}.")
        else:
            print(f"Advertencia: Elemento clickeable pequeño: {elem.tag_name} con tamaño {size['width']}x{size['height']}.")

        # Verificación de espaciado alrededor
        elements_around = driver.find_elements(By.XPATH, f"//body//*[not(self::script)][not(self::style)][contains(@style, 'position: absolute') and not(contains(@class, 'ignored'))]")
        for nearby_elem in elements_around:
            nearby_location = nearby_elem.location
            if abs(location['x'] - nearby_location['x']) < 20 and abs(location['y'] - nearby_location['y']) < 20:
                print(f"Advertencia: Elemento clickeable {elem.tag_name} podría tener un espaciado insuficiente.")

    # 63. Verificación de la Presencia y Adecuación de la Ayuda Contextual
    try:
        help_elements = driver.find_elements(By.CSS_SELECTOR, '.help, .tooltip, .hint, [title], [aria-label]')
        visible_help_elements = [elem for elem in help_elements if elem.is_displayed()]

        if visible_help_elements:
            print(f"Se encontraron {len(visible_help_elements)} elementos de ayuda contextual visibles.")
            for elem in visible_help_elements:
                intentos = 3  # Intentar manejar el error de referencia obsoleta
                while intentos > 0:
                    try:
                        elem = driver.find_element(By.XPATH, f"//*[@title='{elem.get_attribute('title')}'] | //*[@aria-label='{elem.get_attribute('aria-label')}']")
                        elem.click()
                        print(f"Elemento de ayuda '{elem.get_attribute('title') or elem.text}' es funcional.")
                        break
                    except StaleElementReferenceException:
                        intentos -= 1
                        if intentos == 0:
                            print(f"Advertencia: El elemento de ayuda '{elem.get_attribute('title') or elem.text}' ya no es válido en el DOM después de múltiples intentos.")
                    except Exception as e:
                        print(f"Advertencia: El elemento de ayuda '{elem.get_attribute('title') or elem.text}' no respondió al clic. Error: {e}")
                        break
        else:
            print("No se encontró ayuda contextual visible en la página.")
    except NoSuchElementException:
        print("Error al buscar elementos de ayuda contextual.")

    # 64. Revisión de Enlaces y Textos Descriptivos para Evitar Texto Genérico
    generic_phrases = ["Click aquí", "Más información", "Haz clic aquí", "Leer más", "Ver detalles"]
    links = driver.find_elements(By.TAG_NAME, 'a')

    for link in links:
        link_text = link.text.strip()
        if not link_text:
            print("Advertencia: Enlace sin texto visible o solo con espacios detectado.")
        else:
            if any(phrase.lower() in link_text.lower() for phrase in generic_phrases):
                print(f"Advertencia: Enlace con texto genérico encontrado: {link_text}")
            else:
                print(f"Enlace con texto descriptivo adecuado: {link_text}")

            title_attr = link.get_attribute('title')
            aria_label = link.get_attribute('aria-label')
            if title_attr or aria_label:
                print(f"Enlace mejorado con atributo de accesibilidad: title='{title_attr}', aria-label='{aria_label}'")

    # Cerrar el driver
    driver.quit()

# Ejecutar el análisis en una URL específica
print("------------------------------------------HISTORIA DE USUARIO 1.1------------------------------------------")
hdu_uno('http://www.cantinachichilo.com.ar/')
print("------------------------------------------HISTORIA DE USUARIO 1.2------------------------------------------")
hdu_dos('http://www.cantinachichilo.com.ar/')
print("------------------------------------------HISTORIA DE USUARIO 1.3------------------------------------------")
hdu_tres('http://www.cantinachichilo.com.ar/')
print("------------------------------------------HISTORIA DE USUARIO 1.4------------------------------------------")
hdu_cuatro('http://www.cantinachichilo.com.ar/')
print("------------------------------------------HISTORIA DE USUARIO 1.5------------------------------------------")
hdu_cinco('http://www.cantinachichilo.com.ar/')
print("------------------------------------------HISTORIA DE USUARIO 1.6------------------------------------------")
hdu_seis('http://www.cantinachichilo.com.ar/')
print("------------------------------------------HISTORIA DE USUARIO 1.7------------------------------------------")
hdu_siete('http://www.cantinachichilo.com.ar/')
print("------------------------------------------HISTORIA DE USUARIO 1.8------------------------------------------")
hdu_ocho('http://www.cantinachichilo.com.ar/')
print("------------------------------------------HISTORIA DE USUARIO 1.9------------------------------------------")
hdu_nueve('http://www.cantinachichilo.com.ar/')

