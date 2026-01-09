"""
Technical analysis strategy.

This wraps the Homework 3 `calculate_technical_indicators` logic behind
the common `AnalyticsStrategy` interface so it can be used interchangeably
with other analytics strategies.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
from ta.trend import SMAIndicator, EMAIndicator, WMAIndicator, CCIIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volume import MFIIndicator

from .base import AnalyticsStrategy


def _calculate_technical_indicators(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Core implementation copied from Homework 3 `technical_analysis.calculate_technical_indicators`.

    Returns a dictionary with moving averages, oscillators and trading signals
    for the last available bar in the DataFrame.
    """
    if len(df) < 50:
        return None

    df = df.copy()
    df = df.sort_values("date")

    indicators: Dict[str, Any] = {
        "ma": {},
        "oscillators": {},
        "signals": {},
    }

    # Moving averages
    df["sma_20"] = SMAIndicator(close=df["close"], window=20).sma_indicator()
    df["ema_20"] = EMAIndicator(close=df["close"], window=20).ema_indicator()
    df["wma_20"] = WMAIndicator(close=df["close"], window=20).wma()

    # VWAP approximation
    df["typical_price"] = (df["high"] + df["low"] + df["close"]) / 3
    df["cum_vol"] = df["volume"].cumsum()
    df["cum_tp_vol"] = (df["typical_price"] * df["volume"]).cumsum()
    df["vwap"] = df["cum_tp_vol"] / df["cum_vol"]

    # Manual WMA (window 20) for compatibility with original implementation
    n = 20
    if len(df) >= n:
        wma_values = []
        for i in range(len(df)):
            if i < n - 1:
                wma_values.append(None)
            else:
                window_data = df["close"].iloc[i - n + 1 : i + 1]
                weights = range(1, n + 1)
                wma = sum(w * p for w, p in zip(weights, window_data)) / sum(weights)
                wma_values.append(wma)
        df["wma_20"] = wma_values

    # Hull Moving Average approximation (period 20)
    hma_period = 20
    if len(df) >= hma_period:
        half_length = int(hma_period / 2)
        sqrt_length = int(hma_period ** 0.5)

        wma_half = WMAIndicator(close=df["close"], window=half_length).wma()
        wma_full = WMAIndicator(close=df["close"], window=hma_period).wma()

        raw_hma = 2 * wma_half - wma_full
        df["hma_20"] = WMAIndicator(close=raw_hma, window=sqrt_length).wma()
    else:
        df["hma_20"] = None

    # Oscillators
    df["rsi_14"] = RSIIndicator(close=df["close"], window=14).rsi()

    macd_indicator = MACD(close=df["close"], window_slow=26, window_fast=12, window_sign=9)
    df["macd"] = macd_indicator.macd()
    df["macd_signal"] = macd_indicator.macd_signal()
    df["macd_hist"] = macd_indicator.macd_diff()

    stoch = StochasticOscillator(
        high=df["high"], low=df["low"], close=df["close"], window=14, smooth_window=3
    )
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()

    df["cci_20"] = CCIIndicator(
        high=df["high"], low=df["low"], close=df["close"], window=20
    ).cci()
    df["mfi_14"] = MFIIndicator(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        volume=df["volume"],
        window=14,
    ).money_flow_index()

    last_row = df.iloc[-1]

    # Moving averages
    indicators["ma"]["sma_20"] = (
        round(float(last_row["sma_20"]), 2) if pd.notna(last_row["sma_20"]) else None
    )
    indicators["ma"]["ema_20"] = (
        round(float(last_row["ema_20"]), 2) if pd.notna(last_row["ema_20"]) else None
    )
    indicators["ma"]["wma_20"] = (
        round(float(last_row["wma_20"]), 2) if pd.notna(last_row["wma_20"]) else None
    )
    indicators["ma"]["hma_20"] = (
        round(float(last_row["hma_20"]), 2) if pd.notna(last_row["hma_20"]) else None
    )
    indicators["ma"]["vwap"] = (
        round(float(last_row["vwap"]), 2) if pd.notna(last_row["vwap"]) else None
    )

    # Oscillators
    rsi_val = float(last_row["rsi_14"]) if pd.notna(last_row["rsi_14"]) else None
    indicators["oscillators"]["rsi_14"] = round(rsi_val, 2) if rsi_val else None

    if pd.notna(last_row.get("macd")) and pd.notna(last_row.get("macd_signal")):
        indicators["oscillators"]["macd"] = {
            "macd": round(float(last_row["macd"]), 2),
            "signal": round(float(last_row["macd_signal"]), 2),
            "hist": (
                round(float(last_row["macd_hist"]), 2)
                if pd.notna(last_row.get("macd_hist"))
                else None
            ),
        }
    else:
        indicators["oscillators"]["macd"] = None

    if pd.notna(last_row.get("stoch_k")) and pd.notna(last_row.get("stoch_d")):
        indicators["oscillators"]["stochastic"] = {
            "k": round(float(last_row["stoch_k"]), 2),
            "d": round(float(last_row["stoch_d"]), 2),
        }
    else:
        indicators["oscillators"]["stochastic"] = None

    cci_val = float(last_row["cci_20"]) if pd.notna(last_row["cci_20"]) else None
    indicators["oscillators"]["cci_20"] = round(cci_val, 2) if cci_val else None

    mfi_val = float(last_row["mfi_14"]) if pd.notna(last_row["mfi_14"]) else None
    indicators["oscillators"]["mfi_14"] = round(mfi_val, 2) if mfi_val else None

    # Signals
    if rsi_val:
        if rsi_val < 30:
            indicators["signals"]["rsi"] = "buy"
        elif rsi_val > 70:
            indicators["signals"]["rsi"] = "sell"
        else:
            indicators["signals"]["rsi"] = "neutral"
    else:
        indicators["signals"]["rsi"] = "neutral"

    if indicators["oscillators"]["macd"]:
        macd_val = indicators["oscillators"]["macd"]["macd"]
        signal_val = indicators["oscillators"]["macd"]["signal"]
        if macd_val > signal_val:
            indicators["signals"]["macd"] = "buy"
        elif macd_val < signal_val:
            indicators["signals"]["macd"] = "sell"
        else:
            indicators["signals"]["macd"] = "neutral"
    else:
        indicators["signals"]["macd"] = "neutral"

    if indicators["oscillators"]["stochastic"]:
        k_val = indicators["oscillators"]["stochastic"]["k"]
        if k_val > 80:
            indicators["signals"]["stochastic"] = "sell"
        elif k_val < 20:
            indicators["signals"]["stochastic"] = "buy"
        else:
            indicators["signals"]["stochastic"] = "neutral"
    else:
        indicators["signals"]["stochastic"] = "neutral"

    buy_count = sum(
        1
        for s in [
            indicators["signals"]["rsi"],
            indicators["signals"]["macd"],
            indicators["signals"]["stochastic"],
        ]
        if s == "buy"
    )
    sell_count = sum(
        1
        for s in [
            indicators["signals"]["rsi"],
            indicators["signals"]["macd"],
            indicators["signals"]["stochastic"],
        ]
        if s == "sell"
    )

    if buy_count >= 2:
        indicators["signals"]["overall"] = "buy"
    elif sell_count >= 2:
        indicators["signals"]["overall"] = "sell"
    else:
        indicators["signals"]["overall"] = "neutral"

    return indicators


class TechnicalAnalysisStrategy(AnalyticsStrategy):
    """Strategy for computing technical indicators on OHLCV data."""

    def analyze(self, df: pd.DataFrame, symbol: str, **_: Any) -> Dict[str, Any]:
        indicators = _calculate_technical_indicators(df)
        if not indicators:
            return {
                "error": "not_enough_data",
                "required": 50,
                "available": len(df),
            }
        return {
            "symbol": symbol,
            "indicators": indicators,
        }


