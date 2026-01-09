"""
Base interfaces for analytics strategies.

The Strategy pattern allows us to define a common interface for different
types of analytics (technical indicators, LSTM prediction, on-chain &
sentiment) while keeping each algorithm in its own class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

import pandas as pd


class AnalyticsStrategy(ABC):
    """
    Common interface for all analytics strategies.

    Each strategy receives a prepared OHLCV DataFrame and a symbol, and
    returns a dictionary with the analytics result or an error payload.
    """

    @abstractmethod
    def analyze(self, df: pd.DataFrame, symbol: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Run the analytics algorithm for the given symbol and data.

        :param df: Historical OHLCV data sorted by date.
        :param symbol: Asset symbol (e.g. BTC, ETH).
        :param kwargs: Strategy-specific options (timeframe, lookback, epochs, etc.).
        :return: Dictionary containing analytics results and/or error information.
        """
        raise NotImplementedError


