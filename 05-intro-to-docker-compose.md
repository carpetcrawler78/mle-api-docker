# Docker Compose

In chapter 4, we manually built the app image, created a Docker network, and started the PostgreSQL and FastAPI containers one by one. That approach is useful for learning, but it quickly becomes repetitive.

**Docker Compose lets us define a multi-container application in one YAML file and start it with a single command.** It automates the container creation, the shared network, and the service wiring that we handled manually in the previous chapter.

You do not need to install Docker Compose separately if you are using Docker Desktop. It is already available through the `docker compose` command.

## What Compose Automates

With Compose, we no longer need to:

- create the Docker network manually
- run the database container separately
- run the app container separately
- remember the exact `docker run` flags for each service

Instead, we describe the whole application once in `docker-compose.yaml`.

## What We Are Building

The application still has the same two services:

- `db` for PostgreSQL
- `app` for FastAPI

The difference is that Compose now manages the network and startup flow for us.

```mermaid
flowchart LR
    Client["Browser / curl"] -->|"http://localhost:8000"| App["Compose service: app"]
    App -->|"DB_CONN uses host db"| DB["Compose service: db"]
    DB -->|"stores data in"| Volume["postgres-db-volume"]
    App -->|"runs on shared Compose network"| Net["Compose bridge network"]
    DB --> Net
```

## The Compose File

The file **`docker-compose.yaml`** contains:

```yaml
services:
  db:
    image: postgres:17
    container_name: postgres_compose
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - ./postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - my_network_compose

  app:
    build:
      context: service
      dockerfile: Dockerfile
    container_name: fastapi_compose
    restart: always
    environment:
      DB_CONN: postgresql://postgres:postgres@db:5432/fastapi_db
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    networks:
      - my_network_compose

networks:
  my_network_compose:
    driver: bridge
```

## How to Read This File

### Services

Each entry under `services:` defines one containerized part of the application.

| Service | Purpose |
| --- | --- |
| `db` | PostgreSQL database |
| `app` | FastAPI application |

### Important YAML fields

| Field | Meaning |
| --- | --- |
| `image` | Use a prebuilt image |
| `build` | Build an image from a Dockerfile |
| `environment` | Set environment variables inside the container |
| `ports` | Publish container ports to the host |
| `volumes` | Persist or share files |
| `depends_on` | Start one service before another |
| `healthcheck` | Tell Docker how to check whether a service is actually ready |
| `networks` | Attach services to a shared network |

## Why `DB_CONN` Is Different Here

In chapter 3, the API ran on your host machine, so `localhost` in the root `.env` was correct.

In chapter 4, we passed a container-specific `DB_CONN` manually with:

```bash
-e DB_CONN='postgresql://postgres:postgres@postgres_cont:5432/fastapi_db'
```

In Compose, the same idea still applies: the app runs inside a container, so it must connect to the database **by service name**, not by `localhost`.

That is why the app service uses:

```text
postgresql://postgres:postgres@db:5432/fastapi_db
```

Here, `db` is the Compose service name, and Docker Compose automatically makes that name available on the shared network.

The root `.env` file can stay unchanged for host-based local runs. Compose overrides only the app container’s connection string in `docker-compose.yaml`.

## Why the Volume Path Matters

The PostgreSQL image stores its data in:

```text
/var/lib/postgresql/data
```

That is why the `db` service mounts:

```yaml
- ./postgres-db-volume:/var/lib/postgresql/data
```

This keeps the database data on your machine so it survives container restarts.

## Running the Compose Application

### What we are doing

We are asking Compose to build the app image if needed, create the network, and start both services.

### Command

```bash
docker compose up -d
```

### What the command means

- `docker compose up` creates and starts the services
- `-d` runs them in detached mode, in the background

### What to expect

Compose will:

- create the `app` image from `service/Dockerfile`
- start the PostgreSQL container
- wait until PostgreSQL is healthy
- start the FastAPI container
- create the shared bridge network automatically

## Checking the Running Services

To see whether the services are running:

```bash
docker compose ps
```

You should see both `db` and `app`.

To follow the logs:

```bash
docker compose logs -f
```

To view only the app logs:

```bash
docker compose logs app
```

If the FastAPI service started correctly, you should see Uvicorn startup messages.

## Testing the Compose Setup

Now test the application from your host machine.

### Root endpoint

```bash
curl http://localhost:8000/
```

Expected response:

```json
{"data":"user list"}
```

### Empty user list

```bash
curl http://localhost:8000/users
```

Expected response on a fresh database:

```json
[]
```

### Swagger UI

Open: <http://localhost:8000/docs>

If that page loads, the Compose-managed app is reachable from your browser and the API is connected to the database correctly.

## Why Compose Is Simpler Than Chapter 4

Compare this chapter with the manual setup from chapter 4:

| Manual Docker | Docker Compose |
| --- | --- |
| Build images separately | Build is defined in YAML |
| Create network manually | Network is created automatically |
| Run containers with long commands | One `docker compose up -d` command |
| Pass app DB host manually | Service name `db` is already known on the network |

That is the main value of Compose: it turns a collection of related container commands into one application definition.

## Stopping the Compose Application

To stop the services without removing them:

```bash
docker compose stop
```

To stop and remove the containers and network:

```bash
docker compose down
```

If you also want to remove the persisted database volume directory content on your machine, delete `postgres-db-volume` manually afterward.

## Common Compose Commands

| Command | What it does |
| --- | --- |
| `docker compose build` | Build or rebuild service images |
| `docker compose up` | Create and start services |
| `docker compose up -d` | Start services in the background |
| `docker compose ps` | Show service status |
| `docker compose logs` | Show logs from all services |
| `docker compose logs -f` | Follow logs in real time |
| `docker compose logs app` | Show logs for only the app service |
| `docker compose exec app bash` | Open a shell in the app container |
| `docker compose stop` | Stop running services |
| `docker compose down` | Stop and remove containers and networks |

## Summary

In this chapter, you:

- used `docker-compose.yaml` to define the database and API services,
- let Compose build the app image automatically,
- let Compose create the shared network automatically,
- connected the app to the database using the service hostname `db`,
- started the whole application with `docker compose up -d`.

At this point, you have the same two-container application from chapter 4, but managed in a much simpler and more repeatable way.
