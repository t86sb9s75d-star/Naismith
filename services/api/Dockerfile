# Build context is the repo root (see docker-compose.yml) so the service can
# copy in the shared constitution/ directory it surfaces at runtime.
FROM python:3.12-slim

WORKDIR /app

COPY services/api/pyproject.toml services/api/README.md ./services/api/
COPY services/api/src ./services/api/src
COPY constitution ./constitution

# Include the Postgres driver: the composed stack uses DATABASE_URL=postgres...
RUN pip install --no-cache-dir "./services/api[postgres]"

ENV NAISMITH_HOST=0.0.0.0 \
    NAISMITH_PORT=8000 \
    PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["naismith-api"]
