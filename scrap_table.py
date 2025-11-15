import time
import boto3
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from chrome_aws_lambda import chromedriver_binary
from bs4 import BeautifulSoup

def lambda_handler(event, context):
    # Configuración de opciones de Chrome para Lambda usando chrome-aws-lambda
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Ejecutar sin interfaz gráfica
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.binary_location = chromedriver_binary.chromedriver_filename  # Usar el chromedriver de chrome-aws-lambda

    # Inicializa el WebDriver de Selenium con los binarios proporcionados por chrome-aws-lambda
    service = Service(chromedriver_binary.chromedriver_filename)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # URL de la página web
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"

    # Accede a la página web
    driver.get(url)

    # Esperar a que la página cargue completamente (ajustar el tiempo según sea necesario)
    time.sleep(5)  # Espera 5 segundos para que la página cargue

    # Obtener el HTML de la página cargada
    html = driver.page_source

    # Parsear el HTML y buscar la tabla
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')  # Encuentra la tabla de sismos

    if not table:
        return {
            'statusCode': 404,
            'body': 'No se encontró la tabla en la página web'
        }

    # Extraer los encabezados de la tabla
    headers = [header.find('span').text.strip() for header in table.find_all('th')]

    # Extraer las filas de la tabla
    rows = []
    for row in table.find_all('tr')[1:]:  # Omitir el encabezado
        cells = row.find_all('td')
        # Asegúrate de que el número de celdas es igual al número de encabezados
        if len(cells) == len(headers):
            row_data = {}
            for i, cell in enumerate(cells):
                span = cell.find('span')
                if span:
                    row_data[headers[i]] = span.text.strip()  # Extraer el texto del span
                else:
                    row_data[headers[i]] = cell.text.strip()  # Si no tiene span, se extrae el texto normal
            rows.append(row_data)

    # Guardar los datos en DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaWebScrapping_2')

    # Eliminar todos los elementos de la tabla antes de agregar los nuevos
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(
                Key={
                    'id': each['id']
                }
            )

    # Insertar los nuevos datos
    i = 1
    for row in rows:
        row['#'] = i
        row['id'] = str(uuid.uuid4())  # Generar un ID único para cada entrada
        table.put_item(Item=row)
        i = i + 1

    # Cerrar el navegador
    driver.quit()

    # Retornar el resultado como JSON
    return {
        'statusCode': 200,
        'body': rows
    }
