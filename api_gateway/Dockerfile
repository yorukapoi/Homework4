FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if needed for scientific stack)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Copy shared backend code and gateway app
COPY backend ./backend
COPY api_gateway ./api_gateway

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "api_gateway.app.main:app", "--host", "0.0.0.0", "--port", "8000"]


