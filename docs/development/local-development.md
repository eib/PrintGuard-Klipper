# Local Development

This guide is for running PrintGuard from source during development.

## Setup

### Backend (FastAPI)

Prerequisites:

- Python **3.13+** (see `pyproject.toml`)

Steps:

```bash
git clone https://github.com/oliverbravery/PrintGuard.git
cd PrintGuard

python -m venv venv
source venv/bin/activate

pip install -e .
pip install -e ./printguard-shared

printguard serve --reload
```

The API will be available at `http://localhost:8000/api`.

### Frontend (WebUI)

Prerequisites:

- Node.js / npm

Steps:

```bash
cd webui
npm install
npm run dev
```

The WebUI will be available at `http://localhost:5173` and will proxy `/api` to `http://localhost:8000`.

### Notes

- On first run, PrintGuard initializes the SQLite database and prints an auto-generated `admin` password to the server logs.
- If you build the WebUI (`webui/dist`), the backend can serve it directly (see `src/printguard/main.py`).

