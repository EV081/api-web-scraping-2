import requests
import boto3
import uuid
import json

def lambda_handler(event, context):
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/ajaxb/2025"
    response = requests.get(url)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': json.dumps({'error': 'Error al acceder a la API'})
        }

    payload = response.json()      # {'data': [ ... ]}
    sismos = payload.get('data', [])

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaWebScrapping_2')

    # borrar registros antiguos
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan.get('Items', []):
            batch.delete_item(Key={'id': each['id']})

    # insertar nuevos
    rows = []
    for i, s in enumerate(sismos, start=1):
        item = {
            'id': str(uuid.uuid4()),
            '#': i,
            'fecha_local': s.get('fecha_local'),
            'hora_local': s.get('hora_local'),
            'magnitud': s.get('magnitud'),
            'referencia': s.get('referencia'),
            # añade los campos que quieras más...
        }
        rows.append(item)
        table.put_item(Item=item)

    return {
        'statusCode': 200,
        'body': json.dumps(rows, default=str)
    }
