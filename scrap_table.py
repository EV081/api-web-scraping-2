from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Configuración del driver de Selenium (usando ChromeDriver)
chrome_driver_path = '/ruta/al/chromedriver'  # Cambia esta ruta al directorio donde está el chromedriver

# Configuración de las opciones para no abrir la ventana del navegador (opcional)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Corre el navegador en segundo plano sin abrir una ventana

# Inicializa el driver de Selenium con las opciones configuradas
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# URL de la página web
url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"

# Accede a la página web
driver.get(url)

# Espera a que la página cargue completamente (ajusta el tiempo según sea necesario)
time.sleep(5)  # Espera 5 segundos (esto puede ajustarse dependiendo de la velocidad de carga)

# Obtén el HTML de la página cargada
html = driver.page_source

# Usar BeautifulSoup para parsear el HTML
soup = BeautifulSoup(html, 'html.parser')

# Encontrar la tabla
table = soup.find('table')
if table:
    print("Tabla encontrada. Extrayendo los datos...")
    
    # Extraer los encabezados de la tabla (si existen)
    headers = [header.text.strip() for header in table.find_all('th')]
    print("Encabezados:", headers)
    
    # Extraer las filas de la tabla
    rows = []
    for row in table.find_all('tr')[1:]:  # Omitir el encabezado
        cells = row.find_all('td')
        row_data = {headers[i]: cell.text.strip() for i, cell in enumerate(cells)}
        rows.append(row_data)
    
    print("Datos extraídos:", rows)
else:
    print("No se encontró la tabla en la página.")

# Cierra el navegador
driver.quit()
