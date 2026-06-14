import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor
import joblib
import os


def prepare_features(forecast_data: list) -> pd.DataFrame:
    """
    Convert raw forecast API data into ML features.
    """
    df = pd.DataFrame(forecast_data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Time-based features
    df["hour"]       = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["day_of_year"] = df["timestamp"].dt.dayofyear
    df["month"]      = df["timestamp"].dt.month

    # Lag features — previous AQI values
    df["aqi_lag_1"]  = df["aqi"].shift(1).fillna(df["aqi"].mean())
    df["aqi_lag_3"]  = df["aqi"].shift(3).fillna(df["aqi"].mean())
    df["aqi_lag_6"]  = df["aqi"].shift(6).fillna(df["aqi"].mean())
    df["aqi_rolling_mean_6"] = df["aqi"].rolling(6, min_periods=1).mean()

    return df


def train_models(df: pd.DataFrame):
    """
    Train Random Forest and XGBoost models on forecast data.
    Returns both trained models and evaluation metrics.
    """
    feature_cols = [
        "hour", "day_of_week", "day_of_year", "month",
        "aqi_lag_1", "aqi_lag_3", "aqi_lag_6", "aqi_rolling_mean_6",
        "pm2_5", "pm10", "o3", "no2"
    ]

    X = df[feature_cols]
    y = df["aqi"]

    # Train/test split — last 20% as test
    split = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    # Random Forest
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=6,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    rf_pred = rf_model.predict(X_test)
    rf_mae = round(mean_absolute_error(y_test, rf_pred), 3)
    rf_r2  = round(r2_score(y_test, rf_pred), 3)

    # XGBoost
    xgb_model = XGBRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        verbosity=0
    )
    xgb_model.fit(X_train, y_train)
    xgb_pred = xgb_model.predict(X_test)
    xgb_mae = round(mean_absolute_error(y_test, xgb_pred), 3)
    xgb_r2  = round(r2_score(y_test, xgb_pred), 3)

    metrics = {
        "random_forest": {"mae": rf_mae, "r2": rf_r2},
        "xgboost":       {"mae": xgb_mae, "r2": xgb_r2},
        "best_model":    "xgboost" if xgb_mae < rf_mae else "random_forest",
        "train_samples": len(X_train),
        "test_samples":  len(X_test)
    }

    return rf_model, xgb_model, metrics


def generate_predictions(df: pd.DataFrame,
                         rf_model,
                         xgb_model) -> pd.DataFrame:
    """
    Generate AQI predictions using both models on the full dataset.
    """
    feature_cols = [
        "hour", "day_of_week", "day_of_year", "month",
        "aqi_lag_1", "aqi_lag_3", "aqi_lag_6", "aqi_rolling_mean_6",
        "pm2_5", "pm10", "o3", "no2"
    ]

    X = df[feature_cols]

    df["rf_prediction"]  = rf_model.predict(X).clip(1, 5).round().astype(int)
    df["xgb_prediction"] = xgb_model.predict(X).clip(1, 5).round().astype(int)

    # Ensemble — average of both
    df["ensemble_prediction"] = ((df["rf_prediction"] + df["xgb_prediction"]) / 2).round().astype(int)

    return df


def run_forecast_pipeline(forecast_data: list) -> dict:
    """
    Full pipeline: prepare data → train → predict.
    Returns predictions and metrics.
    """
    if len(forecast_data) < 10:
        return {"status": "error", "message": "Not enough forecast data"}

    df = prepare_features(forecast_data)
    rf_model, xgb_model, metrics = train_models(df)
    df = generate_predictions(df, rf_model, xgb_model)

    # Save models
    os.makedirs("models", exist_ok=True)
    joblib.dump(rf_model,  "models/rf_model.pkl")
    joblib.dump(xgb_model, "models/xgb_model.pkl")

    return {
        "status": "success",
        "predictions": df[["timestamp", "aqi", "rf_prediction",
                            "xgb_prediction", "ensemble_prediction",
                            "pm2_5", "pm10", "o3", "no2"]].to_dict("records"),
        "metrics": metrics
    }


if __name__ == "__main__":
    from src.data.fetcher import get_aqi_forecast

    print("Fetching forecast data for Chennai...")
    forecast_data = get_aqi_forecast(13.0827, 80.2707)

    if forecast_data:
        print(f"Got {len(forecast_data)} forecast data points")
        result = run_forecast_pipeline(forecast_data)

        if result["status"] == "success":
            print("\nModel Performance:")
            print(f"  Random Forest — MAE: {result['metrics']['random_forest']['mae']}, R2: {result['metrics']['random_forest']['r2']}")
            print(f"  XGBoost       — MAE: {result['metrics']['xgboost']['mae']}, R2: {result['metrics']['xgboost']['r2']}")
            print(f"  Best model: {result['metrics']['best_model']}")
            print(f"\nFirst 5 predictions:")
            for p in result["predictions"][:5]:
                print(f"  {p['timestamp']} | Actual: {p['aqi']} | RF: {p['rf_prediction']} | XGB: {p['xgb_prediction']}")
    else:
        print("Failed to fetch forecast data")