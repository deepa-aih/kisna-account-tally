FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS application

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/work/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/work/api.py backend/work/db.py ./
COPY --from=frontend-build /frontend/dist ./static

EXPOSE 9104

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "9104"]
