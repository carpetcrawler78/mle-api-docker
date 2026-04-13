# Week 17 – APIs & Docker: Vom Notebook zur Produktionsanwendung

> **Zielgruppe:** Einsteiger in AI Engineering  
> **Kurs:** Machine Learning Engineering Bootcamp  
> **Projekt-Bezug:** SentinelAI – Capstone II  

---

## Inhaltsübersicht

1. [Warum APIs & Docker?](#1-warum-apis--docker)
2. [JSON – Das Datenformat der APIs](#2-json--das-datenformat-der-apis)
3. [REST APIs – Wie Software mit Software spricht](#3-rest-apis--wie-software-mit-software-spricht)
4. [FastAPI – APIs mit Python bauen](#4-fastapi--apis-mit-python-bauen)
5. [Error Handling in APIs](#5-error-handling-in-apis)
6. [Docker – Das „Works on my machine"-Problem lösen](#6-docker--das-works-on-my-machine-problem-lösen)
7. [Mehrere Container verbinden](#7-mehrere-container-verbinden)
8. [Docker Compose – Der One-Command-Stack](#8-docker-compose--der-one-command-stack)
9. [Deployment in der Cloud](#9-deployment-in-der-cloud)
10. [SentinelAI: Alles zusammen anwenden](#10-sentinelai-alles-zusammen-anwenden)
11. [Cheat Sheet – Alle wichtigen Befehle](#11-cheat-sheet--alle-wichtigen-befehle)

---

## 1. Warum APIs & Docker?

### Das Problem

Du hast ein trainiertes ML-Modell in einem Jupyter Notebook. Was nun?

- **Stakeholder** können kein Notebook öffnen
- Das Modell läuft **nur auf deinem Laptop**
- Jemand Neues im Team braucht 30 Minuten Setup-Call: „Welche Python-Version? Welche Pakete? Ich kriege einen Fehler in Zeile 47 – bei dir funktioniert es aber…"
- Eine Pickle-Datei per E-Mail schicken ist **kein Deployment**

### Die Lösung: APIs + Docker

| Problem | Lösung |
|---|---|
| Modell nur lokal verfügbar | **FastAPI** – das Modell als Webservice bereitstellen |
| Unterschiedliche Umgebungen brechen den Code | **Docker** – die gesamte Laufzeitumgebung einpacken |
| Komplizierter Start vieler Services | **Docker Compose** – alles mit einem Befehl starten |

### Der Weg vom Notebook zur Produktion

```
Notebook → Python Script → FastAPI Webservice → Docker Container → Cloud Deployment
```

Jeder Schritt macht deinen Code **nutzbarer, portabler und zuverlässiger**.

---

## 2. JSON – Das Datenformat der APIs

### Was ist JSON?

**JSON** steht für *JavaScript Object Notation*. Es ist ein **Textformat** zum Austausch von strukturierten Daten – und das Standardformat, das APIs zum Senden und Empfangen von Daten verwenden.

> **Einfache Eselsbrücke:** JSON ist Text. Ein Python-Dictionary ist ein Python-Objekt im Speicher. Die Konvertierung zwischen beiden nennt man *Serialisierung* (Python → JSON) und *Deserialisierung* (JSON → Python).

**Beispiel JSON:**
```json
{
  "name": "Ada Lovelace",
  "age": 36,
  "skills": ["math", "writing"],
  "active": true,
  "manager": null
}
```

### JSON ↔ Python: Die Typ-Übersetzungstabelle

| JSON | Python |
|---|---|
| object `{}` | `dict` |
| array `[]` | `list` |
| string `"text"` | `str` |
| number | `int` oder `float` |
| `true` / `false` | `True` / `False` |
| `null` | `None` |

> **Achtung:** JSON kennt keine Tupel. Wenn du ein Python-Tupel `(1, 2)` als JSON speicherst und wieder lädst, bekommst du eine Liste `[1, 2]` zurück.

### Die 4 wichtigsten JSON-Funktionen in Python

```python
import json

# 1. Python-Objekt → JSON-String (für Übertragung/Anzeige)
json_text = json.dumps({"name": "Ada", "age": 36}, indent=2)

# 2. JSON-String → Python-Objekt (einlesen aus Text)
data = json.loads(json_text)

# 3. Python-Objekt → JSON-Datei schreiben
with open("daten.json", "w") as f:
    json.dump({"name": "Ada"}, f, indent=2)

# 4. JSON-Datei → Python-Objekt einlesen
with open("daten.json") as f:
    data = json.load(f)
```

**Merkregel:** Funktionen **mit** `s` am Ende (`dumps`, `loads`) arbeiten mit **S**trings. Funktionen **ohne** `s` (`dump`, `load`) arbeiten mit **Dateien**.

### JSON von einer API lesen

```python
import requests

response = requests.get("https://api.beispiel.com/daten")
data = response.json()   # Empfohlen: direkt parsen
# Äquivalent, aber umständlicher:
# data = json.loads(response.text)
```

### Daten validieren mit Pydantic

**Pydantic** ist eine Python-Bibliothek zur Datenvalidierung. Du definierst ein *Modell* (eine Klasse), und Pydantic prüft automatisch, ob eingehende Daten das richtige Format und die richtigen Typen haben.

```python
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    name: str
    age: int
    email: str

# Gültige Daten
user = User(name="Ada", age=36, email="ada@example.com")

# Ungültige Daten → Pydantic wirft einen ValidationError
try:
    User(name="Ada", age="dreißig", email="ada@example.com")
except ValidationError as e:
    print(e)  # Klare Fehlermeldung: age muss eine Zahl sein
```

> **Warum ist das wichtig?** In einer API kommen Daten von außen – von Nutzern, anderen Systemen, Mobilapps. Mit Pydantic fängst du fehlerhafte Eingaben *bevor* sie dein Modell oder deine Datenbank erreichen.

**SentinelAI-Bezug:** Die Anomalie-API von SentinelAI erwartet Sensor-Messwerte in einem bestimmten Format (z. B. Zeitstempel + numerische Features). Pydantic stellt sicher, dass ein falsch formatierter Request sofort mit einer verständlichen Fehlermeldung abgelehnt wird, statt das Modell zum Absturz zu bringen.

---

## 3. REST APIs – Wie Software mit Software spricht

### Was ist eine API?

**API** steht für *Application Programming Interface* – eine definierte Schnittstelle, über die Programme miteinander kommunizieren können.

Es gibt drei Arten, wie Menschen und Software mit deinem Modell interagieren können:

| Interaktionsart | Wer nutzt es? | Typischer Einsatz | Beispiel |
|---|---|---|---|
| **Direkt im Code** | ML-Ingenieure | Experimente, Notebooks | `model.predict(X)` direkt im Skript |
| **User Interface (UI)** | Endnutzer | Dashboards, Web-Apps | Arzt lädt MRT-Bild hoch, sieht Vorhersage |
| **API** | Andere Anwendungen | Produktionsintegration | Email-App sendet Text an Spam-Filter-API |

### REST – der verbreitetste API-Stil

**REST** steht für *Representational State Transfer*. Eine REST API läuft auf dem HTTP-Protokoll (das gleiche Protokoll, das Webseiten verwendet) und nutzt standardisierte Methoden:

| HTTP-Methode | Aktion | Beispiel |
|---|---|---|
| `GET` | Daten lesen | Alle Nutzer abrufen |
| `POST` | Daten erstellen | Neuen Nutzer anlegen |
| `PUT` | Daten aktualisieren | Nutzerprofil bearbeiten |
| `DELETE` | Daten löschen | Nutzer löschen |

### Wie eine API-Anfrage funktioniert

```
Client (Browser / App / curl)
    │
    │  HTTP Request: POST /predict
    │  Body: {"features": [1.2, 3.4, 5.6]}
    ▼
API Server (FastAPI)
    │
    │  Validiert Input, ruft Modell auf, erstellt Antwort
    ▼
Client empfängt Response:
    {"prediction": "anomaly", "confidence": 0.92}
```

Daten werden typischerweise als **JSON** übertragen.

> **SentinelAI-Bezug:** Das SentinelAI-System braucht eine REST API mit einem `/predict`-Endpunkt. Andere Systeme (z. B. ein SCADA-Monitoring-Dashboard) können Sensordaten per POST-Request schicken und sofort eine Anomalie-Klassifikation zurückbekommen – ohne Python-Kenntnisse zu benötigen.

---

## 4. FastAPI – APIs mit Python bauen

### Warum FastAPI?

Python bietet mehrere Web-Frameworks. Für ML Engineering ist **FastAPI** die beste Wahl:

| Framework | Eignung | Anmerkung |
|---|---|---|
| **Django** | Große Webanwendungen | Sehr komplex, überdimensioniert für reine APIs |
| **Flask** | Einfache Prototypen | Beliebt, aber wenig eingebaut |
| **FastAPI** | Moderne ML-APIs ✓ | Schnell, typsicher, automatische Dokumentation |

FastAPI ist:
- **Schnell** – gebaut auf `asyncio` (Starlette + Uvicorn)
- **Typsicher** – nutzt Python Type Hints zur automatischen Validierung
- **Selbstdokumentierend** – generiert Swagger UI automatisch unter `/docs`

### Hello World mit FastAPI

```python
from fastapi import FastAPI

app = FastAPI()  # Erstellt die App-Instanz

@app.get("/")   # Registriert einen GET-Endpunkt unter "/"
def root():
    return {"message": "Hello World"}  # Wird automatisch zu JSON
```

Starten mit:
```bash
uvicorn main:app --reload
```

> **Uvicorn** ist ein *ASGI-Server* – das Programm, das deinen FastAPI-Code tatsächlich als Webserver ausführt. `--reload` bedeutet: bei Codeänderungen automatisch neu starten (nur für Entwicklung).

Danach öffne `http://localhost:8000/docs` im Browser für die **interaktive Swagger UI** – du kannst alle Endpunkte direkt testen, ohne curl oder Postman.

### Eingaben validieren mit Pydantic

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class IrisInput(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float

@app.post("/predict")
def predict(data: IrisInput):
    # FastAPI validiert automatisch:
    # - Sind alle Felder vorhanden?
    # - Sind die Typen korrekt (float)?
    # Falsche Typen → HTTP 422 Fehler, automatisch
    features = [[data.sepal_length, data.sepal_width,
                 data.petal_length, data.petal_width]]
    prediction = model.predict(features)
    return {"prediction": int(prediction[0])}
```

### Eine vollständige CRUD-API (Nutzer-Beispiel)

**CRUD** = Create, Read, Update, Delete – die vier Grundoperationen jeder datenbankgestützten Anwendung.

Das Projekt besteht aus vier Dateien:

| Datei | Aufgabe |
|---|---|
| `database.py` | Datenbankverbindung mit SQLAlchemy aufbauen |
| `models.py` | Tabellen-Struktur als Python-Klassen definieren |
| `schemas.py` | Pydantic-Modelle für Request/Response |
| `main.py` | FastAPI-App mit allen Endpunkten |

**`database.py`** – Verbindung zur PostgreSQL-Datenbank:
```python
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()  # Lädt .env Datei (enthält z.B. DB_CONN)

engine = create_engine(os.getenv("DB_CONN"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

> **SQLAlchemy** ist ein ORM (*Object-Relational Mapper*): Es lässt dich mit Python-Objekten arbeiten, statt SQL direkt zu schreiben. Statt `SELECT * FROM users` schreibst du `db.query(User).all()`.

**`models.py`** – Tabellen-Definition:
```python
from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
```

**`schemas.py`** – Pydantic-Modelle (was reinkommt / rausgeht):
```python
from pydantic import BaseModel, ConfigDict

class UserModel(BaseModel):         # Für POST-Request (Nutzer erstellen)
    model_config = ConfigDict(from_attributes=True)
    name: str
    email: str
    password: str

class UserOut(BaseModel):           # Für Response (Passwort NICHT ausgeben!)
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
```

> **Sicherheits-Tipp:** `UserOut` enthält kein `password`-Feld. So wird das Passwort niemals in API-Antworten zurückgeschickt – auch wenn es in der Datenbank gespeichert ist.

**`main.py`** – Die API-Endpunkte:
```python
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import engine, SessionLocal

app = FastAPI()
models.Base.metadata.create_all(bind=engine)  # Tabellen anlegen falls nötig

def get_db():                       # Datenbankverbindung pro Request
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users", response_model=list[schemas.UserOut])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.post("/users", response_model=schemas.UserOut)
def create_user(request: schemas.UserModel, db: Session = Depends(get_db)):
    new_user = models.User(**request.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.put("/users/{id}")
def update_user(id: int, request: schemas.UserModel, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Nutzer nicht gefunden")
    for field, value in request.model_dump().items():
        setattr(user, field, value)
    db.commit()
    return "Erfolgreich aktualisiert"

@app.delete("/users/{id}")
def delete_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Nutzer nicht gefunden")
    db.delete(user)
    db.commit()
    return "Erfolgreich gelöscht"
```

**API testen mit curl:**
```bash
# Alle Nutzer abrufen
curl http://localhost:8000/users

# Neuen Nutzer erstellen
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Ada Lovelace","email":"ada@example.com","password":"sicher123"}'

# Nutzer aktualisieren (id=1)
curl -X PUT http://localhost:8000/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Ada Smith","email":"ada.smith@example.com","password":"neu456"}'

# Nutzer löschen (id=1)
curl -X DELETE http://localhost:8000/users/1
```

**SentinelAI-Bezug:** Für SentinelAI würdest du dieses Muster nutzen, um einen `/predict`-Endpunkt zu bauen, der Sensordaten entgegennimmt, das trainierte Anomalieerkennungsmodell aufruft und das Ergebnis (normal / anomalie + Konfidenz) zurückgibt. Alle Vorhersagen könnten außerdem in einer PostgreSQL-Datenbank gespeichert werden (z. B. für Audit-Logs oder späteres Retraining).

---

## 5. Error Handling in APIs

### Warum Error Handling wichtig ist

Deine API läuft perfekt – bis jemand ungültige Daten schickt. Ohne Error Handling:
- Nutzer sehen `500 Internal Server Error` und einen kryptischen Stack Trace
- Keine hilfreiche Fehlermeldung
- Die aufrufende Anwendung weiß nicht, was sie falsch gemacht hat

### HTTP-Statuscodes – die Sprache der APIs

| Code | Bedeutung | Wann |
|---|---|---|
| **200** | OK | Alles funktioniert |
| **400** | Bad Request | Ungültige Eingabe vom Client |
| **404** | Not Found | Ressource existiert nicht |
| **422** | Validation Error | FastAPI: falscher Datentyp |
| **500** | Internal Server Error | Unbehandelter Fehler im Server |

> Jeder Status-Code ist wie ein Ampelsignal für die aufrufende Anwendung. `200` = grün. `4xx` = der Client hat etwas falsch gemacht. `5xx` = der Server hat ein Problem.

### Ohne vs. mit Error Handling

```python
# ❌ Ohne Error Handling – gefährlich in Produktion
@app.post("/predict")
def predict(data: dict):
    features = data["features"]      # KeyError wenn "features" fehlt!
    result = model.predict([features])
    return {"prediction": result[0]}

# ✅ Mit Error Handling – produktionsreif
@app.post("/predict")
def predict(data: dict):
    try:
        features = data["features"]
        result = model.predict([features])
        return {"prediction": result[0]}
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail="Pflichtfeld 'features' fehlt im Request-Body"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server-Fehler: {str(e)}")
```

### Das HTTPException-Muster

```python
from fastapi import HTTPException

@app.get("/sensors/{sensor_id}")
def get_sensor(sensor_id: int):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(
            status_code=404,
            detail=f"Sensor {sensor_id} nicht gefunden"
        )
    return sensor
```

Was der Client erhält:
```json
HTTP/1.1 404 Not Found
{
  "detail": "Sensor 42 nicht gefunden"
}
```

> **Faustregel:** Jeder Endpunkt sollte mindestens `KeyError`, `ValueError` und einen allgemeinen `Exception`-Fallback behandeln.

---

## 6. Docker – Das „Works on my machine"-Problem lösen

### Das Problem

Du baust und testest deine API stundenlang. Alles läuft. Du schickst den Code an einen Kollegen – sofortiger Absturz. Bekannt?

Typische Ursachen:
- Anderes Betriebssystem (Windows vs. macOS vs. Linux)
- Andere Python-Version
- Fehlende oder inkompatible Pakete
- Unterschiedliche Datei-Pfade oder Umgebungsvariablen

### Lösung: Virtualisierung mit Docker

**Virtualisierung** = eine Software imitiert eine komplette Hardware/Betriebssystem-Umgebung.

Dein Python-`venv` ist ein kleiner Vorgeschmack davon – es isoliert Pakete. Aber `venv` schützt nicht vor Betriebssystem-Unterschieden oder unterschiedlichen Python-Versionen.

**Docker** geht weiter: Es verpackt *alles* in einen **Container**:
- deinen Code
- die Python-Version
- alle Abhängigkeiten
- System-Tools und Konfiguration
- ein minimales Betriebssystem

### Die drei wichtigsten Docker-Begriffe

| Begriff | Analogie | Erklärung |
|---|---|---|
| **Dockerfile** | Kochrezept | Anleitung, wie das Image gebaut wird |
| **Image** | Fertiges Gericht (eingefroren) | Gepacktes, startfähiges Template |
| **Container** | Das Gericht auf dem Teller | Eine laufende Instanz des Images |

> **Kurz gesagt:** Das `Dockerfile` beschreibt *wie*. Das `Image` ist das fertige Ergebnis. Der `Container` ist das *laufende Programm*.

### Ein Dockerfile verstehen

**Beispiel: FastAPI-App containerisieren**

```dockerfile
# Basis-Image: Python 3.11.3 (klein/schlank = "slim-buster")
FROM python:3.11.3-slim-buster

# Arbeitsverzeichnis innerhalb des Containers
WORKDIR /app

# Code in den Container kopieren
COPY . /app

# Python-Pakete installieren
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Port nach außen dokumentieren (nicht automatisch öffnen!)
EXPOSE 8000

# Startbefehl wenn der Container startet
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

> **`--host 0.0.0.0`** ist wichtig! Ohne das lauscht uvicorn nur auf `localhost` *innerhalb* des Containers, und kein externer Traffic kann ihn erreichen. `0.0.0.0` bedeutet: auf allen Netzwerkschnittstellen lauschen.

**Beispiel: PostgreSQL-Datenbank-Container**

```dockerfile
FROM postgres:17    # Offizielles PostgreSQL 17 Image
WORKDIR /app
EXPOSE 5432
CMD ["postgres"]
```

Wir installieren PostgreSQL *nicht selbst* – wir nutzen ein offizielles, gepflegtes Base-Image.

### Docker-Befehle: Image bauen und Container starten

```bash
# Image bauen (. = aktueller Ordner als Build-Kontext)
docker build -t mein_image_name .

# Container starten
docker run -d \
    --name mein_container \
    -p 8000:8000 \           # Host-Port:Container-Port
    -e API_KEY=geheim123 \   # Umgebungsvariable setzen
    mein_image_name

# Laufende Container anzeigen
docker ps

# Container-Logs anzeigen
docker logs mein_container

# Container stoppen
docker stop mein_container

# Container entfernen
docker rm -f mein_container
```

> **Port-Mapping `-p 8000:8000`:** Der erste Port ist der Port auf *deinem* Rechner (Host), der zweite ist der Port *im Container*. Du kannst auch `-p 9090:8000` schreiben – dann erreichst du die App unter Port 9090.

### Docker Hub – GitHub für Docker Images

**Docker Hub** ist ein öffentliches Registry (Speicher) für Docker Images. Ähnlich wie GitHub für Code.

```bash
# Offizielles Python-Image herunterladen
docker pull python:3.11

# Eigenes Image hochladen (nach docker login)
docker push meinusername/sentinelai-api:v1.0
```

> **Sicherheitshinweis:** Öffentliche Images können Malware oder veraltete Pakete enthalten. Verwende immer offizielle Images (mit dem „verified"-Badge) oder erstelle eigene private Registries.

**SentinelAI-Bezug:** Das trainierte SentinelAI-Modell wird mit dem FastAPI-Webservice in ein Docker-Image gepackt. Jemand aus dem Team kann dann `docker pull sentinelai/api:v1.0` ausführen und sofort die exakt gleiche Produktionsumgebung lokal laufen lassen – egal ob Windows, Mac oder Linux.

---

## 7. Mehrere Container verbinden

### Das Problem: Container sind isoliert

Standardmäßig können Docker-Container nicht miteinander kommunizieren. Ein FastAPI-Container kann die PostgreSQL-Datenbank in einem anderen Container nicht finden – selbst wenn sie auf demselben Rechner laufen.

> **Wichtig:** `localhost` innerhalb eines Containers bedeutet *dieser Container selbst*, nicht dein Host-Rechner und nicht ein anderer Container!

### Lösung: User-defined Bridge Network

Ein **Docker-Netzwerk** verbindet Container miteinander. In einem *user-defined bridge network* können Container sich **gegenseitig beim Namen aufrufen**.

```bash
# Netzwerk erstellen
docker network create mein_netz

# PostgreSQL im Netzwerk starten
docker run -d --name postgres_cont \
    --network mein_netz \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=fastapi_db \
    postgres_im

# FastAPI im gleichen Netzwerk starten
# DB_CONN verwendet "postgres_cont" als Hostname (Container-Name!)
docker run -d --name fastapi_cont \
    --network mein_netz \
    -e DB_CONN='postgresql://postgres:postgres@postgres_cont:5432/fastapi_db' \
    -p 8000:8000 \
    fastapi_im
```

### Überblick: Wer spricht wen wie an?

| Von wo | Adresse für PostgreSQL | Adresse für FastAPI-API |
|---|---|---|
| Dein Rechner (Host) | `localhost:5432` | `localhost:8000` |
| Vom FastAPI-Container aus | `postgres_cont:5432` | — |

### Datenpersistenz mit Volumes

Container sind *vergänglich* – stoppt man sie, sind alle Daten weg. **Volumes** speichern Daten außerhalb des Containers:

```bash
docker run -d --name postgres_cont \
    -v "$(pwd)/daten:/var/lib/postgresql/data" \  # Host-Ordner:Container-Ordner
    postgres_im
```

Jetzt überleben Datenbankdaten einen Container-Neustart, weil sie in `./daten/` auf deinem Rechner liegen.

---

## 8. Docker Compose – Der One-Command-Stack

### Was ist Docker Compose?

Docker Compose automatisiert alles, was wir in Kapitel 7 manuell gemacht haben:
- Netzwerk erstellen
- Container einzeln starten
- Umgebungsvariablen übergeben
- Ports mappen

Stattdessen definieren wir die gesamte Anwendung in **einer YAML-Datei** (`docker-compose.yaml`) und starten alles mit einem Befehl.

> **YAML** ist ein Konfigurationsdateiformat. Es verwendet Einrückungen (keine geschweiften Klammern) um Hierarchie auszudrücken. Einrückung mit 2 Leerzeichen ist Standard.

### Die `docker-compose.yaml` des Projekts

```yaml
services:
  db:                                      # Service-Name (= Hostname im Netzwerk!)
    image: postgres:17                     # Fertig-Image verwenden
    container_name: postgres_compose
    restart: always                        # Bei Absturz automatisch neu starten
    environment:
      POSTGRES_USER: ${POSTGRES_USER}      # Wert aus .env Datei laden
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - ./postgres-db-volume:/var/lib/postgresql/data
    healthcheck:                           # Warten bis DB wirklich bereit ist
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - my_network_compose

  app:
    build:                                 # Image selbst bauen (aus Dockerfile)
      context: service
      dockerfile: Dockerfile
    container_name: fastapi_compose
    restart: always
    environment:
      DB_CONN: postgresql://postgres:postgres@db:5432/fastapi_db
      # "db" ist der Service-Name von oben – Docker Compose löst das automatisch auf
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy         # Erst starten wenn DB gesund ist
    networks:
      - my_network_compose

networks:
  my_network_compose:
    driver: bridge
```

### Wichtige YAML-Felder erklärt

| Feld | Bedeutung |
|---|---|
| `image` | Fertiges Docker-Image aus Registry verwenden |
| `build` | Image aus lokalem Dockerfile bauen |
| `environment` | Umgebungsvariablen (wie `-e` bei `docker run`) |
| `ports` | Port-Mapping (Host:Container) |
| `volumes` | Daten persistieren |
| `depends_on` | Startreihenfolge festlegen |
| `healthcheck` | Prüfen ob Service wirklich bereit ist |
| `networks` | Gemeinsames Netzwerk für Inter-Container-Kommunikation |

### Warum `db` als Hostname und nicht `localhost`?

In Docker Compose läuft jede App in ihrem eigenen Container. `localhost` im `app`-Container bedeutet „ich selbst" – nicht die Datenbank. Docker Compose macht Service-Namen (hier: `db`) automatisch als Hostnamen im Netzwerk verfügbar. Deshalb:

```
DB_CONN: postgresql://postgres:postgres@db:5432/fastapi_db
                                          ↑
                               Service-Name aus docker-compose.yaml
```

### Docker Compose Befehle

```bash
# Alle Services bauen und starten (im Hintergrund)
docker compose up -d

# Status aller Services anzeigen
docker compose ps

# Logs aller Services
docker compose logs -f

# Nur App-Logs
docker compose logs app

# In einen laufenden Container einloggen
docker compose exec app bash

# Alles stoppen
docker compose stop

# Alles stoppen und Container + Netzwerk löschen
docker compose down
```

### Vergleich: Manuell vs. Docker Compose

| Manuell (Kapitel 7) | Docker Compose (Kapitel 8) |
|---|---|
| Images separat bauen | Build in YAML definiert |
| Netzwerk manuell erstellen | Netzwerk automatisch erstellt |
| Jeden Container mit langen Befehlen starten | `docker compose up -d` |
| DB-Hostname manuell übergeben | Service-Name `db` ist automatisch verfügbar |

**SentinelAI-Bezug:** Die SentinelAI-Produktionsumgebung könnte aus mehreren Services bestehen: FastAPI-API, PostgreSQL für Logs, einem separaten Modell-Server. Docker Compose erlaubt es, diese gesamte Infrastruktur in einer `docker-compose.yaml` zu definieren und mit einem Befehl zu starten – ideal für lokale Entwicklung und erste Cloud-Deployments.

---

## 9. Deployment in der Cloud

### Der Weg in die Cloud

Lokal läuft alles. Jetzt sollen Nutzer von überall drauf zugreifen. Dafür braucht es einen **öffentlichen Server**.

Der Workflow ist identisch mit lokal – nur die Maschine ist eine andere:

```
1. docker build  →  Image bauen
2. docker push   →  Image in Registry hochladen (Docker Hub / GCP Artifact Registry)
3. (auf Server)  docker pull  →  Image herunterladen
4. (auf Server)  docker run   →  Container starten
```

### Kostenlose / günstige Cloud-Plattformen

| Plattform | Vorteil | Ideal für |
|---|---|---|
| **Render** | Kostenloses Tier, verbindet mit GitHub, auto-deploy bei Push | Erste Schritte |
| **Railway** | Großzügiges Free-Tier, erkennt Dockerfile automatisch | Prototypen |
| **Fly.io** | Globales Deployment, CLI-basiert | Fortgeschrittene |
| **Hugging Face Spaces** | Kostenlos für ML-Demos, Docker-Support | ML-spezifische Apps |
| **Google Cloud Run** | Serverlos, skaliert automatisch | Produktion |
| **AWS ECS Fargate** | Vollständig managed, enterprise-fähig | Große Teams |

> **Für SentinelAI als Capstone-Projekt:** Render oder Hugging Face Spaces sind perfekt für eine Demo. Für eine produktionsreife Version kommt Google Cloud Run in Frage.

### Warum Cloud Run besonders geeignet ist

Cloud Run startet deinen Docker-Container nur wenn Requests eintreffen und berechnet nur für die tatsächliche Laufzeit. Bei einem ML-API-Service wie SentinelAI, der keine kontinuierliche Last hat, ist das sehr kosteneffizient.

---

## 10. SentinelAI: Alles zusammen anwenden

### Die SentinelAI-Architektur mit APIs & Docker

SentinelAI ist ein Anomalieerkennungssystem für industrielle Sensordaten. Mit dem Wissen aus Week 17 sieht die Produktionsarchitektur so aus:

```
Sensor-Daten (z.B. SCADA-System)
         │
         │ HTTP POST /predict
         ▼
┌─────────────────────────────────────────┐
│         Docker Compose Stack            │
│                                         │
│  ┌─────────────────┐  ┌──────────────┐  │
│  │  FastAPI App    │  │  PostgreSQL  │  │
│  │  /predict       │──│  Anomaly Log │  │
│  │  /health        │  │  (Audit)     │  │
│  │  /sensors       │  └──────────────┘  │
│  └─────────────────┘                    │
└─────────────────────────────────────────┘
         │
         │ {"anomaly": true, "confidence": 0.94}
         ▼
  Dashboard / Alarm-System
```

### SentinelAI `/predict`-Endpunkt

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import joblib

app = FastAPI()
model = joblib.load("sentinel_model.pkl")  # Gespeichertes Modell laden

class SensorReading(BaseModel):
    sensor_id: str
    timestamp: str
    temperature: float
    pressure: float
    vibration: float
    current: float

class PredictionResult(BaseModel):
    sensor_id: str
    anomaly: bool
    confidence: float
    message: str

@app.post("/predict", response_model=PredictionResult)
def predict(data: SensorReading):
    try:
        features = np.array([[
            data.temperature,
            data.pressure,
            data.vibration,
            data.current
        ]])
        prediction = model.predict(features)[0]
        confidence = float(model.predict_proba(features).max())

        return PredictionResult(
            sensor_id=data.sensor_id,
            anomaly=bool(prediction == 1),
            confidence=confidence,
            message="Anomalie erkannt!" if prediction == 1 else "Normaler Betrieb"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vorhersage fehlgeschlagen: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok", "model": "sentinel_v1"}
```

### SentinelAI `docker-compose.yaml`

```yaml
services:
  api:
    build: .
    container_name: sentinelai_api
    ports:
      - "8000:8000"
    environment:
      DB_CONN: postgresql://postgres:sentinel@db:5432/sentinel_db
      MODEL_PATH: /app/models/sentinel_model.pkl
    volumes:
      - ./models:/app/models    # Modell-Datei außerhalb des Images
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:17
    container_name: sentinelai_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: sentinel
      POSTGRES_DB: sentinel_db
    volumes:
      - ./data/db:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      retries: 10

networks:
  default:
    driver: bridge
```

Starten mit:
```bash
docker compose up -d
# SentinelAI API läuft unter http://localhost:8000
# Docs:         http://localhost:8000/docs
```

---

## 11. Cheat Sheet – Alle wichtigen Befehle

### JSON in Python

```python
import json

json.dumps(obj)              # Python → JSON String
json.loads(string)           # JSON String → Python
json.dump(obj, file)         # Python → JSON Datei
json.load(file)              # JSON Datei → Python
response.json()              # API Response → Python (requests-Bibliothek)
```

### FastAPI

```bash
uvicorn main:app --reload              # Dev-Server starten
uvicorn main:app --host 0.0.0.0 --port 8000  # Produktions-Start
# http://localhost:8000/docs           # Swagger UI
# http://localhost:8000/redoc          # ReDoc Dokumentation
```

### Docker

```bash
# Image bauen
docker build -t image_name .
docker build -t image_name pfad/zum/ordner

# Container starten
docker run -d --name container_name image_name
docker run -d -p 8000:8000 -e VAR=wert image_name
docker run -d -v $(pwd)/daten:/container/pfad image_name

# Container verwalten
docker ps                   # Laufende Container
docker ps -a                # Alle Container (auch gestoppte)
docker logs container_name  # Logs anzeigen
docker stop container_name  # Stoppen
docker start container_name # Wieder starten
docker rm -f container_name # Stoppen & löschen

# Images verwalten
docker images               # Alle Images
docker rmi image_name       # Image löschen
docker pull python:3.11     # Image herunterladen
docker push user/image:tag  # Image hochladen

# Netzwerk
docker network create netz_name
docker network ls

# In Container einloggen
docker exec -it container_name bash
```

### Docker Compose

```bash
docker compose up -d           # Starten (Hintergrund)
docker compose up --build -d   # Neu bauen + starten
docker compose ps              # Status
docker compose logs -f         # Logs (live)
docker compose logs app        # Nur einen Service
docker compose exec app bash   # Shell in Service
docker compose stop            # Stoppen
docker compose down            # Stoppen + löschen
docker compose down -v         # + Volumes löschen
```

### PostgreSQL (im Container)

```bash
# Von außen verbinden
psql -h localhost -p 5432 -U postgres -d fastapi_db

# Aus dem Container heraus
docker exec -it postgres_cont psql -U postgres -d fastapi_db

# Wichtige psql-Befehle
\l        # Datenbanken auflisten
\c dbname # Datenbank wechseln
\dt       # Tabellen auflisten
\q        # Beenden
```

---

## Zusammenfassung: Der Weg vom Modell zur Produktion

```
1. NOTEBOOK         Experimentieren, Modell entwickeln, Ergebnisse verstehen

2. PYTHON SCRIPT    Code aufräumen, Funktionen extrahieren, versionierbar machen

3. FASTAPI          Modell als REST API bereitstellen:
                    - Endpunkte definieren (@app.post("/predict"))
                    - Eingaben validieren (Pydantic)
                    - Fehler behandeln (HTTPException)
                    - Automatische Doku unter /docs

4. DOCKERFILE       App containerisieren:
                    - Reproduzierbare Umgebung
                    - Kein "works on my machine" mehr
                    - docker build + docker run

5. COMPOSE          Multi-Service-Stack:
                    - API + Datenbank zusammen definieren
                    - docker compose up -d

6. CLOUD            Deployment (Render / Cloud Run / AWS):
                    - docker push → Registry
                    - Server zieht Image, startet Container
                    - Weltweit erreichbar
```

> **Als ML Engineer wirst du kein Software-Ingenieur.** Du wirst ein ML Engineer, der Code schreibt, den andere Menschen ausführen, testen und vertrauen können. APIs und Docker sind dafür die unverzichtbaren Werkzeuge.

---

*Dieses Dokument fasst Week 17 des MLE Bootcamps zusammen: Kursfolien, Notebooks und Markdown-Lektionen aus dem Repository `mle-api-docker`. Projektbezug: SentinelAI – Capstone II.*
