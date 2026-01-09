from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from backend import config
from backend.common.db import get_connection
from backend.analytics.facade import AnalyticsFacade


app = FastAPI(title="On-chain & Sentiment Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

facade = AnalyticsFacade()


@app.get("/health")
def health() -> dict:
  return {"status": "ok", "service": "onchain_sentiment"}


@app.get("/onchain-sentiment/{symbol}")
def get_onchain_sentiment(symbol: str) -> dict:
  """
  Combined on-chain metrics and sentiment analysis for `symbol`.

  Mirrors the Homework 3 `/coins/{coin_id}/onchain-sentiment` endpoint,
  but as a dedicated microservice using the Strategy/Facade layer.
  """
  symbol = symbol.upper()

  try:
      conn = get_connection()
      cursor = conn.cursor()

      cursor.execute(
          f"""
          SELECT date, open, high, low, close, volume
          FROM {config.TABLE_NAME}
          WHERE symbol = ?
          ORDER BY date DESC
          LIMIT 365
      """,
          (symbol,),
      )
      rows = cursor.fetchall()
      conn.close()

      if not rows:
          raise HTTPException(status_code=404, detail="Coin not found")

      df = pd.DataFrame(
          rows, columns=["date", "open", "high", "low", "close", "volume"]
      )

      result = facade.get_onchain_sentiment(symbol=symbol, df=df)
      return result
  except HTTPException:
      raise
  except Exception as exc:
      raise HTTPException(status_code=500, detail=str(exc))


