# FastAPI and Docker

In chapter 2 we ran PostgreSQL in Docker. In chapter 3, we ran the API directly on the host machine. In this chapter, we will containerize the FastAPI app too, so both parts of the application can run in Docker.

This chapter focuses on the **manual** multi-container workflow. That means we will build the app image ourselves, create a Docker network ourselves, and start both containers with `docker run`. This is a useful learning step because it shows clearly how the pieces connect before Docker Compose automates the setup in the next lesson.

## What We Are Building

We will now have two containers:

- a **PostgreSQL container** for the database
- a **FastAPI container** for the API

The FastAPI container needs to talk to the PostgreSQL container over a shared Docker network.

```mermaid
flowchart LR
    Client["Browser / curl"] -->|"http://localhost:8000"| HostPort["Host Port 8000"]
    HostPort -->|"mapped with -p 8000:8000"| App["Container: fastapi_cont"]
    App -->|"DB_CONN uses hostname postgres_cont"| Net["User-defined bridge network"]
    DB["Container: postgres_cont"] --> Net
    App -->|"runs uvicorn main:app"| API["FastAPI application"]
    API -->|"SQLAlchemy queries"| DB
```

## Why Containerize the API Too?

Running the API in a container gives us a few benefits:

- the app runs in the same predictable environment on different machines
- Python and package versions are controlled by the image
- the API can communicate with the database container by container name
- the setup starts to look more like a real multi-service application

This chapter is also the bridge between:

- **chapter 3**, where the API ran locally
- **chapter 5**, where Docker Compose will run everything together

## Before You Start

This chapter assumes:

- the root PostgreSQL `Dockerfile` from chapter 2 already exists
- the FastAPI app from chapter 3 is working
- Docker Desktop is running

You will **not** need to change the root `.env` here. We will keep the local host-based `.env` for local FastAPI runs and pass the container-specific database connection only at runtime with `-e DB_CONN=...`.

## Creating the App Dockerfile

The FastAPI app now has its own Dockerfile in **`service/Dockerfile`**:

```Dockerfile
# Set the base image
FROM python:3.11.3-slim-buster

# Set the working directory
WORKDIR /app

# Copy the application code to the working directory
COPY . /app

# Install the dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### What each line does

| Line | Purpose |
| --- | --- |
| `FROM python:3.11.3-slim-buster` | Use Python 3.11.3 as the base image |
| `WORKDIR /app` | Set the working directory inside the container |
| `COPY . /app` | Copy the FastAPI app into the image |
| `RUN pip install ...` | Install the Python dependencies |
| `EXPOSE 8000` | Document that the API listens on port `8000` |
| `CMD [...]` | Start the FastAPI app with Uvicorn |

The important idea is the same as in chapter 2: the Dockerfile is the recipe, and the image is the packaged result.

## Building the App Docker Image

### What we are doing

We are building a Docker image for the FastAPI app from the `service/` folder.

### Command

Run this command from the project root:

```bash
docker build -t fastapi_im service
```

### What the command means

- `docker build` builds a Docker image
- `-t fastapi_im` tags the image as `fastapi_im`
- `service` tells Docker to use the `service/` folder as the build context

### What to expect

Docker reads `service/Dockerfile`, copies the FastAPI app into the image, installs the dependencies, and creates an image named `fastapi_im`.

## Networking in Docker

By default, containers are isolated from each other. That isolation is usually helpful, but it also means the app container cannot automatically find the database container.

To let the containers communicate, we will create a **user-defined bridge network**.

### Why not just use `localhost`?

Inside a container, `localhost` means **that same container**, not your host machine and not another container.

So:

- from your **host machine**, `localhost:8000` means the published FastAPI port
- from the **FastAPI container**, `postgres_cont` means the PostgreSQL container on the same Docker network

### Default bridge vs user-defined bridge

| Network type | How containers usually find each other |
| --- | --- |
| Default bridge | Mostly by IP address |
| User-defined bridge | By container name as hostname |

That second behavior is exactly what we want here, because it lets us use `postgres_cont` in the database connection string.

## Creating the Network

### What we are doing

We are creating a private Docker network for the API and database containers.

### Command

```bash
docker network create fastapi_net
```

### What to expect

Docker creates a new user-defined bridge network named `fastapi_net`.

If you want to list Docker networks, run:

```bash
docker network ls
```

## Running the PostgreSQL Container on the Network

### What we are doing

We are starting the database container and attaching it to `fastapi_net`.

If you already created the PostgreSQL image in chapter 2, you can reuse it. If not, build it from the project root first:

```bash
docker build -t postgres_im .
```

Then run the container:

```bash
docker run -d --name postgres_cont \
    --network fastapi_net \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=fastapi_db \
    postgres_im
