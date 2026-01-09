"""
Technical Analysis microservice (Homework 4).

Exposes a small FastAPI application that:
- Reads OHLCV data from the shared SQLite database
- Delegates indicator computation to the AnalyticsFacade / TechnicalAnalysisStrategy
"""


