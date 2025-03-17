import os
import csv
import io
import logging
from google.cloud import bigquery  # Bibliothek zur Kommunikation mit Google BigQuery
import requests  # Zum Senden von HTTP-Anfragen
from flask import Flask, jsonify  # Flask ist ein leichtgewichtiges Webframework, jsonify wandelt Daten in JSON um

# Logging konfigurieren
logging.basicConfig(
    level=logging.DEBUG,  # Setzt den minimalen Log-Level auf DEBUG (d.h. alle Debug-, Info-, Warnungs- und Fehlermeldungen werden ausgegeben)
    format="%(asctime)s [%(levelname)s] %(message)s"  # Format für die Log-Ausgaben
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Konfiguration – entweder aus Environment Variablen oder mit Standardwerten
INHABER_TOKEN = os.environ.get("INHABER_TOKEN", "Dein_Inhaber_Token")
BIGQUERY_TABLE = os.environ.get("BIGQUERY_TABLE", "myposter-data-hub.mp_mkt_4_crm.crm_emarsys_order_article")
API_ENDPOINT = os.environ.get("API_ENDPOINT", "https://admin.scarabresearch.com/hapi/merchant/1B86E9D84EC2F51F/sales-data/api")

def fetch_bigquery_data():
    logger.debug("Starte BigQuery-Client")
    client = bigquery.Client()
    query = f"SELECT * FROM `{BIGQUERY_TABLE}`"
    logger.debug("Führe Query aus: %s", query)
    query_job = client.query(query)
    results = query_job.result()  # Warten, bis die Ergebnisse vorliegen
    # Falls verfügbar, kann man die Anzahl der Zeilen loggen:
    try:
        row_count = results.total_rows
    except Exception:
        row_count = "unbekannt"
    logger.debug("Query erfolgreich abgeschlossen, Anzahl der Zeilen: %s", row_count)
    return results

def convert_to_csv(results):
    logger.debug("Beginne mit der Konvertierung der Ergebnisse in CSV")
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
    logger.debug("Sende CSV-Daten an Emarsys, Datenlänge: %d Bytes", len(csv_data))
    headers = {
        "Authorization": f"bearer {INHABER_TOKEN}",
        "Content-type": "text/csv",
        "Accept": "text/plain",
    }
    try:
        response = requests.post(API_ENDPOINT, headers=headers, data=csv_data.encode("utf-8"))
        logger.debug("Emarsys API antwortete mit Status: %s", response.status_code)
        return response
    except Exception as e:
        logger.error("Fehler beim Senden der Daten an Emarsys: %s", str(e))
        raise

@app.route('/', methods=['GET'])
def main_endpoint():
    logger.info("Empfange Anfrage an '/'")
    try:
        logger.info("Hole Daten von BigQuery")
        results = fetch_bigquery_data()
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
        logger.exception("Ein Fehler ist aufgetreten während der Verarbeitung der Anfrage")
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    logger.info("Starte Flask-Server auf Port %d", port)
    app.run(host='0.0.0.0', port=port)
