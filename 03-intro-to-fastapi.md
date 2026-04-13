# Application Programming Interfaces (APIs)

**An API is a way for software systems to communicate with each other.** In a web API, one application sends an HTTP request and another application sends back a response, often in JSON format.

In this chapter, we will build a small **REST API** with **FastAPI**. REST is a common style for web APIs where data is exposed through URLs and standard HTTP methods such as:

- `GET` to read data
- `POST` to create data
- `PUT` to update data
- `DELETE` to remove data

FastAPI is a modern Python framework for building APIs. It is popular because it is:

- easy to read and write
- fast in development and at runtime
- strongly typed
- able to generate interactive API documentation automatically

In this repository, FastAPI is the application layer that sits in front of the PostgreSQL database we created in the previous Docker lesson. FastAPI receives requests, validates input data, talks to the database through SQLAlchemy, and returns JSON responses.

## What We Are Building

We will build a small CRUD API for users. CRUD stands for:

- **Create**
- **Read**
- **Update**
- **Delete**

Our application has four main building blocks:

| File | Responsibility |
| --- | --- |
| `database.py` | Connect to PostgreSQL and create SQLAlchemy session helpers |
| `models.py` | Define SQLAlchemy table models |
| `schemas.py` | Define Pydantic models for request and response data |
| `main.py` | Create the FastAPI app and define the API routes |

At a high level, the flow looks like this:

```mermaid
flowchart LR
    Client["Browser / curl / Swagger UI"] --> API["FastAPI App"]
    API --> Schemas["Pydantic Schemas"]
    API --> Session["SQLAlchemy Session"]
    Session --> Models["SQLAlchemy Models"]
    Models --> DB["PostgreSQL Database"]
    DB --> Models
    Models --> API
    Schemas --> API
    API --> Client
```

## Before You Start

This chapter assumes that the PostgreSQL database from [02-intro-to-docker.md](02-intro-to-docker.md) is already running and that the root `.env` file points to:

```text
DB_CONN='postgresql://postgres:postgres@localhost:5432/fastapi_db'
```

That `localhost` host is correct for this chapter because we are running FastAPI directly on your machine, not inside a Docker container yet.

## How the Pieces Fit Together

The app uses three main libraries together:

| Tool | What it does here |
| --- | --- |
| **FastAPI** | Defines routes and returns HTTP responses |
| **Pydantic** | Validates request bodies and shapes response data |
| **SQLAlchemy** | Talks to PostgreSQL using Python objects |

That separation is useful:

- FastAPI handles the web layer
- Pydantic handles data validation and serialization
- SQLAlchemy handles database access

This keeps the code easier to understand and easier to extend later.

## Creating the Database Connection

### What we are doing

We are creating the reusable database connection setup for the app.

### Code

The file **`service/database.py`** contains:

```python
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

SQLALCHEMY_DATABASE_URI = os.getenv("DB_CONN")

if SQLALCHEMY_DATABASE_URI is None:
    raise ValueError("DB_CONN environment variable is required")

engine = create_engine(SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```

### What this does

- `load_dotenv()` loads values from the `.env` file
- `os.getenv("DB_CONN")` reads the database connection string
- `create_engine(...)` creates the SQLAlchemy database engine
- `sessionmaker(...)` creates a factory for database sessions
- `declarative_base()` creates the base class for our SQLAlchemy models

### Why `SessionLocal` matters

Each request should get its own database session. That session is opened when needed and then closed when the request finishes. This helps keep database access organized and avoids leaving connections open longer than necessary.

## Creating the Database Model

### What we are doing

We are defining the Python class that maps to the `users` table in PostgreSQL.

### Code

The file **`service/models.py`** contains:

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

### What this does

- `User` is a SQLAlchemy model
- `__tablename__ = "users"` maps the class to the `users` table
- Each `Column(...)` describes one database column

SQLAlchemy lets us work with Python objects instead of writing raw SQL for every operation.

## Creating the Pydantic Schemas

### What we are doing

We are defining the request and response shapes for the API.

### Code

The file **`service/schemas.py`** contains:

```python
from pydantic import BaseModel, ConfigDict


class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class UserUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: str
    password: str
```

### What this does

- `UserModel` describes the body for creating a user
- `UserOut` describes what we send back to clients
- `UserUpdate` describes the body for updating a user

### Why `from_attributes=True` matters

FastAPI often returns SQLAlchemy objects directly. In Pydantic v2, `ConfigDict(from_attributes=True)` tells Pydantic that it is allowed to build response data from object attributes, not only from plain dictionaries.

That is why the API can return a SQLAlchemy `User` object and still produce valid JSON automatically.

Also notice that `UserOut` does **not** include a `password` field. This means the password is stored in the database, but it is not exposed in API responses.

## Creating the FastAPI App

### What we are doing

We are combining the database layer, schemas, and routes into one FastAPI application.

### Code

The file **`service/main.py`** contains:

