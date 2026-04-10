FROM node:20-alpine AS admin-builder

WORKDIR /build/admin-console

COPY admin-console/package.json admin-console/package-lock.json ./
RUN npm ci

COPY admin-console/ ./
RUN npm run build


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app ./app
COPY config ./config
COPY admin-console/package.json ./admin-console/package.json
COPY --from=admin-builder /build/admin-console/dist ./admin-console/dist

EXPOSE 80

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-80}"]
