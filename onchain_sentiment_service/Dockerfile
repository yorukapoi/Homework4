FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY backend ./backend
COPY onchain_sentiment_service ./onchain_sentiment_service

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

EXPOSE 8003

CMD ["uvicorn", "onchain_sentiment_service.app.main:app", "--host", "0.0.0.0", "--port", "8003"]


