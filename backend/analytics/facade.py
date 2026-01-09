"""
Analytics facade.

This module implements the Facade pattern to provide a single, simple
entry point for all analytics capabilities:

- Technical indicators
- LSTM-based price prediction
- On-chain metrics and sentiment

API and microservices use this class instead of talking directly to
individual strategy implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd

from .strategies.base import AnalyticsStrategy
from .strategies.lstm import LSTMPredictionStrategy
from .strategies.onchain import OnchainSentimentStrategy
from .strategies.technical import TechnicalAnalysisStrategy


@dataclass
class AnalyticsFacade:
    """
    Facade that coordinates all analytics strategies.

    The facade hides the details of how data is passed into individual
    strategies and provides small, purpose-specific methods for the API
    layer and microservices to call.
    """

    technical_strategy: AnalyticsStrategy | None = None
    lstm_strategy: AnalyticsStrategy | None = None
    onchain_strategy: AnalyticsStrategy | None = None

    def __post_init__(self) -> None:
        # Lazy defaults so the facade can also be constructed with custom strategies
        if self.technical_strategy is None:
            self.technical_strategy = TechnicalAnalysisStrategy()
        if self.lstm_strategy is None:
            self.lstm_strategy = LSTMPredictionStrategy()
        if self.onchain_strategy is None:
            self.onchain_strategy = OnchainSentimentStrategy()

    @staticmethod
    def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize incoming OHLCV data frame:
        - Ensure we operate on a copy
        - Sort by date ascending
        """
        prepared = df.copy()
        if "date" in prepared.columns:
            prepared = prepared.sort_values("date")
        return prepared

    # Public, high-level methods used by services/API

    def get_technical(self, symbol: str, df: pd.DataFrame, timeframe: str = "1m") -> Dict[str, Any]:
        """
        Compute technical indicators for the given symbol.

        The timeframe is kept for API compatibility, but the strategy itself
        focuses on the last ~200 points passed in the DataFrame.
        """
        prepared_df = self._prepare_df(df)
        result = self.technical_strategy.analyze(prepared_df, symbol)

        # If the strategy already returns an error payload, just forward it.
        if "error" in result:
            return result

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "indicators": result.get("indicators", result),
        }

    def get_prediction(
        self,
        symbol: str,
        df: pd.DataFrame,
        lookback: int = 30,
        epochs: int = 15,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate an LSTM-based next-close prediction for the given symbol.

        Delegates details (training vs cached model, metrics calculation)
        to the LSTM strategy.
        """
        prepared_df = self._prepare_df(df)
        return self.lstm_strategy.analyze(
            prepared_df,
            symbol,
            lookback=lookback,
            epochs=epochs,
            use_cache=use_cache,
        )

    def get_onchain_sentiment(self, symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute on-chain metrics, sentiment analysis and a combined signal
        for the given symbol.
        """
        prepared_df = self._prepare_df(df)
        return self.onchain_strategy.analyze(prepared_df, symbol)


