<div align="center">

# 🔍 NovelVerified.AI

**AI-Powered Novel Claim Verification System**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)

*Verify character backstory claims against actual novel text using RAG + LLM*

**NovelVerified.AI - Pathway-based Document Processing**

</div>

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Ollama** - [Download](https://ollama.ai)

### Option 1: Automated Setup

```bash
# Make setup.sh executable and run it
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install frontend dependencies
cd frontend && npm install && cd ..

# 4. Install Ollama and a model
# Visit https://ollama.ai to install, then:
ollama pull mistral:7b-instruct-q4_0
```

### Run the Pipeline

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the full verification pipeline
python run_all.py --local --clean
```

### Run the Dashboard

```bash
# Terminal 1: Start backend
python flask_api/app.py

# Terminal 2: Start frontend
cd frontend && npm run dev

# Open: http://localhost:5173
```

---

---

## ✨ Key Features

- **🛡️ Anti-Bias Reasoning**: Dual-perspective (Support vs Contradiction) analysis to prevent LLM hallucinations.
- **⏱️ Temporal Awareness**: Retrieves evidence from Early, Mid, and Late narrative stages.
- **🖥️ Modern Dashboard**:
  - **Real-time Analytics**: Visualize accuracy, confidence, and verdict distribution.
  - **Pipeline Control**: Start/Stop/Monitor the entire process from a beautiful Glassmorphism UI.
  - **Deep Dive**: Inspect every claim's dossier, evidence, and reasoning chain.
- **⚡ High Performance**: Powered by Pathway for efficient document processing and FAISS for sub-second retrieval.

---

## 📖 What It Does

NovelVerified.AI verifies whether **character backstory claims** are **supported** or **contradicted** by actual novel text.

### Example

> **Claim:** "Edmond Dantes was imprisoned for fourteen years"  
> **Novel:** *The Count of Monte Cristo*  
> **Verdict:** ✅ **SUPPORTED** (confidence: 0.95)

---

## 📁 Project Structure

```
NovelVerified_AI/
├── Data/                    # Source data (novels + claims CSVs)
│   ├── *.txt                # Novel texts
│   ├── train.csv            # Training claims with labels
│   └── test.csv             # Test claims to verify
├── agents/                  # Pipeline agents (11 Python files)
├── flask_api/               # Backend API (6 Python files)
├── frontend/                # React dashboard
├── tests/                   # Unit tests
├── run_all.py               # Pipeline orchestrator
├── setup.sh                 # Installation script
├── requirements.txt         # Python dependencies
└── PROJECT_DOCUMENTATION.txt # Full documentation
```

### Generated Directories (after running pipeline)

| Directory | Contents |
|-----------|----------|
| `chunks/` | Chunked novel text (JSONL) |
| `index/` | FAISS vector index |
| `claims/` | Parsed claims (JSONL) |
| `evidence/` | Retrieved passages per claim |
| `verdicts/` | LLM verdicts (JSON) |
| `output/` | Final results.csv |

---

## 🔧 Pipeline Stages

1. **Ingestion** - Chunk novels with temporal slicing (EARLY/MID/LATE)
2. **Embedding** - Create FAISS vector index
3. **Claims** - Parse train.csv and test.csv
4. **Retrieval** - Find relevant passages per claim
5. **Reasoning** - 4-stage anti-bias LLM verification
6. **Dossiers** - Generate Markdown reports
7. **Results** - Create NovelVerified.AI-format CSV

---

## 📊 Output Format

```csv
Story ID,Prediction,Rationale
95,1,Evidence confirms the claim about...
136,0,The backstory contradicts the novel's...
```

- `1` = Claim is consistent with novel
- `0` = Claim is contradicted by novel

---

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| "Module not found" | Activate venv: `source .venv/bin/activate` |
| "Ollama not found" | Install from https://ollama.ai |
| Pipeline fails at Reasoning | Ensure Ollama is running: `ollama serve` |
| Frontend won't start | Run: `cd frontend && npm install` |

---

## 📄 Documentation

- **PROJECT_DOCUMENTATION.txt** - Full technical documentation
- **REPORT.md** - Technical report for NovelVerified.AI submission
- **TECHNICAL_ARCHITECTURE.md** - Architecture and Pathway integration details

---

<div align="center">

**NovelVerified.AI**

Built with ❤️ for literary AI research

</div>
