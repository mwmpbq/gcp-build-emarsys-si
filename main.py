import os
import csv
import io
import logging
from datetime import datetime
from google.cloud import bigquery  # Bibliothek zur Kommunikation mit Google BigQuery
import requests  # Für HTTP-Anfragen
from flask import Flask, jsonify, request  # Flask ist ein leichtgewichtiges Webframework

# Logging konfigurieren: DEBUG-Level gibt sehr detaillierte Informationen aus
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Konfiguration: Entweder werden Umgebungsvariablen genutzt oder Standardwerte verwendet
INHABER_TOKEN = os.environ.get("INHABER_TOKEN", "MnOPw8nrNf-K9pGu3X-NFGpuIcCIr6_fMYoTckz8fXnfVvMGmadWagKpfpHlTlCx-0VyC7T_wyq5DAuWJawfDMqAzk3lrun172ezVSiUeSk")
BIGQUERY_TABLE = os.environ.get("BIGQUERY_TABLE", "myposter-data-hub.mp_mkt_4_crm.crm_emarsys_order_article")
API_ENDPOINT = os.environ.get("API_ENDPOINT", "https://admin.scarabresearch.com/hapi/merchant/1B86E9D84EC2F51F/sales-data/api")

def fetch_bigquery_data(mode='all'):
    """
    Ruft Daten aus BigQuery ab.
    Wenn mode='yesterday' wird nur die Daten von gestern abgerufen,
    andernfalls werden alle Daten abgefragt.
    
    Die Spalte 'timestamp' wird dabei zur Identifikation des gestrigen Datums genutzt.
    """
    logger.debug("Starte BigQuery-Client")
    client = bigquery.Client()

    if mode == 'yesterday':
        # Filter: DATE(timestamp) entspricht dem gestrigen Datum
        query = (
            f"SELECT * FROM `{BIGQUERY_TABLE}` "
            "WHERE DATE(timestamp) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)"
        )
        logger.info("Abfrage: Nur Daten vom gestrigen Tag")
    else:
        query = f"SELECT * FROM `{BIGQUERY_TABLE}`"
        logger.info("Abfrage: Alle Daten")
    
    logger.debug("Auszuführende Query: %s", query)
    query_job = client.query(query)
    results = query_job.result()  # Blockiert, bis die Ergebnisse vorliegen

    try:
        row_count = results.total_rows
    except Exception:
        row_count = "unbekannt"
    logger.debug("Query abgeschlossen, Zeilenanzahl: %s", row_count)
    return results

def convert_to_csv(results):
    """
    Konvertiert das Query-Ergebnis in einen CSV-String.
    CSV (Comma-Separated Values) ist ein Format, um tabellarische Daten als Text zu speichern.
    """
    logger.debug("Beginne Konvertierung in CSV")
    output = io.StringIO()
    writer = csv.writer(output)
    
    schema = results.schema
    if schema:
        headers = [field.name for field in schema]
        logger.debug("CSV Header: %s", headers)
        writer.writerow(headers)
        for row in results:
            writer.writerow([row[field] for field in headers])
    
    csv_content = output.getvalue()
    logger.debug("CSV-Konvertierung abgeschlossen, Größe: %d Bytes", len(csv_content))
    return csv_content

def send_data_to_emarsys(csv_data):
    """
    Sendet den CSV-String per HTTP-POST an den Emarsys-API-Endpunkt.
    """
    logger.debug("Sende CSV-Daten an Emarsys (Datenlänge: %d Bytes)", len(csv_data))
    headers = {
        "Authorization": f"bearer {INHABER_TOKEN}",
        "Content-type": "text/csv",
        "Accept": "text/plain",
    }
    try:
        response = requests.post(API_ENDPOINT, headers=headers, data=csv_data.encode("utf-8"))
        logger.debug("Emarsys-Antwort: Status %s", response.status_code)
        return response
    except Exception as e:
        logger.error("Fehler beim Senden der Daten an Emarsys: %s", str(e))
        raise

@app.route('/', methods=['GET'])
def main_endpoint():
    """
    Hauptendpunkt, der den gewünschten Modus anhand eines URL-Parameters auswählt:
      - ?mode=all      => Alle Daten werden abgerufen (Standard)
      - ?mode=yesterday => Es werden nur die Daten vom gestrigen Tag abgerufen
    """
    mode = request.args.get('mode', 'all')
    logger.info("Modus ausgewählt: %s", mode)
    
    try:
        logger.info("Starte Datenabfrage")
        results = fetch_bigquery_data(mode)
        logger.info("Wandle Daten in CSV um")
        csv_data = convert_to_csv(results)
        logger.info("Sende CSV-Daten an Emarsys")
        response = send_data_to_emarsys(csv_data)
        logger.info("Daten erfolgreich gesendet, Antwortcode: %s", response.status_code)
        return jsonify({
            "status": "success",
            "response_code": response.status_code,
            "response_text": response.text
        })
    except Exception as e:
        logger.exception("Fehler während der Verarbeitung")
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    logger.info("Starte Flask-Server auf Port %d", port)
    app.run(host='0.0.0.0', port=port)
