FROM python:3.13-slim

WORKDIR /app


RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*


RUN pip install --upgrade pip


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .


CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--log-level", "debug", "backend.app:app"]