```python
from fastapi import Depends, FastAPI, HTTPException
import models
import schemas
from database import engine, SessionLocal
from sqlalchemy.orm import Session


app = FastAPI()

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@app.get("/")
def index():
    return {"data": "user list"}


@app.get("/users", response_model=list[schemas.UserOut])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


@app.post("/users", response_model=schemas.UserOut)
def create_user(request: schemas.UserModel, db: Session = Depends(get_db)):
    new_user = models.User(
        name=request.name, email=request.email, password=request.password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.put("/users/{id}")
def update_user(id: int, request: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id)
    existing_user = user.first()
    if existing_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in request.model_dump().items():
        setattr(existing_user, field, value)

    db.commit()
    return "Updated successfully"


@app.delete("/users/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id)
    if not user.first():
        raise HTTPException(status_code=404, detail="User not found")
    user.delete(synchronize_session=False)
    db.commit()
    return "Deleted successfully"
```

### What this does

- `app = FastAPI()` creates the API application
- `models.Base.metadata.create_all(bind=engine)` creates the tables if they do not exist yet
- `get_db()` opens a session for the request and closes it afterward
- Each route function handles one API endpoint

### FastAPI decorators at a glance

| Decorator | HTTP Method | Purpose |
| --- | --- | --- |
| `@app.get()` | GET | Read data |
| `@app.post()` | POST | Create data |
| `@app.put()` | PUT | Update data |
| `@app.delete()` | DELETE | Delete data |

### Endpoint summary

| Method | Path | Purpose | Typical response |
| --- | --- | --- | --- |
| `GET` | `/` | Quick sanity endpoint | `{"data":"user list"}` |
| `GET` | `/users` | Return all users | `[]` or a list of users |
| `POST` | `/users` | Create a user | Created user without showing password |
| `PUT` | `/users/{id}` | Update one user | `"Updated successfully"` |
| `DELETE` | `/users/{id}` | Delete one user | `"Deleted successfully"` |

## Running the App

### What we are doing

We are starting the FastAPI development server locally.

### Command

Move into the `service` folder first:

```bash
cd service
uvicorn main:app --reload --port 8000
```

### What the command means

- `uvicorn` starts the ASGI server
- `main:app` means "use the `app` object from `main.py`"
- `--reload` restarts the server automatically when code changes
- `--port 8000` serves the app on port `8000`

### What to expect

Once the app starts, open:

- [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI
- [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) for the OpenAPI schema

If port `8000` is already in use, choose another port with `--port`.

## Testing the App

You can test the API from the interactive docs, but it is also useful to send requests from the terminal with `curl`.

Open a **new terminal** so the Uvicorn server can keep running in the first one.

### 1. Check the root endpoint

```bash
curl http://localhost:8000/
```

Expected response:

```json
{"data":"user list"}
```

### 2. Check the empty user list

On a fresh database, this endpoint should return an empty list:

```bash
curl http://localhost:8000/users
```

Expected response:

```json
[]
```

Notice that if you added a user to the database in the previous chapter and did not stop and remove the container before starting a new one, you will see this user listed here instead of an empty list. In that case, the user to be created in the next step will have `"id":2`.

### 3. Create a user

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Doe","email":"jane.doe@example.com","password":"password1234"}'
```

Expected response:

```json
{"id":1,"name":"Jane Doe","email":"jane.doe@example.com"}
```

Notice that the password is not returned. That happens because the route uses `response_model=schemas.UserOut`.

### 4. List users again

```bash
curl http://localhost:8000/users
```

Expected response:

```json
[{"id":1,"name":"Jane Doe","email":"jane.doe@example.com"}]
```

### 5. Update the user

```bash
curl -X PUT http://localhost:8000/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Smith","email":"jane.smith@example.com","password":"newpass"}'
```

Expected response:

```json
"Updated successfully"
```

### 6. Delete the user

```bash
curl -X DELETE http://localhost:8000/users/1
```

Expected response:

```json
"Deleted successfully"
```

### 7. Confirm the list is empty again

```bash
curl http://localhost:8000/users
```

Expected response:

```json
[]
```

## Common Commands

| Command | What it does |
| --- | --- |
| `curl http://localhost:8000/` | Test the root endpoint |
| `curl http://localhost:8000/users` | List users |
| `curl -X POST ...` | Create a user |
| `curl -X PUT ...` | Update a user |
| `curl -X DELETE ...` | Delete a user |
| `http://localhost:8000/docs` | Open the interactive Swagger UI |

## Why This App Structure Is Useful

This project is intentionally small, but the structure already follows patterns used in larger APIs:

- models are separated from request and response schemas,
- database access is separated from route definitions,
- each request gets its own database session,
- FastAPI generates interactive documentation automatically.

That makes the app easier to test, easier to extend, and easier to containerize in the next chapter.

## Summary

In this lesson, you:

- reviewed what APIs and REST endpoints are,
- built a FastAPI app connected to PostgreSQL,
- used SQLAlchemy models to represent database tables,
- used Pydantic schemas to validate and shape API data,
- ran the app locally with Uvicorn,
- tested the full CRUD flow with `curl`.

In the next lesson, we will put this FastAPI app into a Docker container and connect it to the PostgreSQL container.
