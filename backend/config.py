"""
Configuration for Homework 4 backend services.

This mirrors the Homework 3 configuration so we reuse the same
data model and SQLite database, but keeps the code physically
separate so Homework 3 remains unchanged.
"""

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
COINS_MARKETS_ENDPOINT = f"{COINGECKO_BASE_URL}/coins/markets"
COIN_OHLC_ENDPOINT = f"{COINGECKO_BASE_URL}/coins/{{coin_id}}/ohlc"
BINANCE_BASE_URL = "https://api.binance.com/api/v3"
BINANCE_KLINES_ENDPOINT = f"{BINANCE_BASE_URL}/klines"

VS_CURRENCY = "usd"
MARKETS_PER_PAGE = 250
TOTAL_SYMBOLS = 1000
MIN_VOLUME = 0

HISTORICAL_DAYS_DEFAULT = 3650
REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.0

# We intentionally keep the same DB name and table as Homework 3.
# The physical file can be overridden in production via CRYPTO_DB_PATH env var.
DB_NAME = "homework-1-main-homework3/homework3/crypto_data.db"
TABLE_NAME = "crypto_data"


