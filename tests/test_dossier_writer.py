"""Tests for the dossier writer agent."""

import sys
import json
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.dossier_writer import (
    get_confidence_bar,
    format_temporal_evidence,
    format_spans,
    generate_dossier
)


class TestGetConfidenceBar:
    """Tests for the get_confidence_bar function."""
    
    @pytest.mark.unit
    def test_zero_confidence(self):
        """Zero confidence should show empty bar."""
        result = get_confidence_bar(0.0)
        assert "░░░░░░░░░░" in result
        assert "0%" in result
    
    @pytest.mark.unit
    def test_full_confidence(self):
        """Full confidence should show full bar."""
        result = get_confidence_bar(1.0)
        assert "██████████" in result
        assert "100%" in result
    
    @pytest.mark.unit
    def test_half_confidence(self):
        """Half confidence should show half-full bar."""
        result = get_confidence_bar(0.5)
        assert "█████" in result
        assert "░░░░░" in result
        assert "50%" in result
    
    @pytest.mark.unit
    def test_returns_string(self):
        """Should always return a string."""
        assert isinstance(get_confidence_bar(0.7), str)


class TestFormatSpans:
    """Tests for the format_spans function."""
    
    @pytest.mark.unit
    def test_empty_spans(self):
        """Empty spans should return 'no spans' message."""
        result = format_spans([], "supporting", "📗")
        assert "no supporting spans" in result.lower()
    
    @pytest.mark.unit
    def test_single_span(self):
        """Single span should be formatted with emoji."""
        result = format_spans(["test span"], "supporting", "📗")
        assert "📗" in result
        assert "test span" in result
    
    @pytest.mark.unit
    def test_multiple_spans(self):
        """Multiple spans should all be included."""
        spans = ["span one", "span two", "span three"]
        result = format_spans(spans, "supporting", "📗")
        for span in spans:
            assert span in result
    
    @pytest.mark.unit
    def test_max_five_spans(self):
        """Should limit to 5 spans."""
        spans = [f"span_{i}" for i in range(10)]
        result = format_spans(spans, "supporting", "📗")
        assert "span_4" in result
        assert "span_5" not in result


class TestFormatTemporalEvidence:
    """Tests for the format_temporal_evidence function."""
    
    @pytest.mark.unit
    def test_empty_evidence(self):
        """Empty evidence should return sections with 'no evidence' messages."""
        result = format_temporal_evidence([])
        assert "No evidence from this section" in result
    
    @pytest.mark.unit
    def test_evidence_organized_by_slice(self):
        """Evidence should be organized by temporal slice."""
        evidence = [
            {"temporal_slice": "EARLY", "book": "Test", "chunk_idx": 0, "score": 0.8, "text": "Early text"},
            {"temporal_slice": "MID", "book": "Test", "chunk_idx": 1, "score": 0.7, "text": "Mid text"},
            {"temporal_slice": "LATE", "book": "Test", "chunk_idx": 2, "score": 0.9, "text": "Late text"}
        ]
        result = format_temporal_evidence(evidence)
        
        assert "EARLY" in result
        assert "MID" in result
        assert "LATE" in result
        assert "Early text" in result
        assert "Mid text" in result
        assert "Late text" in result
    
    @pytest.mark.unit
    def test_includes_book_and_score(self):
        """Evidence should include book name and score."""
        evidence = [{
            "temporal_slice": "MID",
            "book": "Test Book",
            "chunk_idx": 5,
            "score": 0.85,
            "text": "This is the evidence text."
        }]
        result = format_temporal_evidence(evidence)
        
        assert "Test Book" in result
        assert "0.850" in result or "0.85" in result
        assert "This is the evidence text" in result
    
    @pytest.mark.unit
    def test_long_text_truncated(self):
        """Long evidence text should be truncated."""
        long_text = "x" * 1000
        evidence = [{
            "temporal_slice": "MID",
            "book": "Test",
            "chunk_idx": 0,
            "score": 0.5,
            "text": long_text
        }]
        result = format_temporal_evidence(evidence)
        
        # Should be truncated to ~600 chars + "..."
        assert "..." in result


class TestGenerateDossier:
    """Tests for the generate_dossier function."""
    
    @pytest.mark.unit
    def test_generates_markdown(self, sample_verdict, sample_evidence):
        """Should generate valid markdown."""
        result = generate_dossier(sample_verdict, sample_evidence)
        
        assert isinstance(result, str)
        assert "# Constraint-Linked Dossier" in result or "# Claim Dossier" in result
        assert "Verdict" in result
    
    @pytest.mark.unit
    def test_includes_claim_info(self, sample_verdict, sample_evidence):
        """Should include claim information."""
        result = generate_dossier(sample_verdict, sample_evidence)
        
        assert sample_evidence["character"] in result
        assert sample_evidence["book_name"] in result
    
    @pytest.mark.unit
    def test_includes_verdict_badge(self, sample_verdict, sample_evidence):
        """Should include verdict badge."""
        result = generate_dossier(sample_verdict, sample_evidence)
        
        # Supported should have checkmark
        assert "✅" in result or "SUPPORTED" in result
    
    @pytest.mark.unit
    def test_includes_confidence(self, sample_verdict, sample_evidence):
        """Should include confidence bar."""
        result = generate_dossier(sample_verdict, sample_evidence)
        
        assert "Confidence" in result
        assert "█" in result or "░" in result
