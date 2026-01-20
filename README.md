<div align="center">

# 🔍 NovelVerified.AI

**AI-Powered Novel Claim Verification System**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![Tests](https://img.shields.io/badge/tests-68%20passed-brightgreen.svg)]()

*Verify character backstory claims against actual novel text using RAG + LLM*

</div>

---

## 📊 Latest Results

| Metric | Value |
|--------|-------|
| **Contradicted Claims** | 89 |
| **Supported Claims** | 51 |
| **Average Confidence** | 92.39% |
| **Pipeline Runtime** | ~41 minutes |

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Download |
|-------------|---------|----------|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| Ollama | Latest | [ollama.ai](https://ollama.ai) |

### Installation

**Option 1: Automated** (Recommended)
```bash
chmod +x setup.sh && ./setup.sh
```

**Option 2: Manual**
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Pull LLM model
ollama pull mistral:7b-instruct-q4_0
```

### Running the System

**1. Run the Verification Pipeline**
```bash
source .venv/bin/activate
python run_all.py --local --clean
```

**2. Start the Dashboard**
```bash
# Terminal 1: Backend API
python flask_api/app.py

# Terminal 2: Frontend
cd frontend && npm run dev

# Open: http://localhost:5173
```

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🛡️ **Anti-Bias Reasoning** | Dual-perspective analysis (Support vs Contradiction) prevents LLM hallucinations |
| ⏱️ **Temporal Awareness** | Retrieves evidence from Early, Mid, and Late narrative stages |
| 🖥️ **Modern Dashboard** | Glassmorphism UI with real-time analytics and pipeline control |
| ⚡ **High Performance** | Pathway document processing + FAISS sub-second retrieval |

---

## 📖 How It Works

NovelVerified.AI verifies whether **character backstory claims** are **supported** or **contradicted** by actual novel text.

### Example

> **Claim:** "Edmond Dantes was imprisoned for fourteen years"  
> **Novel:** *The Count of Monte Cristo*  
> **Verdict:** ✅ **SUPPORTED** (confidence: 95%)

### Pipeline Flow

```
📚 Novel Text → Chunking → Embedding → Vector Index
                                            ↓
📋 Claims CSV → Parsing → Retrieval ← ← ← ← ┘
                              ↓
                    4-Stage LLM Reasoning
                              ↓
               Dossiers + Final Results CSV
```

**7 Pipeline Stages:**

1. **Ingestion** → Chunk novels with temporal slicing (EARLY/MID/LATE)
2. **Embedding** → Create FAISS vector index
3. **Claims** → Parse train.csv and test.csv
4. **Retrieval** → Find relevant passages per claim
5. **Reasoning** → 4-stage anti-bias LLM verification
6. **Dossiers** → Generate Markdown reports
7. **Results** → Output predictions CSV

---

## 📁 Project Structure

```
NovelVerified.AI/
├── Data/               # Novel texts + claims CSVs
├── agents/             # 11 pipeline agents
├── flask_api/          # Backend REST API
├── frontend/           # React dashboard
├── tests/              # 68 unit tests
├── run_all.py          # Pipeline orchestrator
└── setup.sh            # Installation script
```

### Generated After Pipeline Run

| Directory | Contents |
|-----------|----------|
| `chunks/` | Chunked novel text |
| `index/` | FAISS vector index |
| `claims/` | Parsed claims |
| `evidence/` | Retrieved passages |
| `verdicts/` | LLM verdicts |
| `dossiers/` | Markdown reports |
| `output/` | Final `results.csv` |

---

## 📊 Output Format

```csv
Story ID,Prediction,Rationale
95,1,Evidence confirms the claim...
136,0,The backstory contradicts...
```

| Prediction | Meaning |
|------------|---------|
| `1` | Claim is **consistent** with novel |
| `0` | Claim is **contradicted** by novel |

---

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| "Module not found" | `source .venv/bin/activate` |
| "Ollama not found" | Install from [ollama.ai](https://ollama.ai) |
| Pipeline fails at Reasoning | Run `ollama serve` first |
| Frontend won't start | `cd frontend && npm install` |

---

## 📄 Documentation

| Document | Description |
|----------|-------------|
| `REPORT.md` | Technical architecture report |
| `TECHNICAL_ARCHITECTURE.md` | Pathway integration details |
| `PROJECT_DOCUMENTATION.txt` | Full technical documentation |

---

<div align="center">

**NovelVerified.AI** • Built with ❤️ for literary AI research

</div>
