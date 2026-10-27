"""
api.py  -  FastAPI backend for the Excel merger & summary generator.

Expected uploads (strict filename matching - wrong names are rejected):
  branded_file    -> filename must contain "branded"    (case-insensitive)
  rm_file         -> filename must contain "rm"         (case-insensitive)
  master_file     -> filename must contain "master"     (case-insensitive)
  sale_file       -> filename must contain "sale"       (case-insensitive)
  receivable_file -> filename must contain "receivable" (case-insensitive)

Install dependencies:
    pip install fastapi uvicorn python-multipart

Run with:
    uvicorn api:app --reload --host 0.0.0.0 --port 8080

Interactive docs:
    http://localhost:8080/docs for local development, or
    http://localhost:9104/docs for Docker.

## Docker

The Docker image builds the frontend and copies its static files into the
FastAPI application. One backend container serves both the UI and API.
Configure `MONGODB_URI` and `MONGODB_DATABASE` in `backend/work/.env` before
starting it. Use `backend/work/.env.example` as a template if needed.

From the repository root, build and start the app with:

```sh
docker compose up --build -d
```

Open the application at http://localhost:3205 and the API docs at
http://localhost:9104/docs. Both ports reach the same backend container.
Check status and logs with:

```sh
docker compose ps
docker compose logs -f app
```

Stop it with `docker compose down`.

Endpoint:
    POST /process  ->  multipart/form-data with the five .xlsx files
                   ->  returns Final_Merged_Monthly_Summary.xlsx as download
"""
