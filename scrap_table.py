from playwright.sync_api import sync_playwright
import boto3, uuid

URL = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"
TABLE = "TablaWebScrapping_2"

def scrape_with_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("table")
        headers = [th.inner_text().strip() for th in page.locator("table thead th").all()]
        rows = []
        for r in page.locator("table tbody tr").all():
            cells = [td.inner_text().strip() for td in r.locator("td").all()]
            # A veces la primera columna es '#'; ajusta mapeo si es necesario
            row = {headers[i]: cells[i] for i in range(min(len(headers), len(cells)))}
            row["id"] = str(uuid.uuid4())
            rows.append(row)
        browser.close()
        return rows

def lambda_handler(event, context):
    rows = scrape_with_playwright()
    ddb = boto3.resource("dynamodb").Table(TABLE)
    # (Opcional) borrar y reinsertar como en tu ejemplo
    scan = ddb.scan()
    with ddb.batch_writer() as batch:
        for it in scan.get("Items", []):
            batch.delete_item(Key={"id": it["id"]})
        for it in rows:
            batch.put_item(Item=it)
    return {"statusCode": 200, "body": rows}
