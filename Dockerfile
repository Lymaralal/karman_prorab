FROM python:3.13-slim

WORKDIR /app


RUN apt-get update && apt-get install -y \
    curl \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libharfbuzz-subset0 \
    libfontconfig1 \
    libjpeg62-turbo \
    libopenjp2-7 \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*


RUN pip install --upgrade pip


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .


ENV PORT=8000
EXPOSE 8000


HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
  CMD curl -f http://localhost:8000/health || exit 1


CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.app:app"]