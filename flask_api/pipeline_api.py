"""
Pipeline API Blueprint - REST endpoints for triggering the pipeline.

Endpoints:
    POST /api/pipeline/run - Start the full pipeline
    GET /api/pipeline/status - Get current pipeline status
    POST /api/pipeline/cancel - Cancel running pipeline
    POST /api/pipeline/reset - Reset pipeline status
    POST /api/pipeline/stage/<name> - Run a single stage
"""

from flask import Blueprint, jsonify, request
from pipeline import (
    run_pipeline_async, 
    get_pipeline_status, 
    reset_pipeline_status,
    run_single_stage,
    cancel_pipeline
)

pipeline_bp = Blueprint('pipeline', __name__)


@pipeline_bp.route("/api/pipeline/run", methods=["POST"])
def start_pipeline():
    """
    Start the full verification pipeline.
    
    Request body (optional):
        {
            "clean": true  // Clear old results first (default: true)
        }
    
    Note: Always uses Ollama (local LLM) for processing.
    
    Response:
        {
            "success": true,
            "message": "Pipeline started"
        }
    """
    data = request.get_json() or {}
    clean = data.get("clean", True)
    
    success, message = run_pipeline_async(clean=clean)
    
    return jsonify({
        "success": success,
        "message": message
    }), 200 if success else 409


@pipeline_bp.route("/api/pipeline/status", methods=["GET"])
def pipeline_status():
    """
    Get current pipeline status.
    
    Response:
        {
            "running": true/false,
            "stage": "Reasoning",
            "progress": 60,
            "start_time": "2026-01-11T14:30:00",
            "end_time": null,
            "error": null,
            "log": ["line1", "line2", ...]
        }
    """
    status = get_pipeline_status()
    
    # Limit log to last 50 lines for performance
    if len(status.get("log", [])) > 50:
        status["log"] = status["log"][-50:]
    
    return jsonify(status)


@pipeline_bp.route("/api/pipeline/reset", methods=["POST"])
def reset_pipeline():
    """Reset pipeline status (for recovery from errors)."""
    status = get_pipeline_status()
    
    if status.get("running"):
        return jsonify({
            "success": False,
            "message": "Cannot reset while pipeline is running"
        }), 409
    
    reset_pipeline_status()
    
    return jsonify({
        "success": True,
        "message": "Pipeline status reset"
    })


@pipeline_bp.route("/api/pipeline/cancel", methods=["POST"])
def cancel_running_pipeline():
    """Cancel a running pipeline."""
    success, message = cancel_pipeline()
    
    return jsonify({
        "success": success,
        "message": message
    }), 200 if success else 409


@pipeline_bp.route("/api/pipeline/stage/<stage_name>", methods=["POST"])
def run_stage(stage_name: str):
    """
    Run a single pipeline stage.
    
    Valid stages: ingestion, embedding, claims, retrieval, reasoning, dossiers, results
    """
    success, message = run_single_stage(stage_name)
    
    return jsonify({
        "success": success,
        "message": message
    }), 200 if success else 400
