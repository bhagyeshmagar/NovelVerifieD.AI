"""Tests for the Flask API endpoints."""

import sys
import json
import csv
from pathlib import Path
from unittest.mock import patch
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def app(tmp_path):
    """Create test Flask app with temp data directories."""
    # Add flask_api to path so blueprint imports work
    flask_api_path = str(Path(__file__).parent.parent / "flask_api")
    if flask_api_path not in sys.path:
        sys.path.insert(0, flask_api_path)
    
    # Create temp files
    results_file = tmp_path / "output" / "results.csv"
    results_file.parent.mkdir(parents=True)
    
    # Write sample results
    with open(results_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "book_name", "character", "prediction", "verdict", "confidence", "rationale"
        ])
        writer.writeheader()
        writer.writerow({
            "id": "test_001",
            "book_name": "Test Book",
            "character": "Test Character",
            "prediction": 1,
            "verdict": "supported",
            "confidence": 0.95,
            "rationale": "Test rationale"
        })
    
    # Create dossier
    dossiers_dir = tmp_path / "dossiers"
    dossiers_dir.mkdir()
    (dossiers_dir / "test_001.md").write_text("# Test Dossier\n\nContent here.")
    
    # Create verdict
    verdicts_dir = tmp_path / "verdicts"
    verdicts_dir.mkdir()
    with open(verdicts_dir / "test_001.json", "w") as f:
        json.dump({
            "claim_id": "test_001",
            "verdict": "supported",
            "confidence": 0.95
        }, f)
    
    # Create evidence
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    with open(evidence_dir / "test_001.json", "w") as f:
        json.dump({
            "claim_id": "test_001",
            "evidence": [{"text": "test evidence"}]
        }, f)
    
    # Patch the paths in the Flask app
    with patch('flask_api.app.PROJECT_ROOT', tmp_path):
        with patch('flask_api.app.RESULTS_FILE', results_file):
            with patch('flask_api.app.DOSSIERS_DIR', dossiers_dir):
                with patch('flask_api.app.VERDICTS_DIR', verdicts_dir):
                    with patch('flask_api.app.EVIDENCE_DIR', evidence_dir):
                        from flask_api.app import app as flask_app
                        flask_app.config['TESTING'] = True
                        yield flask_app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestAPIIndex:
    """Tests for the index endpoint."""
    
    @pytest.mark.api
    def test_index_returns_api_info(self, client):
        """Index should return API information."""
        response = client.get("/")
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert "name" in data
        assert "NovelVerified" in data["name"]
        assert "endpoints" in data


class TestAPIResults:
    """Tests for the results endpoint."""
    
    @pytest.mark.api
    def test_get_results_success(self, client):
        """Should return results JSON."""
        response = client.get("/api/results")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "results" in data
        assert "total" in data
    
    @pytest.mark.api
    def test_results_have_required_fields(self, client):
        """Results should have all required fields."""
        response = client.get("/api/results")
        data = json.loads(response.data)
        
        if data["results"]:
            result = data["results"][0]
            assert "id" in result or "claim_id" in result
            assert "prediction" in result
            assert "verdict" in result


class TestAPIDossier:
    """Tests for the dossier endpoint."""
    
    @pytest.mark.api
    def test_get_dossier_success(self, client):
        """Should return dossier content."""
        response = client.get("/api/dossier/test_001")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "content" in data
        assert "Test Dossier" in data["content"]
    
    @pytest.mark.api
    def test_get_dossier_not_found(self, client):
        """Should return 404 for non-existent dossier."""
        response = client.get("/api/dossier/nonexistent")
        
        assert response.status_code == 404


class TestAPIStats:
    """Tests for the stats endpoint."""
    
    @pytest.mark.api
    def test_get_stats_success(self, client):
        """Should return statistics."""
        response = client.get("/api/stats")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "total" in data
        assert "supported" in data
        assert "contradicted" in data


class TestAPIVerdict:
    """Tests for the verdict endpoint."""
    
    @pytest.mark.api
    def test_get_verdict_success(self, client):
        """Should return verdict JSON."""
        response = client.get("/api/verdict/test_001")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "verdict" in data
    
    @pytest.mark.api
    def test_get_verdict_not_found(self, client):
        """Should return 404 for non-existent verdict."""
        response = client.get("/api/verdict/nonexistent")
        
        assert response.status_code == 404


class TestAPIEvidence:
    """Tests for the evidence endpoint."""
    
    @pytest.mark.api
    def test_get_evidence_success(self, client):
        """Should return evidence JSON."""
        response = client.get("/api/evidence/test_001")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "evidence" in data
    
    @pytest.mark.api
    def test_get_evidence_not_found(self, client):
        """Should return 404 for non-existent evidence."""
        response = client.get("/api/evidence/nonexistent")
        
        assert response.status_code == 404
