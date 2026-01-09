"""
LSTM prediction strategy.

This wraps the Homework 3 LSTM training/prediction logic behind the
`AnalyticsStrategy` interface so that price prediction is pluggable.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler

from .base import AnalyticsStrategy

try:
    from tensorflow import keras  # noqa: F401
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout

    TENSORFLOW_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    TENSORFLOW_AVAILABLE = False

import os


def _create_sequences(data: np.ndarray, lookback: int) -> tuple[np.ndarray, np.ndarray]:
    """Create rolling window sequences for LSTM input."""
    X, y = [], []
    for i in range(lookback, len(data)):
        X.append(data[i - lookback : i])
        # close price is at index 3
        y.append(data[i, 3])
    return np.array(X), np.array(y)


def _train_lstm_model(df: pd.DataFrame, lookback: int = 30, epochs: int = 15) -> Dict[str, Any]:
    """Core LSTM training and validation copied from Homework 3."""
    if not TENSORFLOW_AVAILABLE:
        return {
            "error": "tensorflow_not_installed",
            "message": "TensorFlow is required for LSTM predictions",
        }

    if len(df) < lookback * 2:
        return {
            "error": "not_enough_data",
            "required": lookback * 2,
            "available": len(df),
        }

    df = df.copy().sort_values("date")
    features = df[["open", "high", "low", "close", "volume"]].values

    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(features)

    X, y = _create_sequences(scaled_data, lookback)

    # 70/30 split for train/validation
    split_idx = int(len(X) * 0.7)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]

    model = Sequential(
        [
            LSTM(50, activation="relu", return_sequences=True, input_shape=(lookback, 5)),
            Dropout(0.2),
            LSTM(50, activation="relu"),
            Dropout(0.2),
            Dense(1),
        ]
    )

    model.compile(optimizer="adam", loss="mse")

    model.fit(
        X_train,
        y_train,
        epochs=epochs,
        batch_size=32,
        validation_data=(X_val, y_val),
        verbose=0,
    )

    # Evaluate on validation set
    y_pred = model.predict(X_val, verbose=0)

    y_val_actual = y_val.reshape(-1, 1)
    dummy_val = np.zeros((len(y_val_actual), 5))
    dummy_val[:, 3] = y_val_actual.flatten()
    y_val_inv = scaler.inverse_transform(dummy_val)[:, 3]

    dummy_pred = np.zeros((len(y_pred), 5))
    dummy_pred[:, 3] = y_pred.flatten()
    y_pred_inv = scaler.inverse_transform(dummy_pred)[:, 3]

    rmse = np.sqrt(mean_squared_error(y_val_inv, y_pred_inv))
    mape = mean_absolute_percentage_error(y_val_inv, y_pred_inv) * 100
    r2 = r2_score(y_val_inv, y_pred_inv)

    # Next-day prediction
    last_sequence = scaled_data[-lookback:].reshape(1, lookback, 5)
    next_pred = model.predict(last_sequence, verbose=0)

    dummy_next = np.zeros((1, 5))
    dummy_next[:, 3] = next_pred.flatten()
    next_close = scaler.inverse_transform(dummy_next)[0, 3]

    return {
        "model": model,
        "metrics": {
            "rmse": round(float(rmse), 2),
            "mape": round(float(mape), 2),
            "r2": round(float(r2), 4),
        },
        "prediction": {
            "next_close": round(float(next_close), 2),
        },
    }


def _models_dir() -> str:
    folder = "models"
    os.makedirs(folder, exist_ok=True)
    return folder


def _save_model(model: Any, symbol: str) -> None:
    """Save trained model to disk for future reuse."""
    path = os.path.join(_models_dir(), f"{symbol}_lstm.h5")
    model.save(path)


def _load_cached_model(symbol: str) -> Any | None:
    """Load a cached Keras model from disk if it exists."""
    path = os.path.join(_models_dir(), f"{symbol}_lstm.h5")
    if not os.path.exists(path):
        return None
    try:
        return load_model(path)
    except Exception:
        return None


def _predict_with_lstm(
    df: pd.DataFrame, symbol: str, lookback: int = 30, epochs: int = 15, use_cache: bool = True
) -> Dict[str, Any]:
    """
    Public function equivalent to Homework 3 `predict_with_lstm`, returning
    either an error dictionary or metrics + prediction (and cache info).
    """
    if use_cache:
        cached_model = _load_cached_model(symbol)
        if cached_model is not None:
            try:
                if len(df) < lookback:
                    return {
                        "error": "not_enough_data",
                        "required": lookback,
                        "available": len(df),
                    }

                df = df.sort_values("date")
                features = df[["open", "high", "low", "close", "volume"]].values

                scaler = MinMaxScaler()
                scaled_data = scaler.fit_transform(features)

                last_sequence = scaled_data[-lookback:].reshape(1, lookback, 5)
                next_pred = cached_model.predict(last_sequence, verbose=0)

                dummy_next = np.zeros((1, 5))
                dummy_next[:, 3] = next_pred.flatten()
                next_close = scaler.inverse_transform(dummy_next)[0, 3]

                return {
                    "cached": True,
                    "prediction": {
                        "next_close": round(float(next_close), 2),
                    },
                }
            except Exception:
                # If cached model fails for any reason, fall back to training a new one
                pass

    result = _train_lstm_model(df, lookback=lookback, epochs=epochs)
    if "error" in result:
        return result

    model = result.get("model")
    if model is not None:
        _save_model(model, symbol)
        del result["model"]

    return result


class LSTMPredictionStrategy(AnalyticsStrategy):
    """Strategy for next-close price prediction using an LSTM model."""

    def analyze(
        self, df: pd.DataFrame, symbol: str, **kwargs: Any
    ) -> Dict[str, Any]:
        lookback = int(kwargs.get("lookback", 30))
        epochs = int(kwargs.get("epochs", 15))
        use_cache = bool(kwargs.get("use_cache", True))

        result = _predict_with_lstm(
            df=df,
            symbol=symbol,
            lookback=lookback,
            epochs=epochs,
            use_cache=use_cache,
        )

        # Attach symbol and lookback for consistency with HW3 API
        if "error" in result:
            return result

        response: Dict[str, Any] = {"symbol": symbol, "lookback": lookback}
        if "metrics" in result:
            response["metrics"] = result["metrics"]
        if "prediction" in result:
            response["prediction"] = result["prediction"]
        if "cached" in result:
            response["cached"] = result["cached"]

        return response