```

If this command fails, you most likely already have a container with the same name running. In that case, stop and remove the existing container with the command below, then start it again with the command above.

```bash
docker rm -f postgres_cont
```

### What the command means

- `--network fastapi_net` attaches the container to our custom network
- `--name postgres_cont` gives the database container a hostname the app can use
- the `POSTGRES_*` variables initialize the database on first startup

### What to expect

The database starts in the background and is reachable from other containers on `fastapi_net` as `postgres_cont`.

You can check the logs with:

```bash
docker logs postgres_cont
```

Wait until PostgreSQL is ready before starting the app container.

## Running the FastAPI Container

### What we are doing

We are starting the FastAPI container on the same network and giving it a container-specific `DB_CONN`.

### Command

```bash
docker run -d --name fastapi_cont \
    --network fastapi_net \
    -e DB_CONN='postgresql://postgres:postgres@postgres_cont:5432/fastapi_db' \
    -p 8000:8000 \
    fastapi_im
```

### What the command means

| Part | Meaning |
| --- | --- |
| `-d` | Run the container in the background |
| `--name fastapi_cont` | Name the app container |
| `--network fastapi_net` | Join the shared Docker network |
| `-e DB_CONN=...` | Override the database connection string for the container |
| `-p 8000:8000` | Publish the API on host port `8000` |
| `fastapi_im` | Use the FastAPI app image we built earlier |

### Why `DB_CONN` is passed here

In chapter 3, the app ran on the host machine, so `localhost` in `.env` was correct.

In this chapter, the app runs inside a container. That means it must connect to the database container by container name: `postgres_cont`

So the connection string becomes:

```text
postgresql://postgres:postgres@postgres_cont:5432/fastapi_db
```

We pass that value directly with `-e DB_CONN=...` so the root `.env` can stay unchanged for local runs.

### What to expect

The FastAPI app starts in the background and becomes available on: <http://localhost:8000>

To confirm the container started correctly, run:

```bash
docker logs fastapi_cont
```

## Testing the Containerized API

Now that both containers are running, test the API from your host machine.

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

### Interactive docs

Open: <http://localhost:8000/docs>

If that page loads, the app container is reachable from your browser and the app is talking to the database successfully.

## Useful Docker Commands

| Command | What it does |
| --- | --- |
| `docker ps` | Show running containers |
| `docker logs postgres_cont` | Show database logs |
| `docker logs fastapi_cont` | Show app logs |
| `docker network ls` | List Docker networks |
| `docker network inspect fastapi_net` | Show details for the custom network |

## Stopping the Containers

To stop both containers:

```bash
docker stop fastapi_cont postgres_cont
```

If you want to remove them too:

```bash
docker rm -f fastapi_cont postgres_cont
```

And if you want to remove the custom network afterward:

```bash
docker network rm fastapi_net
```

## Why This Chapter Matters

This manual workflow is helpful because it makes the hidden pieces visible:

- images must be built separately,
- containers must be started separately,
- environment variables may change depending on where the app runs,
- containers need a shared network to talk to each other by name.

Once that mental model is clear, Docker Compose becomes much easier to understand.

## Summary

In this chapter, you:

- built a Docker image for the FastAPI app,
- created a user-defined bridge network,
- ran PostgreSQL and FastAPI in separate containers,
- connected the app container to the database container by hostname,
- verified that the API works on `localhost:8000`.

In the next lesson, we will use Docker Compose to automate this whole multi-container setup with a single configuration file.
