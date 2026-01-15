"""
NovelVerified.AI - Pipeline Orchestrator

Runs the complete pipeline from novel ingestion to results generation.
Usage:
    python run_all.py               # Run full pipeline (uses Claude API)
    python run_all.py --local       # Run with local LLM (Ollama)
    python run_all.py --clean       # Clear old results before running
    python run_all.py --test-mode   # Run with limited claims for testing
    python run_all.py --skip-reasoning  # Skip LLM calls
"""

import argparse
import subprocess
import sys
import shutil
from pathlib import Path
import time
import os

# Suppress TensorFlow/oneDNN warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TF INFO/WARNING logs

# Pipeline stages in order
STAGES = [
    ("Ingestion", "agents/ingestion_agent.py"),
    ("Embedding", "agents/embedding_agent.py"),
    ("Claims", "agents/claim_parser.py"),
    ("Retrieval", "agents/retriever_agent.py"),
    ("Reasoning", "agents/reasoning_agent.py"),  # Will be swapped for local
    ("Dossiers", "agents/dossier_writer.py"),
    ("Results", "agents/results_aggregator.py"),
]

# Directories to clean before fresh run
INTERMEDIATE_DIRS = [
    "chunks",
    "index", 
    "claims",
    "evidence",
    "verdicts",
    "dossiers",
    "output",
]


def clean_directories():
    """Remove all intermediate directories to start fresh."""
    print("\n🧹 Cleaning intermediate directories...")
    for dir_name in INTERMEDIATE_DIRS:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_name}/")
        else:
            print(f"  Skipped (not found): {dir_name}/")
    print("  Clean complete!\n")


def run_stage(name: str, script: str, test_mode: bool = False) -> bool:
    """Run a single pipeline stage."""
    print(f"\n{'='*60}")
    print(f"STAGE: {name}")
    print(f"{'='*60}")
    
    script_path = Path(script)
    if not script_path.exists():
        print(f"ERROR: Script not found: {script}")
        return False
    
    try:
        args = [sys.executable, str(script_path)]
        if test_mode:
            args.append("--test-mode")
        
        result = subprocess.run(
            args,
            cwd=str(Path.cwd()),
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Stage {name} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to run {name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="NovelVerified.AI Pipeline Orchestrator")
    parser.add_argument("--test-mode", action="store_true", help="Run with limited data for testing")
    parser.add_argument("--skip-reasoning", action="store_true", help="Skip LLM reasoning stage")
    parser.add_argument("--local", action="store_true", help="Use local Ollama LLM instead of Claude API")
    parser.add_argument("--clean", action="store_true", help="Clear all intermediate results before running (fresh start)")
    parser.add_argument("--start-from", type=str, help="Start from a specific stage", 
                        choices=["ingestion", "embedding", "claims", "retrieval", "reasoning", "dossiers", "results"])
    args = parser.parse_args()
    
    print("=" * 60)
    print("NovelVerified.AI - Full Pipeline Execution")
    print("=" * 60)
    
    # Clean intermediate directories if requested
    if args.clean:
        clean_directories()
    
    if args.test_mode:
        print("Running in TEST MODE (limited data)")
    
    if args.local:
        print("Using LOCAL LLM (Ollama)")
        # Swap reasoning agent to local version
        global STAGES
        STAGES = [(n, s.replace("reasoning_agent.py", "reasoning_agent_local.py") if "reasoning" in s else s) 
                  for n, s in STAGES]
    start_time = time.time()
    
    # Determine starting stage
    start_idx = 0
    if args.start_from:
        stage_names = [s[0].lower() for s in STAGES]
        try:
            start_idx = stage_names.index(args.start_from)
            print(f"Starting from stage: {STAGES[start_idx][0]}")
        except ValueError:
            pass
    
    # Run stages
    stages_to_run = STAGES[start_idx:]
    
    for name, script in stages_to_run:
        # Skip reasoning if requested
        if args.skip_reasoning and name == "Reasoning":
            print(f"\nSkipping {name} stage (--skip-reasoning)")
            continue
        
        success = run_stage(name, script, args.test_mode)
        
        if not success:
            print(f"\n{'='*60}")
            print(f"PIPELINE FAILED at stage: {name}")
            print(f"{'='*60}")
            sys.exit(1)
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE!")
    print(f"{'='*60}")
    print(f"Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print("\nOutputs:")
    print("  - chunks/chunks.jsonl: Chunked novel text")
    print("  - index/faiss.index: Vector search index")
    print("  - claims/claims.jsonl: Parsed claims")
    print("  - evidence/*.json: Retrieved evidence per claim")
    print("  - verdicts/*.json: Reasoning verdicts")
    print("  - dossiers/*.md: Human-readable dossiers")
    print("  - output/results.csv: Final predictions")


if __name__ == "__main__":
    main()
