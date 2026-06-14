# AQI-Monitor

A lightweight air-quality monitoring and forecasting project. It ingests sensor or external data, runs forecasting models, and produces map visualizations.

## Features
- Fetches and preprocesses AQI data
- Short-term forecasting using models in `models/` and `src/ml/forecaster.py`
- Map visualization helpers in `src/utils/map_utils.py`
- Simple web or script-driven runner via `app.py`

## Requirements
- Python 3.9+
- See `requirements.txt` for exact dependencies

## Installation
1. Create and activate a virtual environment:

```
python -m venv .venv
.\.venv\Scripts\activate
```

2. Install dependencies:

```
pip install -r requirements.txt
```

## Running locally
- Run the main application:

```
python app.py
```

- Or run individual modules for development:

```
python -m src.data.fetcher
python -m src.ml.forecaster
```

## Docker
Build and run the Docker image (if Dockerfile is present):

```
docker build -t aqi-monitor:latest .
docker run -p 8080:8080 aqi-monitor:latest
```

## Project structure
- `app.py` — application entry point
- `Dockerfile` — container image definition
- `requirements.txt` — Python dependencies
- `test_map.html` — example map output
- `data/` — raw and processed data
- `models/` — trained model artifacts
- `src/` — source modules
  - `src/data/fetcher.py` — data ingestion
  - `src/ml/forecaster.py` — forecasting pipeline
  - `src/utils/map_utils.py` — map visualization helpers

## Data & Models
- Place raw data in `data/` and trained models in `models/`.
- The repository does not contain large datasets or model binaries by default.

