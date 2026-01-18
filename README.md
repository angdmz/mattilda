# Mattilda Challenge

## Overview

This is a small billing system that models:

- Schools
- Students
- Invoices
- Payments
- Payment imputations (partial/full payments per invoice)

The backend is built with FastAPI + async SQLAlchemy + PostgreSQL.
The frontend is a small React + Tailwind app that consumes the API.

## Run with Docker / Podman

1. Copy the environment file:

```bash
cp .env.example .env
```

Edit `.env` if you need to customize database credentials or other settings.

2. Start everything:

```bash
docker compose up --build
# or with podman
podman compose up --build
```

3. Apply database migrations:

```bash
docker compose --profile tools run --rm migrate-up
# or with podman
podman compose --profile tools run --rm migrate-up
```

4. Open:

- Backend API docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Run backend locally (without Docker)

From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set database connection components
export DB_USERNAME=mattilda
export DB_PASSWORD=mattilda
export DB_HOSTNAME=localhost
export DB_PORT=5432
export DB_NAME=mattilda

alembic upgrade head
uvicorn app.main:app --reload
```

## Run tests

### With Docker / Podman

The test database is automatically created by the test fixtures:

```bash
docker compose run --rm tests
# or with podman
podman compose run --rm tests
```

### Locally

From `backend/`:

```bash
# Set database connection components (test database is auto-created)
export DB_USERNAME=mattilda
export DB_PASSWORD=mattilda
export DB_HOSTNAME=localhost
export DB_PORT=5432
export DB_NAME=mattilda_test

pytest
```

## Database Migrations

### Create a new migration

```bash
docker compose --profile tools run --rm migrate-create -m "description of changes"
# or with podman
podman compose --profile tools run --rm migrate-create -m "description of changes"
```

### Apply migrations

```bash
docker compose --profile tools run --rm migrate-up
# or with podman
podman compose --profile tools run --rm migrate-up
```

### Rollback last migration

```bash
docker compose --profile tools run --rm migrate-down
# or with podman
podman compose --profile tools run --rm migrate-down
```

## API

Implemented endpoints:

- CRUD: `/schools`, `/students`, `/invoices`, `/payments`
- Statements:
  - `GET /account-statements/students/{student_id}`
  - `GET /account-statements/schools/{school_id}`
