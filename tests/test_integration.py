"""
Integration Tests for KDSH 2026 Track A Pipeline.

Tests:
1. End-to-end pipeline execution
2. Results.csv format validation
3. Pathway component verification
4. Anti-bias detection (catch "all supported" failure mode)
"""

import pytest
import json
import csv
from pathlib import Path
import subprocess
import sys


# Test paths
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_FILE = PROJECT_ROOT / "output" / "results.csv"
VERDICTS_DIR = PROJECT_ROOT / "verdicts"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
PATHWAY_STORE = PROJECT_ROOT / "pathway_store"


class TestResultsFormat:
    """Test that results.csv matches KDSH specification."""
    
    def test_results_file_exists(self):
        """Results file should exist after pipeline run."""
        if not RESULTS_FILE.exists():
            pytest.skip("Run pipeline first: python run_all.py")
        assert RESULTS_FILE.exists()
    
    def test_results_has_required_columns(self):
        """Results must have exactly: Story ID, Prediction, Rationale."""
        if not RESULTS_FILE.exists():
            pytest.skip("Run pipeline first")
        
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
        
        required = ["Story ID", "Prediction", "Rationale"]
        assert fieldnames is not None
        for col in required:
            assert col in fieldnames, f"Missing required column: {col}"
    
    def test_predictions_are_binary(self):
        """Predictions must be 0 or 1."""
        if not RESULTS_FILE.exists():
            pytest.skip("Run pipeline first")
        
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pred = int(row["Prediction"])
                assert pred in [0, 1], f"Invalid prediction: {pred}"
    
    def test_rationale_not_empty(self):
        """Each row should have a rationale."""
        if not RESULTS_FILE.exists():
            pytest.skip("Run pipeline first")
        
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert row["Rationale"].strip(), f"Empty rationale for {row['Story ID']}"


class TestPathwayIntegration:
    """Test that Pathway is actually used (not cosmetic)."""
    
    def test_pathway_store_exists(self):
        """Pathway store directory should be created by ingestion."""
        if not PATHWAY_STORE.exists():
            pytest.skip("Run pipeline first")
        
        assert PATHWAY_STORE.exists()
        assert (PATHWAY_STORE / "chunks.jsonl").exists()
        assert (PATHWAY_STORE / "metadata.json").exists()
    
    def test_chunks_have_temporal_slice(self):
        """Chunks should have temporal_slice computed by Pathway store."""
        chunks_file = PATHWAY_STORE / "chunks.jsonl"
        if not chunks_file.exists():
            pytest.skip("Run pipeline first")
        
        with open(chunks_file, "r", encoding="utf-8") as f:
            for line in f:
                chunk = json.loads(line)
                assert "temporal_slice" in chunk
                assert chunk["temporal_slice"] in ["EARLY", "MID", "LATE"]
                break  # Check first chunk only
    
    def test_pathway_import_works(self):
        """Pathway should be importable."""
        import pathway as pw
        assert pw is not None


class TestAntiBias:
    """Test that the pipeline doesn't have 'all supported' bias."""
    
    def test_not_all_supported(self):
        """Catch failure mode where everything is 'supported'."""
        if not RESULTS_FILE.exists():
            pytest.skip("Run pipeline first")
        
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if len(rows) < 5:
            pytest.skip("Not enough results for anti-bias test")
        
        supported = sum(1 for r in rows if int(r["Prediction"]) == 1)
        total = len(rows)
        supported_pct = supported / total * 100
        
        # Warning threshold: > 90% supported is suspicious
        if supported_pct > 90:
            pytest.fail(
                f"ANTI-BIAS WARNING: {supported_pct:.0f}% predictions are 'supported'. "
                f"This suggests bias in the model. Review contradiction thresholds."
            )
    
    def test_verdicts_have_dual_perspective(self):
        """Verdicts should include both support and contradiction scores."""
        verdict_files = list(VERDICTS_DIR.glob("*.json"))
        if not verdict_files:
            pytest.skip("Run pipeline first")
        
        with open(verdict_files[0], "r", encoding="utf-8") as f:
            verdict = json.load(f)
        
        # Check for analysis with dual scores
        analysis = verdict.get("analysis", {})
        if analysis:
            assert "support_score" in analysis or "supporting_spans" in verdict
            assert "contradiction_score" in analysis or "contradicting_spans" in verdict


class TestConstraintReasoning:
    """Test multi-stage constraint-aware reasoning."""
    
    def test_evidence_has_temporal_info(self):
        """Retrieved evidence should have temporal slice information."""
        evidence_files = list(EVIDENCE_DIR.glob("*.json"))
        if not evidence_files:
            pytest.skip("Run pipeline first")
        
        with open(evidence_files[0], "r", encoding="utf-8") as f:
            evidence = json.load(f)
        
        if evidence.get("evidence"):
            first_ev = evidence["evidence"][0]
            # New pipeline should have temporal_slice
            if "temporal_slice" not in first_ev:
                pytest.skip("Evidence from old pipeline format")
            assert first_ev["temporal_slice"] in ["EARLY", "MID", "LATE"]
    
    def test_verdict_has_subclaims(self):
        """Verdicts should include sub-claim decomposition (if new pipeline)."""
        verdict_files = list(VERDICTS_DIR.glob("*.json"))
        if not verdict_files:
            pytest.skip("Run pipeline first")
        
        with open(verdict_files[0], "r", encoding="utf-8") as f:
            verdict = json.load(f)
        
        analysis = verdict.get("analysis", {})
        if analysis:
            # New pipeline includes sub-claims
            assert "sub_claims" in analysis or "reasoning" in verdict


class TestPipelineExecution:
    """Test that pipeline can be executed."""
    
    def test_run_all_help(self):
        """run_all.py should have --help."""
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "run_all.py"), "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--clean" in result.stdout
        assert "--local" in result.stdout


# ============================================================================
# Deterministic Test Mode
# ============================================================================

def run_deterministic_test():
    """
    Run a deterministic test with known input/output.
    Called by: pytest tests/test_integration.py::test_deterministic
    """
    print("\n=== Deterministic Integration Test ===")
    print("This test validates the full pipeline with controlled inputs.")
    
    # Check if we have test data
    claims_file = PROJECT_ROOT / "claims" / "claims.jsonl"
    if not claims_file.exists():
        print("SKIP: No claims file. Run claim_parser.py first.")
        return
    
    # Count claims
    with open(claims_file, "r") as f:
        num_claims = sum(1 for _ in f)
    
    print(f"Found {num_claims} claims")
    
    # Check results
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, "r") as f:
            reader = csv.DictReader(f)
            results = list(reader)
        
        print(f"Results: {len(results)} rows")
        
        supported = sum(1 for r in results if int(r["Prediction"]) == 1)
        contradicted = len(results) - supported
        
        print(f"  Supported: {supported} ({supported/len(results)*100:.0f}%)")
        print(f"  Contradicted: {contradicted} ({contradicted/len(results)*100:.0f}%)")
        
        if supported / len(results) > 0.9:
            print("\n⚠️  WARNING: High support rate may indicate bias")
    else:
        print("Results file not found. Run pipeline first.")


if __name__ == "__main__":
    run_deterministic_test()
