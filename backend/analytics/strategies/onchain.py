"""
On-chain metrics and sentiment analysis strategy.

This wraps the Homework 3 `onchain_sentiment` module behind the
`AnalyticsStrategy` interface.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from .base import AnalyticsStrategy

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    VADER_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    VADER_AVAILABLE = False

try:
    import feedparser

    FEEDPARSER_AVAILABLE = True
except ImportError:  # pragma: no cover
    FEEDPARSER_AVAILABLE = False

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:  # pragma: no cover
    REQUESTS_AVAILABLE = False

import re
import random
from datetime import datetime, timedelta  # noqa: F401 (kept for parity with HW3)


def _calculate_onchain_metrics(df: pd.DataFrame, symbol: str) -> Dict[str, Any] | None:
    if len(df) < 7:
        return None

    df = df.copy().sort_values("date")

    latest = df.iloc[-1]
    current_price = float(latest["close"])
    avg_price = df["close"].mean()

    active_addresses = _simulate_active_addresses(df, symbol)
    transaction_count = len(df)
    exchange_flows = _calculate_exchange_flows(df)
    whale_movements = _detect_whale_movements(df)
    hash_rate = _get_hash_rate(symbol)
    tvl = _get_tvl(symbol)
    nvt_ratio = _calculate_nvt_ratio(current_price, df)
    mvrv_ratio = _calculate_mvrv_ratio(current_price, avg_price)

    return {
        "active_addresses": active_addresses,
        "transactions": transaction_count,
        "exchange_flows": exchange_flows,
        "whale_movements": whale_movements,
        "hash_rate": hash_rate,
        "tvl": tvl,
        "nvt_ratio": nvt_ratio,
        "mvrv_ratio": mvrv_ratio,
    }


def _simulate_active_addresses(df: pd.DataFrame, symbol: str) -> int:
    recent_volume = df.tail(30)["volume"].mean()
    base_addresses = {
        "BTC": 900_000,
        "ETH": 500_000,
        "BNB": 200_000,
        "SOL": 150_000,
        "XRP": 100_000,
    }

    base = base_addresses.get(symbol, 50_000)
    volatility_factor = df.tail(7)["close"].std() / df.tail(7)["close"].mean()
    adjustment = 1 + (volatility_factor * 0.5)
    return int(base * adjustment)


def _calculate_exchange_flows(df: pd.DataFrame) -> Dict[str, int]:
    recent_volumes = df.tail(7)["volume"].values
    if len(recent_volumes) < 2:
        return {"inflow": 0, "outflow": 0, "net_flow": 0}

    avg_volume = float(np.mean(recent_volumes))
    latest_volume = float(recent_volumes[-1])

    if latest_volume > avg_volume:
        inflow = int(latest_volume * 0.6)
        outflow = int(latest_volume * 0.4)
    else:
        inflow = int(latest_volume * 0.4)
        outflow = int(latest_volume * 0.6)

    net_flow = inflow - outflow
    return {"inflow": inflow, "outflow": outflow, "net_flow": net_flow}


def _detect_whale_movements(df: pd.DataFrame) -> str:
    volumes = df["volume"].values
    if len(volumes) < 7:
        return "normal"

    percentile_95 = float(np.percentile(volumes, 95))
    latest_volume = float(volumes[-1])

    if latest_volume > percentile_95 * 1.5:
        return "very_high"
    if latest_volume > percentile_95:
        return "high"
    return "normal"


def _get_hash_rate(symbol: str) -> float:
    hash_rates = {
        "BTC": 450,
        "ETH": 0,
        "LTC": 800,
        "BCH": 2.5,
        "BSV": 1.8,
    }
    return float(hash_rates.get(symbol, 0))


def _simulate_tvl(symbol: str) -> int:
    tvl_estimates = {
        "BTC": 48_000_000_000,
        "ETH": 55_000_000_000,
        "BNB": 8_000_000_000,
        "SOL": 4_000_000_000,
        "AVAX": 2_000_000_000,
        "MATIC": 1_500_000_000,
    }
    return int(tvl_estimates.get(symbol, 500_000_000))


def _get_tvl(symbol: str) -> int:
    if not REQUESTS_AVAILABLE:
        return _simulate_tvl(symbol)

    try:
        response = requests.get("https://api.llama.fi/protocols", timeout=5)
        if response.status_code == 200:
            protocols = response.json()

            symbol_map = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "BNB": "bsc",
                "SOL": "solana",
                "AVAX": "avalanche",
            }

            chain_name = symbol_map.get(symbol, symbol.lower())
            total_tvl = 0

            for protocol in protocols:
                if (
                    protocol.get("chain") == chain_name
                    or protocol.get("name", "").lower() == chain_name
                ):
                    total_tvl += protocol.get("tvl", 0)

            if total_tvl > 0:
                return int(total_tvl)

        return _simulate_tvl(symbol)
    except Exception:
        return _simulate_tvl(symbol)


def _calculate_nvt_ratio(current_price: float, df: pd.DataFrame) -> float:
    circulating_supply = 21_000_000
    market_cap = current_price * circulating_supply

    recent_volume = df.tail(30)["volume"].mean()
    daily_transaction_value = recent_volume * current_price

    if daily_transaction_value > 0:
        nvt = market_cap / (daily_transaction_value * 365)
        return round(float(nvt), 2)
    return 0.0


def _calculate_mvrv_ratio(current_price: float, avg_price: float) -> float:
    if avg_price > 0:
        return round(float(current_price / avg_price), 2)
    return 1.0


def _clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[^\w\s]", " ", text)
    text = " ".join(text.split())
    return text


def _generate_mock_sentiment_data(symbol: str) -> List[str]:
    mock_positive = [
        f"{symbol} shows strong bullish momentum with increasing adoption",
        f"Major institutional investor announces {symbol} investment",
        f"{symbol} network activity reaches all-time high",
        f"Positive developments in {symbol} ecosystem drive optimism",
        f"{symbol} technical indicators suggest upward trend",
    ]

    mock_neutral = [
        f"{symbol} price consolidates in narrow range",
        f"Market observers watching {symbol} closely",
        f"{symbol} trading volume remains stable",
    ]

    mock_negative = [
        f"Concerns raised about {symbol} scalability issues",
        f"{symbol} faces regulatory scrutiny in key markets",
        f"Analysts warn of potential {symbol} correction",
    ]

    sentiment_pool = mock_positive * 3 + mock_neutral * 2 + mock_negative
    random.shuffle(sentiment_pool)
    return sentiment_pool[:15]


def _simulate_sentiment(symbol: str) -> Dict[str, Any]:
    positive = random.randint(8, 15)
    neutral = random.randint(3, 8)
    negative = random.randint(2, 6)
    score = random.uniform(0.15, 0.45)

    return {
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "score": round(score, 3),
        "label": "positive",
        "total_analyzed": positive + neutral + negative,
        "note": "Simulated data - VADER not available",
    }


def _fetch_crypto_news(symbol: str) -> List[str]:
    if not FEEDPARSER_AVAILABLE:
        return []

    rss_feeds = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
    ]

    news_texts: List[str] = []
    try:
        for feed_url in rss_feeds:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                if symbol.lower() in title.lower() or symbol.lower() in summary.lower():
                    news_texts.append(f"{title}. {summary}")
        return news_texts[:20]
    except Exception:
        return []


def _fetch_reddit_sentiment(symbol: str) -> List[str]:
    if not REQUESTS_AVAILABLE:
        return []

    try:
        headers = {"User-Agent": "crypto-analytics/1.0"}
        subreddits = ["cryptocurrency", "bitcoin", "ethereum", "cryptomarkets"]
        reddit_texts: List[str] = []

        for subreddit in subreddits:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25"
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", {}).get("children", [])
                for post in posts:
                    post_data = post.get("data", {})
                    title = post_data.get("title", "")
                    selftext = post_data.get("selftext", "")
                    if symbol.upper() in title.upper() or symbol.lower() in title.lower():
                        reddit_texts.append(f"{title}. {selftext}")
        return reddit_texts[:15]
    except Exception:
        return []


def _analyze_sentiment(symbol: str) -> Dict[str, Any]:
    if not VADER_AVAILABLE:
        return _simulate_sentiment(symbol)

    analyzer = SentimentIntensityAnalyzer()
    sentiment_texts: List[str] = []

    sentiment_texts.extend(_fetch_crypto_news(symbol))
    sentiment_texts.extend(_fetch_reddit_sentiment(symbol))

    if not sentiment_texts:
        sentiment_texts = _generate_mock_sentiment_data(symbol)

    positive_count = 0
    neutral_count = 0
    negative_count = 0
    compound_scores: List[float] = []

    for text in sentiment_texts:
        cleaned_text = _clean_text(text)
        if not cleaned_text:
            continue
        scores = analyzer.polarity_scores(cleaned_text)
        compound = scores["compound"]
        compound_scores.append(compound)
        if compound >= 0.05:
            positive_count += 1
        elif compound <= -0.05:
            negative_count += 1
        else:
            neutral_count += 1

    avg_score = sum(compound_scores) / len(compound_scores) if compound_scores else 0

    if avg_score >= 0.05:
        sentiment_label = "positive"
    elif avg_score <= -0.05:
        sentiment_label = "negative"
    else:
        sentiment_label = "neutral"

    return {
        "positive": positive_count,
        "neutral": neutral_count,
        "negative": negative_count,
        "score": round(avg_score, 3),
        "label": sentiment_label,
        "total_analyzed": len(sentiment_texts),
    }


def _generate_combined_signal(
    onchain_metrics: Dict[str, Any], sentiment_data: Dict[str, Any]
) -> str:
    signal_factors: List[int] = []

    # Sentiment contribution
    label = sentiment_data.get("label")
    if label == "positive":
        signal_factors.append(1)
    elif label == "negative":
        signal_factors.append(-1)
    else:
        signal_factors.append(0)

    # Whale movements & exchange flows
    whale_movement = onchain_metrics.get("whale_movements", "normal")
    if whale_movement in ("very_high", "high"):
        net_flow = onchain_metrics.get("exchange_flows", {}).get("net_flow", 0)
        if net_flow > 0:
            signal_factors.append(1)
        elif net_flow < 0:
            signal_factors.append(-1)

    # MVRV ratio
    mvrv = onchain_metrics.get("mvrv_ratio", 1.0)
    if mvrv > 1.5:
        signal_factors.append(1)
    elif mvrv < 0.8:
        signal_factors.append(-1)

    # NVT ratio
    nvt = onchain_metrics.get("nvt_ratio", 0)
    if 0 < nvt < 40:
        signal_factors.append(1)
    elif nvt > 80:
        signal_factors.append(-1)

    if not signal_factors:
        return "neutral"

    avg_signal = sum(signal_factors) / len(signal_factors)
    if avg_signal > 0.3:
        return "bullish"
    if avg_signal < -0.3:
        return "bearish"
    return "neutral"


class OnchainSentimentStrategy(AnalyticsStrategy):
    """
    Strategy that combines on-chain metrics and sentiment analysis to produce
    a single combined market signal (bullish / bearish / neutral).
    """

    def analyze(self, df: pd.DataFrame, symbol: str, **_: Any) -> Dict[str, Any]:
        if len(df) < 7:
            return {
                "error": "not_enough_data",
                "required": 7,
                "available": len(df),
                "message": "Insufficient data for on-chain and sentiment analysis",
            }

        onchain = _calculate_onchain_metrics(df, symbol)
        if not onchain:
            return {
                "error": "calculation_failed",
                "message": "Unable to calculate on-chain metrics",
            }

        sentiment = _analyze_sentiment(symbol)
        combined_signal = _generate_combined_signal(onchain, sentiment)

        return {
            "symbol": symbol,
            "on_chain": onchain,
            "sentiment": sentiment,
            "combined_signal": combined_signal,
        }


