# Sarcasm Detection Project

A sarcasm detection system with a FastAPI backend, a Chrome extension for Reddit and YouTube, and optional scrapers/MLOps utilities.

## What You Need

- Python 3.11 recommended
- Chrome or a Chromium-based browser
- A local model in `backend/saved_model/`
- A root `.env` file for API keys and local variables

## Quick Start

1. Create and activate a Python 3.11 virtual environment.
2. Install the backend dependencies from `backend/requirements.txt`.
3. Copy `.env.example` to `.env` and fill in any required keys.
4. Put the trained model files in `backend/saved_model/`.
5. Start the backend with `MODEL_PATH=backend/saved_model`.
6. Load the `extension/` folder unpacked in Chrome.
7. Run `test_local.html` or hit the API endpoints to verify everything works.

## Dependency Files

- `backend/requirements.txt`: backend API and model runtime dependencies.
- `scrapers/requirements.txt`: Reddit and YouTube scraping dependencies.
- `backend/mlops/requirements.txt`: prediction analysis and monitoring dependencies.

## Required Model Files

The trained backend expects these files in `backend/saved_model/`:

- `config.json`
- `model.safetensors` or `pytorch_model.bin`
- `tokenizer.json`
- `tokenizer_config.json`

Keep the config, tokenizer, and weights from the same model export together.

## Backend Setup

```bash
cd <repo-root>
python3.11 -m venv venv311
source venv311/bin/activate
pip install -r backend/requirements.txt
MODEL_PATH=backend/saved_model python backend/main.py
```

API endpoints:

- `GET /`
- `GET /health`
- `POST /predict`
- `POST /predict/batch`
- `GET /stats`

Docs: `http://localhost:8000/docs`

## Environment Variables

Use a root `.env` file. See [`.env.example`](.env.example) for the expected keys. Source those variables or export them in your shell before running the backend or scrapers, because the backend reads `MODEL_PATH` from the process environment.

## Extension

Load the `extension/` folder unpacked in Chrome after the backend is running locally.

## Scrapers

If you use the scrapers, set:

- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USER_AGENT`
- `YOUTUBE_API_KEY`

## Additional Docs

- [Execution Guide](EXECUTION_GUIDE.md)
