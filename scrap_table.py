import json
import uuid
import boto3
import requests

def lambda_handler(event, context):
    url = "https://ultimosismo.igp.gob.pe/api/ultimo-sismo/ajaxb/2025"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
    }

    response = requests.get(url, headers=headers, timeout=10)

    print("STATUS:", response.status_code)
    print("CONTENT-TYPE:", response.headers.get("Content-Type"))
    print("BODY PREVIEW:", response.text[:200])

    if response.status_code != 200:
        return {
            "statusCode": response.status_code,
            "body": json.dumps({
                "error": "Error al acceder a la API",
                "preview": response.text[:200]
            })
        }

    # La API devuelve directamente una LISTA: [ { ... }, { ... }, ... ]
    try:
        sismos = response.json()
    except ValueError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "La respuesta no es JSON válido",
                "detalle": str(e),
                "preview": response.text[:200]
            })
        }

    if not isinstance(sismos, list):
        sismos = [sismos]

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("TablaWebScrapping")

    # borrar items antiguos
    scan = table.scan()
    with table.batch_writer() as batch:
        for item in scan.get("Items", []):
            batch.delete_item(Key={"id": item["id"]})

    # insertar nuevos
    items_guardados = []
    with table.batch_writer() as batch:
        for i, s in enumerate(sismos, start=1):
            item = {
                "id": str(uuid.uuid4()),
                "#": i,
                "codigo": s.get("codigo"),
                "fecha_local": s.get("fecha_local"),
                "hora_local": s.get("hora_local"),
                "latitud": s.get("latitud"),
                "longitud": s.get("longitud"),
                "magnitud": s.get("magnitud"),
                "profundidad": s.get("profundidad"),
                "referencia": s.get("referencia"),
                "intensidad": s.get("intensidad"),
                "reporte_acelerometrico_pdf": s.get("reporte_acelerometrico_pdf"),
            }
            items_guardados.append(item)
            batch.put_item(Item=item)
            
    print(json.dumps(items_guardados, indent=2, ensure_ascii=False))
    return {
        "statusCode": 200,
        "body": json.dumps(items_guardados, default=str)
    }
