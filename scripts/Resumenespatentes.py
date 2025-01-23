from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import tempfile
import time
from pymongo import MongoClient
import re

# Conexión a la base de datos MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Proyecto"]
coleccion = db["patentes"]

def obtener_resumen_contenido_dinamico(url_universidad):
    driver = None
    temp_dir = None
    try:
        print(f"\nIntentando acceder a URL: {url_universidad}")
        
        # Crear un directorio temporal único
        temp_dir = tempfile.mkdtemp(prefix='chrome_', dir=os.path.expanduser('~'))

        # Configurar el navegador con opciones mejoradas
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"--user-data-dir={temp_dir}")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.binary_location = "/usr/bin/chromium-browser"

        # Configurar el servicio
        CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
        if not os.path.exists(CHROMEDRIVER_PATH):
            raise FileNotFoundError(f"No se encontró ChromeDriver en la ruta: {CHROMEDRIVER_PATH}")
        service = Service(CHROMEDRIVER_PATH)

        # Iniciar el navegador
        driver = webdriver.Chrome(service=service, options=options)
        
        # Asegurar que la URL comienza con http/https
        if not url_universidad.startswith(('http://', 'https://')):
            url_universidad = 'https://' + url_universidad
        
        # Pequeña pausa antes de cargar la URL
        time.sleep(2)
        
        # Acceder a la URL
        driver.get(url_universidad)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Procesar según el dominio
        if "consultas2.oepm.es" in url_universidad:
            print("Detectado dominio OEPM")
            time.sleep(5)
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser', from_encoding='utf-8')

            tables = soup.find_all('table')
            print(f"Encontradas {len(tables)} tablas")
            for table in tables:
                resumen_cell = table.find(string=lambda text: text and "Resumen" in text)
                if resumen_cell:
                    texto_resumen = resumen_cell.find_next('td')
                    if texto_resumen:
                        return texto_resumen.get_text(strip=True)
            print("No se encontró el resumen en las tablas de OEPM")

        elif "patentscope" in url_universidad:
            print("Detectado dominio Patentscope")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Resumen')]"))
            )
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            etiqueta_resumen = soup.find(string=lambda text: text and "Resumen" in text)
            
            if etiqueta_resumen:
                resumen_texto = etiqueta_resumen.find_next("span")
                if resumen_texto:
                    return resumen_texto.get_text(strip=True)
            print("No se encontró el resumen en Patentscope")
        else:
            print(f"URL no reconocida como OEPM o Patentscope: {url_universidad}")

    except Exception as e:
        print(f"Error general al obtener el resumen: {e}")
        return None

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        if temp_dir:
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass
    
    return None

# Contador para seguimiento
total_procesados = 0
total_actualizados = 0

# Procesar todas las URLs en la colección
for documento in coleccion.find():
    total_procesados += 1
    url = documento.get("URL")
    if not url:
        print(f"Documento {total_procesados}: Sin URL, se omite.")
        continue

    # Limpiar la URL eliminando el contenido entre paréntesis
    url_limpia = re.sub(r'\s*\([^)]*\)', '', url).strip()
    print(f"\nDocumento {total_procesados}")
    print(f"URL original: {url}")
    print(f"URL limpia: {url_limpia}")

    resumen = obtener_resumen_contenido_dinamico(url_limpia)

    if resumen:
        print("Resumen encontrado, actualizando base de datos...")
        coleccion.update_one({"_id": documento["_id"]}, {"$set": {"resumen": resumen}})
        total_actualizados += 1
        print(f"Resumen actualizado. Total actualizados: {total_actualizados}")
    else:
        print("No se pudo obtener un resumen para esta URL.")

print(f"\nProceso completado:")
print(f"Total de documentos procesados: {total_procesados}")
print(f"Total de documentos actualizados: {total_actualizados}")