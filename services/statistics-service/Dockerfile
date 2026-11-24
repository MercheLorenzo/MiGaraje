FROM python:3.12-slim AS production
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && groupadd -r migaraje && useradd -r -g migaraje migaraje
COPY app ./app
USER migaraje
EXPOSE 8003
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8003"]
