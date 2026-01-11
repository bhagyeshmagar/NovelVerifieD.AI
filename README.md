<div align="center">

# 🔍 NovelVerified.AI

**AI-Powered Novel Claim Verification System**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*Verify character backstory claims against actual novel text using RAG + LLM*

**Team StrawHats - KDSH 2026**

</div>

---

## 📖 Overview

NovelVerified.AI is an intelligent system that determines whether **character backstory claims** about literary works are **supported** or **contradicted** by the actual text of the novels.

### Example

> **Claim:** "Edmond Dantes was imprisoned for fourteen years"  
> **Novel:** *The Count of Monte Cristo*  
> **Verdict:** ✅ **SUPPORTED** (confidence: 0.95)

---

## 🚀 Quick Start (Complete Setup Guide)

Follow these steps to get the project running on your machine.

### Prerequisites

Make sure you have the following installed:

- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **npm** (comes with Node.js)
- **Git** - [Download](https://git-scm.com/)

### Step 1: Clone the Repository

```bash
git clone https://github.com/bhagyeshmagar/StrawHats_KDSH_2026.git
cd StrawHats_KDSH_2026
```

### Step 2: Set Up Python Environment

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Anthropic API key
# You can get one from: https://console.anthropic.com/
```

Edit the `.env` file:
```env
ANTHROPIC_API_KEY=your-actual-api-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=true
```

### Step 4: Set Up the Frontend

```bash
# Navigate to the frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Go back to the project root
cd ..
```

### Step 5: Run the Application

You need to run **two terminals** simultaneously:

**Terminal 1 - Start the Flask Backend API:**
```bash
# Make sure you're in the project root directory
# Activate the virtual environment if not already active
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Start the Flask API server
python flask_api/app.py
```

The backend will start at: `http://127.0.0.1:5000`

**Terminal 2 - Start the React Frontend:**
```bash
# Navigate to frontend directory
cd frontend

# Start the development server
npm run dev
```

The frontend will start at: `http://localhost:5173`

### Step 6: Access the Application

Open your browser and go to: **http://localhost:5173**

---

## 🔄 Running the Verification Pipeline

To process claims through the AI pipeline:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run full pipeline with Claude API
python run_all.py

# Run with local LLM (Ollama) - no API needed
python run_all.py --local

# Test mode (process limited claims)
python run_all.py --test-mode

# Skip LLM calls (use cached verdicts)
python run_all.py --skip-reasoning
```

---

## 📦 KDSH 2026 Submission

This project is built for **KDSH 2026 Track A** (RAG + LLM with Pathway).

### Create Submission Package

```bash
# Generate results and create submission ZIP
python create_submission.py
```

This creates `StrawHats_KDSH_2026.zip` with:
- All source code
- `results.csv` in KDSH format: `Story ID, Prediction, Rationale`
- Configuration files

### Results Format

The output follows KDSH specifications:
```csv
Story ID,Prediction,Rationale
95,1,Evidence confirms the claim.
136,0,Backstory contradicts novel events.
```

Where:
- `1` = Backstory is consistent with novel
- `0` = Backstory is inconsistent with novel

---

## 🏠 Local LLM Setup (Optional - Ollama)

Run entirely on your machine with no API costs:

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a model (choose based on your GPU VRAM)
ollama pull phi3:mini          # 4GB VRAM - fast
ollama pull mistral:7b-instruct-q4_0  # 5GB VRAM - better quality
ollama pull llama3.2:3b        # 3GB VRAM - lightweight

# 3. Run the pipeline locally
python run_all.py --local
```

---

## 📁 Project Structure

```
StrawHats_KDSH_2026/
├── agents/                  # Pipeline agents
│   ├── ingestion_agent.py   # Chunk novels into segments
│   ├── embedding_agent.py   # Create FAISS vector index
│   ├── claim_parser.py      # Parse claims from CSV
│   ├── retriever_agent.py   # Find relevant passages
│   ├── reasoning_agent.py   # Claude API verification
│   └── dossier_writer.py    # Generate Markdown reports
├── data/
│   ├── novels/              # Source novel .txt files
│   ├── train.csv            # Training claims
│   └── test.csv             # Test claims
├── flask_api/
│   ├── app.py               # Main Flask API server
│   ├── claims.py            # Claims management
│   └── upload.py            # File upload handling
├── frontend/                # React + Vite + Tailwind dashboard
│   ├── src/
│   │   └── components/      # React components
│   └── package.json         # Node.js dependencies
├── tests/                   # Pytest test suite
├── run_all.py               # Pipeline orchestrator
├── requirements.txt         # Python dependencies
└── .env.example             # Environment template
```

### Generated Directories (created after running pipeline)

| Directory | Contents |
|-----------|----------|
| `chunks/` | Chunked novel text (JSONL) |
| `index/` | FAISS index + metadata |
| `claims/` | Parsed claims (JSONL) |
| `evidence/` | Retrieved passages per claim |
| `verdicts/` | LLM verdicts (JSON) |
| `dossiers/` | Human-readable reports (Markdown) |
| `output/` | Final results.csv |

---

## 🧪 Testing

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=agents --cov=flask_api
```

---

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/results` | GET | All verification results |
| `/api/dossier/<id>` | GET | Markdown dossier for claim |
| `/api/verdict/<id>` | GET | Raw verdict JSON |
| `/api/evidence/<id>` | GET | Retrieved evidence |
| `/api/stats` | GET | Summary statistics |
| `/api/books` | GET | List of books |
| `/api/claims` | POST | Add new claims |
| `/api/upload` | POST | Upload novel files |

---

## ❓ Troubleshooting

### "Module not found" error
Make sure your virtual environment is activated:
```bash
source .venv/bin/activate  # Linux/macOS
```

### Frontend not connecting to backend
- Ensure Flask API is running on port 5000
- Check that both terminals are running
- Try restarting both servers

### API Key errors
- Verify your `.env` file has a valid `ANTHROPIC_API_KEY`
- Make sure there are no extra spaces around the key

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                            │
├──────────────────────┬──────────────────────────────────────────┤
│   novels/*.txt       │       train.csv / test.csv              │
└──────────┬───────────┴──────────────────┬───────────────────────┘
           │                              │
           ▼                              ▼
┌──────────────────────┐       ┌──────────────────────┐
│   Ingestion Agent    │       │    Claim Parser      │
│   (chunk novels)     │       │    (parse CSV)       │
└──────────┬───────────┘       └──────────┬───────────┘
           │                              │
           ▼                              │
┌──────────────────────┐                  │
│   Embedding Agent    │                  │
│   (FAISS index)      │                  │
└──────────┬───────────┘                  │
           │                              │
           ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Retriever Agent                            │
│              (find relevant passages per claim)                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Reasoning Agent                            │
│                    (Claude API verdicts)                        │
└──────────┬───────────────────────────────────────┬──────────────┘
           │                                       │
           ▼                                       ▼
┌──────────────────────┐             ┌────────────────────────────┐
│   Dossier Writer     │             │   Results Aggregator       │
│   (Markdown reports) │             │   (CSV output)             │
└──────────────────────┘             └────────────────────────────┘
```

---

## 🤝 Team StrawHats

Built for **KDSH 2026** competition.

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">

**Built with ❤️ for literary AI research**

</div>
