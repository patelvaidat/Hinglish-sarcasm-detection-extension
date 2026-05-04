# Project Execution Guide

This guide reflects the current project layout and runtime flow for the sarcasm detection backend, browser extension, scrapers, and MLOps utilities.

## 0. Quick Setup Checklist

1. Create and activate a Python 3.11 virtual environment.
2. Install backend dependencies from `backend/requirements.txt`.
3. Create a root `.env` file with any API keys you need.
4. Put the trained model in `backend/saved_model/`.
5. Start the backend with `MODEL_PATH=backend/saved_model`.
6. Open `chrome://extensions/` and load the `extension/` folder.
7. Run the API checks or open `test_local.html`.

## 1. What You Need

- macOS, Windows, or Linux.
- Python 3.11 recommended.
- Chrome or a Chromium-based browser for the extension.
- A local fine-tuned model directory for the trained backend flow.
- A root `.env` file for API keys and local environment variables.
- Internet access only if you are installing dependencies or running scrapers against external APIs.

## 2. Project Parts

- `backend/`: FastAPI API, local model loading, prediction logging, MLOps helpers.
- `extension/`: Chrome extension that scrapes Reddit/YouTube and calls the local backend.
- `scrapers/`: Optional standalone Reddit and YouTube scraping scripts.
- `test_local.html`: Browser-based local test page.
- `quick_test.ps1`: Windows PowerShell API smoke test.
- `backend/start.sh`: Bash startup helper for the backend.

## 3. Dependency Files

- `backend/requirements.txt`: backend API and model runtime dependencies.
- `scrapers/requirements.txt`: Reddit and YouTube scraping dependencies.
- `backend/mlops/requirements.txt`: prediction analysis and monitoring dependencies.

## 4. Python Environment Setup

### 4.1. Recommended setup on macOS/Linux
```bash
cd <repo-root>
python3.11 -m venv venv311
source venv311/bin/activate
python -m pip install --upgrade pip
```

### 4.2. Install backend dependencies
```bash
cd <repo-root>/backend
pip install -r requirements.txt
```

### 4.3. Install scraper dependencies when needed
```bash
cd <repo-root>/scrapers
pip install -r requirements.txt
```

### 4.4. Install MLOps dependencies when needed
```bash
cd <repo-root>/backend/mlops
pip install -r requirements.txt
```

## 4. Backend Requirements

### 4.1. Backend Python packages

The backend currently depends on:

- `fastapi`
- `uvicorn[standard]`
- `torch`
- `transformers`
- `pydantic`
- `python-multipart`
- `vaderSentiment`
- `scikit-fuzzy`
- `scipy`
- `numpy`

### 4.2. Model files required for the trained backend

Place the trained model in `backend/saved_model/` and make sure at least these files exist:

- `config.json`
- `model.safetensors` or `pytorch_model.bin`
- `tokenizer.json`
- `tokenizer_config.json`

These are the files the backend checks for first. Other tokenizer artifacts such as `special_tokens_map.json` or `vocab.txt` are fine to keep if your model export includes them.

If you are swapping in a different checkpoint, keep the model weights, config, and tokenizer files from the same export together. Mismatched tokenizer or config files are a common source of load-time errors.

### 4.3. Required runtime behavior

- The backend loads the model from `MODEL_PATH` if set.
- If `MODEL_PATH` is not set, it falls back to `backend/saved_model` relative to the backend file location.
- The API listens on port `8000`.

### 4.4. Optional environment variables

Create a root `.env` file if you are using the scraper tools or want to make the local backend path explicit.

Example values:

```bash
MODEL_PATH=backend/saved_model
YOUTUBE_API_KEY=your_youtube_api_key_here
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=SarcasmDetector/1.0
```

Only set the keys you actually use. Keep real credentials out of source control.

## 5. Backend Startup

### 5.1. Trained model mode

From the repository root:

```bash
cd <repo-root>
source venv311/bin/activate
MODEL_PATH=backend/saved_model python backend/main.py
```

If you prefer to run from inside `backend/`:

```bash
cd <repo-root>/backend
source ../venv311/bin/activate
MODEL_PATH=./saved_model python main.py
```

### 5.2. Test mode without a trained model

Use this when you want a quick local demo without the fine-tuned model artifacts:

```bash
cd <repo-root>/backend
source ../venv311/bin/activate
python main_test.py
```

### 5.3. Optional startup helper

The `backend/start.sh` script is intended as a convenience launcher, but the most reliable current flow is still to set `MODEL_PATH` explicitly and start the backend from the repository root.

## 6. API Endpoints

The backend currently exposes:

- `GET /`
- `GET /health`
- `POST /predict`
- `POST /predict/batch`
- `GET /stats`

The interactive docs are available at `http://localhost:8000/docs` when the API is running.

## 7. API Testing

### 7.1. Manual checks

```bash
curl http://localhost:8000/health
curl -X POST "http://localhost:8000/predict" -H "Content-Type: application/json" -d '{"text":"Oh great, another meeting","platform":"twitter"}'
curl http://localhost:8000/stats
```

### 7.2. Batch prediction check

```bash
curl -X POST "http://localhost:8000/predict/batch" \
  -H "Content-Type: application/json" \
  -d '[{"text":"Love working on weekends!","platform":"test"},{"text":"Perfect, just perfect!","platform":"test"}]'
```

### 7.3. Local test page

Open `test_local.html` in a browser after the backend is running.

### 7.4. Windows smoke test

If you are on Windows and have PowerShell available, `quick_test.ps1` runs a quick endpoint check against the local API.

## 8. Chrome Extension

### 8.1. Requirements

- The extension folder can be loaded unpacked into Chrome.
- The backend must be running locally at `http://127.0.0.1:8000` or `http://localhost:8000`.
- The extension is not a standalone predictor; it depends on the backend for inference.

### 8.2. Load unpacked

1. Open `chrome://extensions/`.
2. Enable Developer Mode.
3. Click Load unpacked.
4. Select the `extension` folder.

### 8.3. Extension assets

The extension folder already includes the necessary assets it references, including the manifest, scripts, popup UI, styles, and icons.

## 9. Scrapers

### 9.1. Scraper requirements

- `praw`
- `google-api-python-client`
- `python-dotenv`

### 9.2. Usage

- Put your scraper credentials in the root `.env` file or export them in your shell before running the scripts.
- For Reddit scraping, set `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and `REDDIT_USER_AGENT`.
- For YouTube scraping, set `YOUTUBE_API_KEY`.
- Run the scripts from the `scrapers/` directory.
- Scraped output is written under the scraper data folders in the repo.

## 10. Logs and Monitoring

- Prediction logs are written to `backend/logs/predictions.jsonl`.
- Use `GET /stats` for quick counts and sarcasm rate checks.
- Keep an eye on the backend terminal for model-loading or API errors.

## 11. MLOps Pipeline

### 11.1. MLOps requirements

- `pandas`
- `numpy`

### 11.2. Run the pipeline

```bash
cd <repo-root>/backend
source ../venv311/bin/activate
python mlops/run_pipeline.py
```

## 12. Troubleshooting

- If the backend fails to start, confirm the virtual environment is active and the dependencies are installed.
- If the trained model does not load, check that `MODEL_PATH` points to the correct local folder and that the required files exist.
- If Hugging Face model loading fails, verify that `config.json`, tokenizer files, and weights all came from the same export.
- If the extension shows no results, make sure the backend is already running before scanning a page.
- If scraping fails, verify the `.env` values, API credentials, and network access.