---
description: Start the development servers for local development
---

# Development Server

Start both the Flask backend and React frontend for local development.

## Prerequisites
- Python virtual environment with dependencies installed
- Node.js dependencies installed (`cd frontend && npm install`)

## Steps

1. **Terminal 1 - Start Flask Backend:**
```bash
source .venv/bin/activate
python3 flask_api/app.py
```
The backend will be available at http://localhost:5000

// turbo
2. **Terminal 2 - Start React Frontend:**
```bash
cd frontend && npm run dev
```
The frontend will be available at http://localhost:5173

## Dashboard Features

- **Dashboard**: Overview of verification results and statistics
- **Pipeline**: Start/stop/monitor the verification pipeline
- **Results**: Browse all verified claims with filtering
- **Docs**: View documentation

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| GET `/api/results` | Get all verification results |
| GET `/api/stats` | Get summary statistics |
| GET `/api/dossier/<id>` | Get dossier for a claim |
| POST `/api/pipeline/run` | Start the pipeline |
| POST `/api/pipeline/cancel` | Cancel running pipeline |
