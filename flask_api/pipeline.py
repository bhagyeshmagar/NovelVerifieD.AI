"""
Pipeline API - Triggers the verification pipeline from the Flask API.

This allows the frontend to start the pipeline without manual terminal commands.
"""

import subprocess
import threading
import json
import time
import os
import signal
from pathlib import Path
from datetime import datetime

# Pipeline state tracking
_pipeline_status = {
    "running": False,
    "stage": None,
    "progress": 0,
    "start_time": None,
    "end_time": None,
    "error": None,
    "log": []
}

# Track the subprocess for cancellation
_pipeline_process = None

PROJECT_ROOT = Path(__file__).parent.parent
PYTHON_CMD = "python3"


def get_pipeline_status():
    """Get current pipeline status."""
    return _pipeline_status.copy()


def reset_pipeline_status():
    """Reset pipeline status."""
    global _pipeline_status
    _pipeline_status = {
        "running": False,
        "stage": None,
        "progress": 0,
        "start_time": None,
        "end_time": None,
        "error": None,
        "log": []
    }


def cancel_pipeline():
    """Cancel the running pipeline."""
    global _pipeline_process, _pipeline_status
    
    if not _pipeline_status["running"]:
        return False, "No pipeline is running"
    
    if _pipeline_process is not None:
        try:
            # Kill the process group to also kill child processes
            os.killpg(os.getpgid(_pipeline_process.pid), signal.SIGTERM)
            _pipeline_status["stage"] = "Cancelled"
            _pipeline_status["error"] = "Pipeline cancelled by user"
            _pipeline_status["running"] = False
            _pipeline_status["end_time"] = datetime.now().isoformat()
            _pipeline_status["log"].append("Pipeline cancelled by user")
            return True, "Pipeline cancelled"
        except Exception as e:
            return False, f"Failed to cancel: {str(e)}"
    
    return False, "No process to cancel"


def run_pipeline_async(clean=True):
    """
    Run the pipeline in a background thread.
    
    Args:
        clean: If True, clear old results before running
    
    Note: Always uses Ollama (local LLM) for processing.
    """
    global _pipeline_status
    
    if _pipeline_status["running"]:
        return False, "Pipeline is already running"
    
    def pipeline_worker():
        global _pipeline_status, _pipeline_process
        
        _pipeline_status["running"] = True
        _pipeline_status["stage"] = "Starting"
        _pipeline_status["progress"] = 0
        _pipeline_status["start_time"] = datetime.now().isoformat()
        _pipeline_status["error"] = None
        _pipeline_status["log"] = []
        
        # Build command - always use local LLM (Ollama)
        cmd = [PYTHON_CMD, "run_all.py", "--local"]
        if clean:
            cmd.append("--clean")
        
        _pipeline_status["log"].append(f"Running: {' '.join(cmd)}")
        
        try:
            # Run the pipeline with new session for proper cancellation
            _pipeline_process = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                start_new_session=True  # Allows killing process group
            )
            
            stages = ["Ingestion", "Embedding", "Claims", "Retrieval", "Reasoning", "Dossiers", "Results"]
            current_stage_idx = 0
            
            for line in _pipeline_process.stdout:
                line = line.strip()
                if line:
                    _pipeline_status["log"].append(line)
                    
                    # Update stage based on output
                    for i, stage in enumerate(stages):
                        if f"STAGE: {stage}" in line or f"{stage.upper()}" in line.upper():
                            current_stage_idx = i
                            _pipeline_status["stage"] = stage
                            _pipeline_status["progress"] = int((i + 1) / len(stages) * 100)
                            break
                    
                    # Check for errors
                    if "ERROR" in line.upper() or "FAILED" in line.upper():
                        _pipeline_status["error"] = line
            
            _pipeline_process.wait()
            
            if _pipeline_process.returncode == 0:
                _pipeline_status["stage"] = "Complete"
                _pipeline_status["progress"] = 100
            else:
                _pipeline_status["error"] = f"Pipeline failed with exit code {_pipeline_process.returncode}"
                _pipeline_status["stage"] = "Failed"
                
        except Exception as e:
            _pipeline_status["error"] = str(e)
            _pipeline_status["stage"] = "Failed"
        
        finally:
            _pipeline_status["running"] = False
            _pipeline_status["end_time"] = datetime.now().isoformat()
    
    # Start the pipeline in a background thread
    thread = threading.Thread(target=pipeline_worker, daemon=True)
    thread.start()
    
    return True, "Pipeline started"


def run_single_stage(stage_name: str):
    """Run a single pipeline stage."""
    global _pipeline_status
    
    if _pipeline_status["running"]:
        return False, "Pipeline is already running"
    
    stage_scripts = {
        "ingestion": "agents/ingestion_agent.py",
        "embedding": "agents/embedding_agent.py",
        "claims": "agents/claim_parser.py",
        "retrieval": "agents/retriever_agent.py",
        "reasoning": "agents/reasoning_agent_local.py",
        "dossiers": "agents/dossier_writer.py",
        "results": "agents/results_aggregator.py"
    }
    
    if stage_name.lower() not in stage_scripts:
        return False, f"Unknown stage: {stage_name}"
    
    def stage_worker():
        global _pipeline_status
        
        _pipeline_status["running"] = True
        _pipeline_status["stage"] = stage_name
        _pipeline_status["progress"] = 50
        _pipeline_status["start_time"] = datetime.now().isoformat()
        _pipeline_status["error"] = None
        _pipeline_status["log"] = []
        
        script = stage_scripts[stage_name.lower()]
        cmd = [PYTHON_CMD, script]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            _pipeline_status["log"] = result.stdout.split("\n")
            
            if result.returncode == 0:
                _pipeline_status["stage"] = "Complete"
                _pipeline_status["progress"] = 100
            else:
                _pipeline_status["error"] = result.stderr or "Stage failed"
                _pipeline_status["stage"] = "Failed"
                
        except subprocess.TimeoutExpired:
            _pipeline_status["error"] = "Stage timed out"
            _pipeline_status["stage"] = "Failed"
        except Exception as e:
            _pipeline_status["error"] = str(e)
            _pipeline_status["stage"] = "Failed"
        finally:
            _pipeline_status["running"] = False
            _pipeline_status["end_time"] = datetime.now().isoformat()
    
    thread = threading.Thread(target=stage_worker, daemon=True)
    thread.start()
    
    return True, f"Stage {stage_name} started"
