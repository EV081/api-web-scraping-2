const chromium = require('@sparticuz/chromium');
const puppeteer = require('puppeteer-core');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, PutCommand, BatchWriteCommand } = require('@aws-sdk/lib-dynamodb');

const client = new DynamoDBClient('us-east-1');
const docClient = DynamoDBDocumentClient.from(client);

const TABLE_NAME = 'TablaWebScrapping2';
const URL = 'https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados';


exports.lambda_handler = async (event, context) => {
  let browser = null;

  try {
    console.log('Iniciando scraping de sismos...');

    browser = await puppeteer.launch({
      args: chromium.args,
      defaultViewport: chromium.defaultViewport,
      executablePath: await chromium.executablePath(),
      headless: chromium.headless,
    });

    const page = await browser.newPage();

    await page.setDefaultNavigationTimeout(60000);

    console.log(`Navegando a: ${URL}`);
    await page.goto(URL, {
      waitUntil: 'networkidle0'
    });

    console.log('Esperando que la tabla se cargue...');
    await page.waitForSelector('table tbody tr', { timeout: 30000 });

    const sismos = await page.evaluate(() => {
      const rows = Array.from(document.querySelectorAll('table tbody tr'));

      return rows.map(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length < 5) return null;

        return {
          reporte_sismico: cells[0]?.textContent?.trim() || '',
          referencia: cells[1]?.textContent?.trim() || '',
          fecha_hora_local: cells[2]?.textContent?.trim() || '',
          magnitud: cells[3]?.textContent?.trim() || '',
          enlace_reporte: cells[4]?.querySelector('a')?.href || ''
        };
      }).filter(item => item !== null);
    });

    console.log(`Se encontraron ${sismos.length} sismos`);

    if (sismos.length === 0) {
      return {
        statusCode: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify({
          message: 'No se encontraron sismos para procesar',
          count: 0
        })
      };
    }

    await saveToDynamoDB(sismos);

    console.log('Scraping completado exitosamente');

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        message: 'Scraping completado exitosamente',
        count: sismos.length,
        timestamp: new Date().toISOString(),
        sismos: sismos
      })
    };

  } catch (error) {
    console.error('Error durante el scraping:', error);

    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        message: 'Error durante el scraping',
        error: error.message,
        stack: error.stack
      })
    };
  } finally {
    if (browser) {
      await browser.close();
      console.log('Browser cerrado');
    }
  }
};


async function saveToDynamoDB(sismos) {
  const timestamp = new Date().toISOString();

  const batchSize = 25;

  for (let i = 0; i < sismos.length; i += batchSize) {
    const batch = sismos.slice(i, i + batchSize);

    const putRequests = batch.map((sismo, index) => ({
      PutRequest: {
        Item: {
          id: `${sismo.reporte_sismico.replace(/\s+/g, '_')}_${Date.now()}_${i + index}`,
          reporte_sismico: sismo.reporte_sismico,
          referencia: sismo.referencia,
          fecha_hora_local: sismo.fecha_hora_local,
          magnitud: parseFloat(sismo.magnitud) || sismo.magnitud,
          enlace_reporte: sismo.enlace_reporte,
          scraped_at: timestamp
        }
      }
    }));

    const command = new BatchWriteCommand({
      RequestItems: {
        [TABLE_NAME]: putRequests
      }
    });

    try {
      await docClient.send(command);
      console.log(`Lote ${Math.floor(i / batchSize) + 1} guardado en DynamoDB`);
    } catch (error) {
      console.error(`Error guardando lote en DynamoDB:`, error);
      throw error;
    }
  }
}