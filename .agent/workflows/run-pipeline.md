---
description: Run the verification pipeline to process claims
---

# Run Pipeline

## Prerequisites
- Python virtual environment activated
- Ollama installed and running with a model (e.g., mistral:7b-instruct-q4_0)
- Novel files in `Data/` directory
- Claims files (train.csv, test.csv) in `Data/` directory

## Steps

1. Activate the virtual environment:
```bash
source .venv/bin/activate
```

2. Start Ollama service (if not running):
```bash
ollama serve
```

// turbo
3. Run the full pipeline with local LLM:
```bash
python3 run_all.py --local --clean
```

## Pipeline Options

- `--local`: Use local Ollama LLM instead of Claude API
- `--clean`: Clear all intermediate results before running
- `--test-mode`: Run with limited claims for testing
- `--skip-reasoning`: Skip the LLM reasoning stage
- `--start-from <stage>`: Start from a specific stage (ingestion, embedding, claims, retrieval, reasoning, dossiers, results)

## Pipeline Stages

1. **Ingestion**: Chunks novels into overlapping segments
2. **Embedding**: Creates FAISS vector index
3. **Claims**: Parses train.csv and test.csv
4. **Retrieval**: Finds relevant passages per claim
5. **Reasoning**: 4-stage anti-bias LLM verification
6. **Dossiers**: Generates Markdown reports
7. **Results**: Creates NovelVerified.AI-format CSV

## Output

- `output/results.csv`: Final predictions
- `dossiers/*.md`: Human-readable dossiers
- `verdicts/*.json`: Raw verdict data
