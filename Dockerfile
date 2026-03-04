FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends sqlite3 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY app/ app/
COPY app.py .
COPY wsgi.py .
COPY scripts/ scripts/

RUN mkdir -p /app/data

EXPOSE 5000

VOLUME ["/app/data"]

STOPSIGNAL SIGTERM

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--graceful-timeout", "25", "wsgi:app"]
