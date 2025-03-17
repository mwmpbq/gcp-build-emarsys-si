import os
import csv
import io
from google.cloud import bigquery
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# Konfiguration – diese Werte können auch über Umgebungsvariablen gesetzt werden.
INHABER_TOKEN = os.environ.get("INHABER_TOKEN", "MnOPw8nrNf-K9pGu3X-NFGpuIcCIr6_fMYoTckz8fXnfVvMGmadWagKpfpHlTlCx-0VyC7T_wyq5DAuWJawfDMqAzk3lrun172ezVSiUeSk")
BIGQUERY_TABLE = os.environ.get("BIGQUERY_TABLE", "myposter-data-hub.mp_mkt_4_crm.crm_emarsys_order_article")
API_ENDPOINT = os.environ.get("API_ENDPOINT", "https://admin.scarabresearch.com/hapi/merchant/1B86E9D84EC2F51F/sales-data/api")

def fetch_bigquery_data():
    """
    Stellt eine Verbindung zu BigQuery her, führt eine Abfrage auf der angegebenen Tabelle aus
    und gibt das Ergebnis zurück.
    """
    client = bigquery.Client()
    query = f"SELECT * FROM `{BIGQUERY_TABLE}`"
    query_job = client.query(query)
    results = query_job.result()  # Warten, bis die Ergebnisse vorliegen
    return results

def convert_to_csv(results):
    """
    Konvertiert das Abfrageergebnis in einen CSV-String.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Schreibe Header, falls Daten vorhanden sind
    schema = results.schema
    if schema:
        headers = [field.name for field in schema]
        writer.writerow(headers)
        # Schreibe alle Zeilen
        for row in results:
            writer.writerow([row[field] for field in headers])
    return output.getvalue()

def send_data_to_emarsys(csv_data):
    """
    Sendet den CSV-String als POST-Request an den Emarsys-Endpunkt.
    """
    headers = {
        "Authorization": f"bearer {INHABER_TOKEN}",
        "Content-type": "text/csv",
        "Accept": "text/plain",
    }
    response = requests.post(API_ENDPOINT, headers=headers, data=csv_data.encode("utf-8"))
    return response

@app.route('/', methods=['GET'])
def main():
    try:
        # Daten von BigQuery abrufen
        results = fetch_bigquery_data()
        # Daten in CSV umwandeln
        csv_data = convert_to_csv(results)
        # CSV-Daten an Emarsys senden
        response = send_data_to_emarsys(csv_data)
        return jsonify({
            "status": "success",
            "response_code": response.status_code,
            "response_text": response.text
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    # Starte die App auf dem Host 0.0.0.0 und dem Port, der in der Umgebungsvariablen PORT definiert ist (Standard: 8080)
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
