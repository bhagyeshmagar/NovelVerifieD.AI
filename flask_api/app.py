"""
NovelVerified.AI - Flask Backend API

Serves results and dossiers to the React frontend.

Endpoints:
    GET /api/results - Get all results as JSON
    GET /api/dossier/<claim_id> - Get dossier markdown
    GET /download/results.csv - Download results as CSV file
"""

import os
import json
import csv
from pathlib import Path
from flask import Flask, jsonify, send_file, request, abort
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
HOST = os.getenv("FLASK_HOST", "127.0.0.1")
PORT = int(os.getenv("FLASK_PORT", 5000))
DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

# Paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_FILE = PROJECT_ROOT / "output" / "results.csv"  # KDSH submission format
RESULTS_EXTENDED = PROJECT_ROOT / "output" / "results_extended.csv"  # Dashboard format
DOSSIERS_DIR = PROJECT_ROOT / "dossiers"
VERDICTS_DIR = PROJECT_ROOT / "verdicts"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Register upload blueprint
from upload import upload_bp
app.register_blueprint(upload_bp)

# Register history blueprint
from history import history_bp
app.register_blueprint(history_bp)

# Register claims blueprint
from claims import claims_bp
app.register_blueprint(claims_bp)

# Register pipeline blueprint
from pipeline_api import pipeline_bp
app.register_blueprint(pipeline_bp)


