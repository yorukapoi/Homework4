from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from backend import config
from backend.common.db import get_connection
from backend.analytics.facade import AnalyticsFacade


app = FastAPI(title="LSTM Prediction Service", version="1.0.0")

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
    return {"status": "ok", "service": "lstm_prediction"}


@app.get("/predict/{symbol}")
def get_price_prediction(
    symbol: str, lookback: int = 30, epochs: int = 15, use_cache: bool = True
) -> dict:
    """
    LSTM-based next-close prediction for `symbol`.

    This mirrors the Homework 3 `/coins/{coin_id}/predict` endpoint, but
    is isolated as a dedicated microservice.
    """
    symbol = symbol.upper()

    if lookback < 5 or lookback > 100:
        raise HTTPException(
            status_code=400, detail="Lookback must be between 5 and 100"
        )
    if epochs < 5 or epochs > 50:
        raise HTTPException(status_code=400, detail="Epochs must be between 5 and 50")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT date, open, high, low, close, volume
            FROM {config.TABLE_NAME}
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT 500
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

        result = facade.get_prediction(
            symbol=symbol,
            df=df,
            lookback=lookback,
            epochs=epochs,
            use_cache=use_cache,
        )

        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


