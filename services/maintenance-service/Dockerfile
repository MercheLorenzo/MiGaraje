# Stage 1: Install production dependencies
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Production image
FROM python:3.12-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create a dedicated non-root user
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --create-home app

# Copy installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application code and db migrations
COPY --chown=app:app app/ ./app/
COPY --chown=app:app alembic.ini .
COPY --chown=app:app alembic/ ./alembic/

# Run the application without root privileges
USER 10001:10001

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]