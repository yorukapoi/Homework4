from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from backend import config
from backend.common.db import get_connection
from backend.analytics.facade import AnalyticsFacade


app = FastAPI(title="Technical Analysis Service", version="1.0.0")

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
    return {"status": "ok", "service": "technical_analysis"}


@app.get("/technical/{symbol}")
def get_technical(symbol: str, timeframe: str = "1m") -> dict:
    """
    Compute technical indicators for `symbol`.

    This mirrors the Homework 3 `/coins/{coin_id}/technical` endpoint,
    but focuses only on technical analysis and delegates the actual
    computation to the Strategy/Facade layer.
    """
    symbol = symbol.upper()

    timeframe_map = {"1d": 1, "1w": 7, "1m": 30}
    if timeframe not in timeframe_map:
        raise HTTPException(
            status_code=400, detail="Invalid timeframe. Use 1d, 1w, or 1m"
        )

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # We pull up to 200 records like in Homework 3, enough for all indicators.
        cursor.execute(
            f"""
            SELECT date, open, high, low, close, volume
            FROM {config.TABLE_NAME}
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT 200
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

        result = facade.get_technical(symbol=symbol, df=df, timeframe=timeframe)
        if "error" in result:
            # Return strategy errors directly (e.g. not enough data)
            return result

        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


