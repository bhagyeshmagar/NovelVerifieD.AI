"""
Ingestion Agent - Pathway-based document ingestion for KDSH 2026 Track A.

TRACK A REQUIREMENT:
This agent uses Pathway as the CANONICAL document store. The system cannot
function without Pathway as all chunk storage flows through PathwayDocumentStore.

Pipeline:
1. Read novels from data/novels/*.txt
2. Chunk with overlapping windows (1400 tokens, 300 overlap)
3. Compute temporal slice (EARLY/MID/LATE) for each chunk
4. Ingest into Pathway store (source of truth)
5. Export to JSONL for FAISS indexing (derived output)
"""

import os
import json
from pathlib import Path
import tiktoken

# Import Pathway store - REQUIRED for Track A compliance
import pathway as pw
from pathway_store import PathwayDocumentStore, get_document_store, export_to_legacy_format

# Configuration
CHUNK_SIZE = 1400  # tokens
CHUNK_OVERLAP = 300  # tokens
INPUT_DIR = Path("data/novels")
LEGACY_OUTPUT = Path("chunks/chunks.jsonl")  # Derived output for FAISS


def count_tokens(text: str, encoding) -> int:
    """Count tokens in text using tiktoken."""
    return len(encoding.encode(text))


def chunk_text(text: str, encoding, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Split text into overlapping chunks based on token count.
    Returns list of dicts with char_start, char_end, text.
    """
    tokens = encoding.encode(text)
    chunks = []
    
    token_idx = 0
    chunk_idx = 0
    
    while token_idx < len(tokens):
        # Get chunk of tokens
        end_idx = min(token_idx + chunk_size, len(tokens))
        chunk_tokens = tokens[token_idx:end_idx]
        
        # Decode back to text
        chunk_text_content = encoding.decode(chunk_tokens)
        
        # Calculate character positions
        if chunk_idx == 0:
            char_start = 0
        else:
            overlap_tokens = tokens[max(0, token_idx - overlap):token_idx]
            overlap_text = encoding.decode(overlap_tokens)
            search_start = chunks[-1]["char_end"] - len(overlap_text) - 100
            char_start = text.find(chunk_text_content[:100], max(0, search_start))
            if char_start == -1:
                char_start = chunks[-1]["char_end"]
        
        char_end = char_start + len(chunk_text_content)
        
        chunks.append({
            "chunk_idx": chunk_idx,
            "char_start": char_start,
            "char_end": char_end,
            "text": chunk_text_content,
            "token_count": len(chunk_tokens)
        })
        
        token_idx += (chunk_size - overlap)
        chunk_idx += 1
        
        if end_idx >= len(tokens):
            break
    
    return chunks


def process_novel(filepath: Path, encoding) -> tuple[list[dict], int]:
    """
    Process a single novel file into chunks.
    
    Returns:
        Tuple of (chunks, total_chars) for temporal slicing
    """
    print(f"Processing: {filepath.name}")
    
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    
    # Record original length for temporal slicing
    original_length = len(text)
    
    # Clean up text - remove excessive whitespace
    text = " ".join(text.split())
    
    book_name = filepath.stem
    chunks = chunk_text(text, encoding)
    
    # Add book name to each chunk
    for chunk in chunks:
        chunk["book"] = book_name
    
    print(f"  -> Generated {len(chunks)} chunks ({original_length:,} chars)")
    return chunks, original_length


def main():
    """
    Main entry point for Pathway-based ingestion agent.
    
    TRACK A COMPLIANCE:
    - Uses Pathway as the canonical document store
    - All chunks flow through PathwayDocumentStore
    - Temporal slicing computed for constraint reasoning
    """
    print("=" * 60)
    print("INGESTION AGENT - Pathway Document Store")
    print("KDSH 2026 Track A: Pathway-managed document ingestion")
    print("=" * 60)
    
    # Verify Pathway is available (Track A requirement)
    try:
        import pathway
        print(f"✓ Pathway {pathway.__version__} detected - Track A compliant")
    except ImportError as e:
        print("✗ CRITICAL: Pathway not installed!")
        print("  Track A requires Pathway. Install with: pip install pathway")
        raise e
    
    # Initialize tokenizer
    encoding = tiktoken.get_encoding("cl100k_base")
    
    # Find all novel files
    novel_files = list(INPUT_DIR.glob("*.txt"))
    
    if not novel_files:
        print(f"ERROR: No .txt files found in {INPUT_DIR}")
        return
    
    print(f"Found {len(novel_files)} novel(s)")
    
    # Process all novels
    all_chunks = []
    book_total_chars = {}
    
    for filepath in novel_files:
        chunks, total_chars = process_novel(filepath, encoding)
        all_chunks.extend(chunks)
        book_total_chars[filepath.stem] = total_chars
    
    # =========================================================================
    # PATHWAY INTEGRATION - Track A Critical Section
    # =========================================================================
    print("\n" + "-" * 40)
    print("PATHWAY STORE INGESTION")
    print("-" * 40)
    
    # Get Pathway document store
    store = get_document_store()
    
    # Ingest chunks into Pathway store with temporal slicing
    # This is the CANONICAL storage - not the JSONL file
    ingested = store.ingest_chunks(all_chunks, book_total_chars)
    
    # =========================================================================
    # LEGACY EXPORT - Derived output for FAISS compatibility
    # =========================================================================
    print("\n" + "-" * 40)
    print("LEGACY EXPORT (for FAISS)")
    print("-" * 40)
    
    # Export to JSONL for backward compatibility with FAISS indexing
    export_count = export_to_legacy_format(LEGACY_OUTPUT)
    print(f"  Exported {export_count} chunks to {LEGACY_OUTPUT}")
    
    # Summary
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    
    metadata = store.get_metadata()
    print(f"  Total chunks: {metadata['total_chunks']}")
    print(f"  Books: {len(metadata['books'])}")
    print(f"  Temporal distribution:")
    for slice_name, count in metadata['temporal_distribution'].items():
        print(f"    {slice_name}: {count} chunks")
    
    print(f"\nPathway store: pathway_store/")
    print(f"Legacy output: {LEGACY_OUTPUT}")


if __name__ == "__main__":
    main()
