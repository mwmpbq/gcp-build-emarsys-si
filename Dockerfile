# Verwende ein Basis-Image mit Python 3.9
FROM python:3.9

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere die Datei mit den Abhängigkeiten in das Arbeitsverzeichnis
COPY requirements.txt .

# Installiere die benötigten Python-Pakete
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den restlichen Quellcode in das Arbeitsverzeichnis
COPY . .

# Exponiere den Port, den Cloud Run verwendet (Standard 8080)
EXPOSE 8080

# Starte die Anwendung (führt main.py aus)
CMD ["python", "main.py"]