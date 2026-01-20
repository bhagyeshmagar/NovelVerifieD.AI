"""Tests for the ingestion agent."""

import sys
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.ingestion_agent import count_tokens, chunk_text
import tiktoken


class TestCountTokens:
    """Tests for the count_tokens function."""
    
    @pytest.fixture
    def encoding(self):
        """Get tiktoken encoding."""
        return tiktoken.get_encoding("cl100k_base")
    
    @pytest.mark.unit
    def test_empty_string(self, encoding):
        """Empty string should have 0 tokens."""
        assert count_tokens("", encoding) == 0
    
    @pytest.mark.unit
    def test_simple_text(self, encoding):
        """Simple text should tokenize correctly."""
        result = count_tokens("Hello world", encoding)
        assert result > 0
        assert result < 10  # Should be small
    
    @pytest.mark.unit
    def test_longer_text(self, encoding):
        """Longer text should have more tokens."""
        short = count_tokens("Hello", encoding)
        long = count_tokens("Hello world, this is a longer sentence.", encoding)
        assert long > short


class TestChunkText:
    """Tests for the chunk_text function."""
    
    @pytest.fixture
    def encoding(self):
        """Get tiktoken encoding."""
        return tiktoken.get_encoding("cl100k_base")
    
    @pytest.mark.unit
    def test_empty_text(self, encoding):
        """Empty text should return empty list."""
        result = chunk_text("", encoding)
        assert result == []
    
    @pytest.mark.unit
    def test_short_text_single_chunk(self, encoding):
        """Text shorter than chunk size should return single chunk."""
        text = "This is a short text that fits in one chunk."
        result = chunk_text(text, encoding, chunk_size=100, overlap=10)
        assert len(result) == 1
        assert result[0]["chunk_idx"] == 0
        assert result[0]["text"] == text
    
    @pytest.mark.unit
    def test_long_text_multiple_chunks(self, encoding):
        """Long text should be split into multiple chunks."""
        # Create text that's longer than chunk size
        text = " ".join(["word"] * 500)  # ~500 tokens
        result = chunk_text(text, encoding, chunk_size=100, overlap=20)
        assert len(result) > 1
    
    @pytest.mark.unit
    def test_chunk_indices_sequential(self, encoding):
        """Chunk indices should be sequential."""
        text = " ".join(["word"] * 500)
        result = chunk_text(text, encoding, chunk_size=100, overlap=20)
        for i, chunk in enumerate(result):
            assert chunk["chunk_idx"] == i
    
    @pytest.mark.unit
    def test_chunks_have_required_fields(self, encoding):
        """Each chunk should have all required fields."""
        text = " ".join(["word"] * 200)
        result = chunk_text(text, encoding, chunk_size=100, overlap=20)
        
        required_fields = ["chunk_idx", "char_start", "char_end", "text", "token_count"]
        for chunk in result:
            for field in required_fields:
                assert field in chunk, f"Missing field: {field}"
    
    @pytest.mark.unit
    def test_token_count_within_limit(self, encoding):
        """Each chunk's token count should not exceed chunk size."""
        text = " ".join(["word"] * 500)
        chunk_size = 100
        result = chunk_text(text, encoding, chunk_size=chunk_size, overlap=20)
        
        for chunk in result:
            assert chunk["token_count"] <= chunk_size + 10  # Allow small margin


class TestProcessNovel:
    """Integration tests for novel processing."""
    
    @pytest.mark.integration
    def test_process_novel_creates_chunks(self, temp_novel_file):
        """Processing a novel file should create chunks."""
        from agents.ingestion_agent import process_novel
        encoding = tiktoken.get_encoding("cl100k_base")
        
        chunks, total_chars = process_novel(temp_novel_file, encoding)
        
        assert len(chunks) > 0
        assert all("book" in c for c in chunks)
        assert all(c["book"] == "test_novel" for c in chunks)
        assert total_chars > 0
