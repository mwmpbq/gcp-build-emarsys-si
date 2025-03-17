# Verwende ein Basis-Image mit Python 3.9
FROM python:3.9

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere die Datei mit den Abhängigkeiten in den Container
COPY requirements.txt .

# Installiere die Python-Pakete
RUN pip install --no-cache-dir -r requirements.txt

# (Optional) Zeige die installierten Pakete zur Diagnose
RUN pip freeze

# Kopiere den restlichen Quellcode in den Container
COPY . .

# Exponiere den Port, den Cloud Run erwartet (standardmäßig 8080)
EXPOSE 8080

# Starte die Anwendung mit Gunicorn als Produktionsserver
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
