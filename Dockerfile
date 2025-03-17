# Verwende ein Basis-Image mit Python 3.9
FROM python:3.9

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere die requirements.txt in den Container
COPY requirements.txt .

# Installiere die Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den restlichen Quellcode in den Container
COPY . .

# Exponiere den Port, den Cloud Run verwendet (Standard: 8080)
EXPOSE 8080

# Starte die Anwendung mit Gunicorn als Produktionsserver und setze den Timeout auf 120 Sekunden
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "300", "main:app"]
