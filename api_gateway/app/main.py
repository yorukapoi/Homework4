import os
from typing import Any, Dict, List

import pandas as pd
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend import config
from backend.common.db import get_connection


app = FastAPI(title="Crypto Analytics API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Internal microservice URLs (overridable via environment variables)
TECH_SERVICE_URL = os.getenv("TECH_SERVICE_URL", "http://technical-analysis-service:8001")
LSTM_SERVICE_URL = os.getenv("LSTM_SERVICE_URL", "http://lstm-prediction-service:8002")
ONCHAIN_SERVICE_URL = os.getenv(
    "ONCHAIN_SERVICE_URL", "http://onchain-sentiment-service:8003"
)


@app.get("/")
def root() -> Dict[str, Any]:
    return {"message": "Crypto Analytics API Gateway", "docs": "/docs"}


def _fetch_rows(query: str, params: tuple[Any, ...]) -> List[Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


@app.get("/coins")
def get_coins(limit: int = 100) -> List[Dict[str, Any]]:
    """
    List of coins with latest price and basic metrics.

    Logic copied from Homework 3 `get_coins`, so the frontend can stay the same.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT DISTINCT symbol FROM {config.TABLE_NAME}
            ORDER BY symbol ASC LIMIT ?
        """,
            (limit,),
        )
        symbols = [row[0] for row in cursor.fetchall()]

        coins: List[Dict[str, Any]] = []
        for symbol in symbols:
            cursor.execute(
                f"""
                SELECT close, date, volume FROM {config.TABLE_NAME}
                WHERE symbol = ? ORDER BY date DESC LIMIT 1
            """,
                (symbol,),
            )
            latest = cursor.fetchone()
            if not latest:
                continue

            current_price = float(latest[0]) if latest[0] else 0
            latest_date = latest[1]
            latest_volume = float(latest[2]) if latest[2] else 0

            cursor.execute(
                f"""
                SELECT close FROM {config.TABLE_NAME}
                WHERE symbol = ? AND date < ?
                ORDER BY date DESC LIMIT 1
            """,
                (symbol, latest_date),
            )
            prev_row = cursor.fetchone()
            prev_price = float(prev_row[0]) if prev_row and prev_row[0] else current_price

            price_change_24h = (
                (current_price - prev_price) / prev_price * 100 if prev_price > 0 else 0
            )

            cursor.execute(
                f"""
                SELECT high, low, close, volume FROM {config.TABLE_NAME}
                WHERE symbol = ? ORDER BY date DESC LIMIT 7
            """,
                (symbol,),
            )
            week_data = cursor.fetchall()

            week_high = max([float(r[0]) for r in week_data if r[0]], default=0)
            week_low = min(
                [float(r[1]) for r in week_data if r[1] and r[1] > 0], default=0
            )
            week_closes = [float(r[2]) for r in week_data if r[2]]
            week_volumes = [float(r[3]) for r in week_data if r[3]]

            avg_volume = sum(week_volumes) / len(week_volumes) if week_volumes else 0

            if len(week_closes) > 1:
                mean_price = sum(week_closes) / len(week_closes)
                variance = sum((p - mean_price) ** 2 for p in week_closes) / len(
                    week_closes
                )
                volatility = variance ** 0.5
            else:
                volatility = 0

            cursor.execute(
                f"""
                SELECT MAX(close), MIN(close) FROM {config.TABLE_NAME}
                WHERE symbol = ?
            """,
                (symbol,),
            )
            ath_atl = cursor.fetchone()
            ath = float(ath_atl[0]) if ath_atl and ath_atl[0] else 0
            atl = float(ath_atl[1]) if ath_atl and ath_atl[1] else 0

            # Simplified market cap approximation as in HW3
            market_cap = current_price * 1_000_000
            liquidity_score = (avg_volume / market_cap * 100) if market_cap > 0 else 0

            cursor.execute(
                f"""
                SELECT date, close FROM {config.TABLE_NAME}
                WHERE symbol = ? ORDER BY date DESC LIMIT 7
            """,
                (symbol,),
            )
            sparkline_data = [
                {"date": r[0], "price": float(r[1]) if r[1] else 0}
                for r in cursor.fetchall()
            ]

            coins.append(
                {
                    "symbol": symbol,
                    "currentPrice": current_price,
                    "lastDate": latest_date,
                    "priceChange24h": round(price_change_24h, 2),
                    "volume24h": latest_volume,
                    "liquidityScore": round(liquidity_score, 4),
                    "week7High": week_high,
                    "week7Low": week_low,
                    "ath": ath,
                    "atl": atl,
                    "volatility": round(volatility, 2),
                    "sparkline": list(reversed(sparkline_data)),
                }
            )

        conn.close()
        return coins
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/coins/{coin_id}")
def get_coin_details(coin_id: str) -> Dict[str, Any]:
    """
    Detailed metrics for a single coin.

    Direct DB access as in Homework 3.
    """
    try:
        coin_id = coin_id.upper()
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT symbol, close, date, volume FROM {config.TABLE_NAME}
            WHERE symbol = ? ORDER BY date DESC LIMIT 1
        """,
            (coin_id,),
        )
        latest = cursor.fetchone()
        if not latest:
            conn.close()
            raise HTTPException(status_code=404, detail="Coin not found")

        current_price = float(latest[1]) if latest[1] else 0
        latest_date = latest[2]
        latest_volume = float(latest[3]) if latest[3] else 0

        cursor.execute(
            f"""
            SELECT close FROM {config.TABLE_NAME}
            WHERE symbol = ? AND date < ?
            ORDER BY date DESC LIMIT 1
        """,
            (coin_id, latest_date),
        )
        prev_row = cursor.fetchone()
        prev_price = float(prev_row[0]) if prev_row and prev_row[0] else current_price
        price_change_24h = (
            (current_price - prev_price) / prev_price * 100 if prev_price > 0 else 0
        )

        cursor.execute(
            f"""
            SELECT MIN(close) as low, MAX(close) as high,
                   AVG(close) as avg, COUNT(*) as records
            FROM {config.TABLE_NAME} WHERE symbol = ?
        """,
            (coin_id,),
        )
        stats = cursor.fetchone()

        cursor.execute(
            f"""
            SELECT high, low, close, volume FROM {config.TABLE_NAME}
            WHERE symbol = ? ORDER BY date DESC LIMIT 7
        """,
            (coin_id,),
        )
        week_data = cursor.fetchall()

        week_high = max([float(r[0]) for r in week_data if r[0]], default=0)
        week_low = min(
            [float(r[1]) for r in week_data if r[1] and r[1] > 0], default=0
        )
        week_closes = [float(r[2]) for r in week_data if r[2]]
        week_volumes = [float(r[3]) for r in week_data if r[3]]

        if len(week_closes) > 1:
            mean_price = sum(week_closes) / len(week_closes)
            variance = sum((p - mean_price) ** 2 for p in week_closes) / len(
                week_closes
            )
            volatility = variance ** 0.5
        else:
            volatility = 0

        total_volume = sum(week_volumes) if week_volumes else 0
        total_prices = sum(
            [float(r[2]) * float(r[3]) for r in week_data if r[2] and r[3]]
        )
        vwap = (total_prices / total_volume) if total_volume > 0 else 0

        market_cap = current_price * 1_000_000
        avg_volume = sum(week_volumes) / len(week_volumes) if week_volumes else 0
        liquidity_score = (avg_volume / market_cap * 100) if market_cap > 0 else 0

        conn.close()

        return {
            "symbol": latest[0],
            "currentPrice": current_price,
            "lastUpdate": latest_date,
            "priceChange24h": round(price_change_24h, 2),
            "volume24h": latest_volume,
            "low52w": float(stats[0]) if stats[0] else 0,
            "high52w": float(stats[1]) if stats[1] else 0,
            "avgPrice": float(stats[2]) if stats[2] else 0,
            "totalRecords": stats[3],
            "week7High": week_high,
            "week7Low": week_low,
            "volatility": round(volatility, 2),
            "vwap": round(vwap, 2),
            "liquidityScore": round(liquidity_score, 4),
            "marketCap": market_cap,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/coins/{coin_id}/history")
def get_coin_history(coin_id: str, days: int = 365) -> Dict[str, Any]:
    """
    OHLCV history for `coin_id` over the last `days` rows.
    """
    try:
        coin_id = coin_id.upper()
        rows = _fetch_rows(
            f"""
            SELECT date, open, high, low, close, volume
            FROM {config.TABLE_NAME}
            WHERE symbol = ? ORDER BY date DESC LIMIT ?
        """,
            (coin_id, days),
        )
        if not rows:
            raise HTTPException(status_code=404, detail="No data found")

        history: List[Dict[str, Any]] = []
        for row in reversed(rows):
            history.append(
                {
                    "date": row[0],
                    "open": float(row[1]) if row[1] else 0,
                    "high": float(row[2]) if row[2] else 0,
                    "low": float(row[3]) if row[3] else 0,
                    "close": float(row[4]) if row[4] else 0,
                    "volume": float(row[5]) if row[5] else 0,
                }
            )

        return {"symbol": coin_id, "data": history}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/compare")
def compare_coins(coin1: str, coin2: str, days: int = 365) -> Dict[str, Any]:
    """
    Compare two coins side-by-side, returning their OHLCV history.
    """
    try:
        coin1, coin2 = coin1.upper(), coin2.upper()
        if coin1 == coin2:
            raise HTTPException(status_code=400, detail="Coins must be different")

        conn = get_connection()
        cursor = conn.cursor()

        def get_history(symbol: str) -> List[Any]:
            cursor.execute(
                f"""
                SELECT date, open, high, low, close, volume
                FROM {config.TABLE_NAME}
                WHERE symbol = ? ORDER BY date DESC LIMIT ?
            """,
                (symbol, days),
            )
            return cursor.fetchall()

        rows1 = get_history(coin1)
        rows2 = get_history(coin2)
        conn.close()

        if not rows1:
            raise HTTPException(status_code=404, detail=f"{coin1} not found")
        if not rows2:
            raise HTTPException(status_code=404, detail=f"{coin2} not found")

        def format_data(rows: List[Any]) -> List[Dict[str, Any]]:
            return [
                {
                    "date": r[0],
                    "open": float(r[1]) if r[1] else 0,
                    "high": float(r[2]) if r[2] else 0,
                    "low": float(r[3]) if r[3] else 0,
                    "close": float(r[4]) if r[4] else 0,
                    "volume": float(r[5]) if r[5] else 0,
                }
                for r in reversed(rows)
            ]

        return {
            "coin1": {"symbol": coin1, "data": format_data(rows1)},
            "coin2": {"symbol": coin2, "data": format_data(rows2)},
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/coins/{coin_id}/technical")
def get_technical_analysis(coin_id: str, timeframe: str = "1m") -> Dict[str, Any]:
    """
    Proxy to the technical analysis microservice.
    """
    coin_id = coin_id.upper()
    try:
        resp = requests.get(
            f"{TECH_SERVICE_URL}/technical/{coin_id}",
            params={"timeframe": timeframe},
            timeout=30,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/coins/{coin_id}/predict")
def get_price_prediction(
    coin_id: str, lookback: int = 30, epochs: int = 15
) -> Dict[str, Any]:
    """
    Proxy to the LSTM prediction microservice.
    """
    coin_id = coin_id.upper()
    try:
        resp = requests.get(
            f"{LSTM_SERVICE_URL}/predict/{coin_id}",
            params={"lookback": lookback, "epochs": epochs, "use_cache": True},
            timeout=60,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/coins/{coin_id}/onchain-sentiment")
def get_onchain_sentiment(coin_id: str) -> Dict[str, Any]:
    """
    Proxy to the on-chain & sentiment microservice.
    """
    coin_id = coin_id.upper()
    try:
        resp = requests.get(
            f"{ONCHAIN_SERVICE_URL}/onchain-sentiment/{coin_id}",
            timeout=60,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


