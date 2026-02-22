# Kenya Stocks Prototype

Prototype Kenyan stock market dashboard.

## Backend (FastAPI)

```bash
cd backend
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

## Frontend

Open `frontend/index.html` in your browser (double-click or via a simple static server).

It will call `http://127.0.0.1:8000/stocks/sample` to load sample stock data.

Real NSE data + document ingestion coming next.