@app.route("/api/results", methods=["GET"])
def get_results():
    """Return all results as JSON (uses extended format for dashboard)."""
    # Use extended results for dashboard
    results_file = RESULTS_EXTENDED if RESULTS_EXTENDED.exists() else RESULTS_FILE
    
    if not results_file.exists():
        return jsonify({"error": "Results file not found. Run the pipeline first."}), 404
    
    results = []
    with open(results_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize field names for frontend compatibility
            normalized = {
                "id": row.get("Story ID", row.get("id", "")),
                "prediction": int(row.get("Prediction", row.get("prediction", 0))),
                "rationale": row.get("Rationale", row.get("rationale", "")),
                "book_name": row.get("book_name", ""),
                "character": row.get("character", ""),
                "verdict": row.get("verdict", ""),
                "confidence": float(row.get("confidence", 0)),
            }
            results.append(normalized)
    
    return jsonify({
        "total": len(results),
        "results": results
    })


@app.route("/api/dossier/<claim_id>", methods=["GET"])
def get_dossier(claim_id: str):
    """Return dossier markdown for a specific claim."""
    dossier_file = DOSSIERS_DIR / f"{claim_id}.md"
    
    if not dossier_file.exists():
        return jsonify({"error": f"Dossier not found for claim {claim_id}"}), 404
    
    with open(dossier_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    return jsonify({
        "claim_id": claim_id,
        "content": content
    })


@app.route("/api/verdict/<claim_id>", methods=["GET"])
def get_verdict(claim_id: str):
    """Return raw verdict JSON for a specific claim."""
    verdict_file = VERDICTS_DIR / f"{claim_id}.json"
    
    if not verdict_file.exists():
        return jsonify({"error": f"Verdict not found for claim {claim_id}"}), 404
    
    with open(verdict_file, "r", encoding="utf-8") as f:
        verdict = json.load(f)
    
    return jsonify(verdict)


@app.route("/api/evidence/<claim_id>", methods=["GET"])
def get_evidence(claim_id: str):
    """Return evidence data for a specific claim."""
    evidence_file = EVIDENCE_DIR / f"{claim_id}.json"
    
    if not evidence_file.exists():
        return jsonify({"error": f"Evidence not found for claim {claim_id}"}), 404
    
    with open(evidence_file, "r", encoding="utf-8") as f:
        evidence = json.load(f)
    
    return jsonify(evidence)


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Return summary statistics including model accuracy."""
    # Use extended results for stats
    results_file = RESULTS_EXTENDED if RESULTS_EXTENDED.exists() else RESULTS_FILE
    
    if not results_file.exists():
        return jsonify({"error": "Results file not found"}), 404
    
    results = []
    with open(results_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    
    # Load ground truth labels from claims
    claims_file = PROJECT_ROOT / "claims" / "claims.jsonl"
    ground_truth = {}
    if claims_file.exists():
        with open(claims_file, "r", encoding="utf-8") as f:
            for line in f:
                claim = json.loads(line)
                claim_id = str(claim.get("id"))
                label = claim.get("label", "").lower()
                # Map labels: consistent -> 1, contradictory -> 0
                if label in ["consistent", "supported"]:
                    ground_truth[claim_id] = 1
                elif label in ["contradictory", "contradicted"]:
                    ground_truth[claim_id] = 0
    
    # Calculate stats (handle both old and new column names)
    total = len(results)
    supported = sum(1 for r in results if int(r.get("Prediction", r.get("prediction", 0))) == 1)
    contradicted = total - supported
    
    # Calculate accuracy (only for claims with ground truth)
    correct = 0
    evaluated = 0
    for r in results:
        claim_id = str(r.get("Story ID", r.get("id", "")))
        prediction = int(r.get("Prediction", r.get("prediction", 0)))
        if claim_id in ground_truth:
            evaluated += 1
            if prediction == ground_truth[claim_id]:
                correct += 1
    
    accuracy = round((correct / evaluated * 100), 2) if evaluated > 0 else None
    
    # Breakdown by book
    books = {}
    for r in results:
        book = r.get("book_name", "Unknown")
        if book not in books:
            books[book] = {"total": 0, "supported": 0, "contradicted": 0}
        books[book]["total"] += 1
        if int(r.get("Prediction", r.get("prediction", 0))) == 1:
            books[book]["supported"] += 1
        else:
            books[book]["contradicted"] += 1
    
    # Breakdown by verdict
    verdicts = {}
    for r in results:
        v = r.get("verdict", "unknown")
        verdicts[v] = verdicts.get(v, 0) + 1
    
    # Average confidence
    avg_confidence = sum(float(r.get("confidence", 0)) for r in results) / total if total > 0 else 0
    
    return jsonify({
        "total": total,
        "supported": supported,
        "contradicted": contradicted,
        "accuracy": accuracy,
        "evaluated_claims": evaluated,
        "correct_predictions": correct,
        "by_book": books,
        "by_verdict": verdicts,
        "avg_confidence": round(avg_confidence, 3)
    })


@app.route("/download/results.csv", methods=["GET"])
def download_results():
    """Download results CSV file."""
    if not RESULTS_FILE.exists():
        return jsonify({"error": "Results file not found"}), 404
    
    return send_file(
        str(RESULTS_FILE),
        mimetype="text/csv",
        as_attachment=True,
        download_name="results.csv"
    )


@app.route("/api/books", methods=["GET"])
def get_books():
    """Return list of unique books."""
    if not RESULTS_FILE.exists():
        return jsonify({"books": []})
    
    books = set()
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            books.add(row.get("book_name", ""))
    
    return jsonify({"books": sorted(list(books))})


@app.route("/api/characters", methods=["GET"])
def get_characters():
    """Return list of unique characters."""
    if not RESULTS_FILE.exists():
        return jsonify({"characters": []})
    
    characters = set()
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            characters.add(row.get("character", ""))
    
    return jsonify({"characters": sorted(list(characters))})


@app.route("/", methods=["GET"])
def index():
    """API info endpoint."""
    return jsonify({
        "name": "NovelVerified.AI API",
        "version": "1.1.0",
        "endpoints": {
            "/api/results": "GET all results",
            "/api/dossier/<id>": "GET dossier markdown",
            "/api/verdict/<id>": "GET verdict JSON",
            "/api/evidence/<id>": "GET evidence JSON",
            "/api/stats": "GET summary statistics",
            "/api/books": "GET list of books",
            "/api/characters": "GET list of characters",
            "/api/upload": "POST upload novel (PDF/DOCX/TXT)",
            "/api/novels": "GET list of uploaded novels",
            "/api/pipeline/run": "POST trigger pipeline",
            "/download/results.csv": "Download CSV file"
        }
    })


if __name__ == "__main__":
    print(f"Starting NovelVerified.AI API on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
