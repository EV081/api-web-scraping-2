import os, json, uuid, boto3, asyncio
from playwright.async_api import async_playwright

URL = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"
TABLE = "TablaWebScrapping_2"

async def scrape_async():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(URL, wait_until="networkidle")
        await page.wait_for_selector("table")
        headers = [await th.inner_text() for th in await page.locator("table thead th").all()]
        rows = []
        for r in await page.locator("table tbody tr").all():
            cells = [await td.inner_text() for td in await r.locator("td").all()]
            row = {headers[i]: cells[i] for i in range(min(len(headers), len(cells)))}
            row["id"] = str(uuid.uuid4())
            rows.append(row)
        await browser.close()
        return rows

def lambda_handler(event, context):
    rows = asyncio.run(scrape_async())
    ddb_table = boto3.resource("dynamodb").Table(TABLE)

    scan = ddb_table.scan()
    with ddb_table.batch_writer() as batch:
        for it in scan.get("Items", []):
            batch.delete_item(Key={"id": it["id"]})
        for it in rows:
            batch.put_item(Item=it)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(rows, ensure_ascii=False)
    }
