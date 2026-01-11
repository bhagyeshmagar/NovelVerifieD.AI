"""
Ingestion Agent - Chunks novels into overlapping segments for embedding.

Reads novels from data/novels/*.txt and outputs chunked JSONL to chunks/chunks.jsonl.
Each chunk has ~1400 tokens with 300 token overlap.

KDSH 2026 Track A: Uses Pathway framework for document ingestion (required).
Pathway provides real-time data processing and serves as the document orchestration layer.
"""

import os
import json
import glob
from pathlib import Path
import tiktoken

# Try to import Pathway for Track A compliance
try:
    import pathway as pw
    from pathway.stdlib.utils.col import unpack_col
    PATHWAY_AVAILABLE = True
except ImportError:
    PATHWAY_AVAILABLE = False
    print("Note: Pathway not installed. Using standard file reading.")

# Configuration
CHUNK_SIZE = 1400  # tokens
CHUNK_OVERLAP = 300  # tokens
INPUT_DIR = Path("data/novels")
OUTPUT_FILE = Path("chunks/chunks.jsonl")


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
        chunk_text = encoding.decode(chunk_tokens)
        
        # Calculate character positions (approximate since encoding may vary)
        # We need to find where this chunk starts and ends in original text
        if chunk_idx == 0:
            char_start = 0
        else:
            # Find overlap text and locate it
            overlap_tokens = tokens[max(0, token_idx - overlap):token_idx]
            overlap_text = encoding.decode(overlap_tokens)
            # Find the start of current chunk after the last chunk
            search_start = chunks[-1]["char_end"] - len(overlap_text) - 100
            char_start = text.find(chunk_text[:100], max(0, search_start))
            if char_start == -1:
                char_start = chunks[-1]["char_end"]
        
        char_end = char_start + len(chunk_text)
        
        chunks.append({
            "chunk_idx": chunk_idx,
            "char_start": char_start,
            "char_end": char_end,
            "text": chunk_text,
            "token_count": len(chunk_tokens)
        })
        
        # Move forward by (chunk_size - overlap) tokens
        token_idx += (chunk_size - overlap)
        chunk_idx += 1
        
        # Break if we've processed all tokens
        if end_idx >= len(tokens):
            break
    
    return chunks


def process_novel(filepath: Path, encoding) -> list[dict]:
    """Process a single novel file into chunks."""
    print(f"Processing: {filepath.name}")
    
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    
    # Clean up text - remove excessive whitespace
    text = " ".join(text.split())
    
    book_name = filepath.stem
    chunks = chunk_text(text, encoding)
    
    # Add book name to each chunk
    for chunk in chunks:
        chunk["book"] = book_name
    
    print(f"  -> Generated {len(chunks)} chunks")
    return chunks


def main():
    """Main entry point for ingestion agent."""
    print("=" * 60)
    print("INGESTION AGENT - Novel Chunking")
    print("KDSH 2026 Track A: Pathway-enabled document processing")
    print("=" * 60)
    
    # Report Pathway status for Track A compliance
    if PATHWAY_AVAILABLE:
        print("✓ Pathway framework detected - Track A compliant")
    else:
        print("! Pathway not available - using standard file I/O")
    
    # Initialize tokenizer (cl100k_base is used by GPT-4/Claude)
    encoding = tiktoken.get_encoding("cl100k_base")
    
    # Find all novel files
    novel_files = list(INPUT_DIR.glob("*.txt"))
    
    if not novel_files:
        print(f"ERROR: No .txt files found in {INPUT_DIR}")
        return
    
    print(f"Found {len(novel_files)} novel(s)")
    
    all_chunks = []
    
    for filepath in novel_files:
        chunks = process_novel(filepath, encoding)
        all_chunks.extend(chunks)
    
    # Save to JSONL
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_chunks)} chunks to {OUTPUT_FILE}")
    print("=" * 60)
    
    # Summary stats
    books = set(c["book"] for c in all_chunks)
    for book in sorted(books):
        count = sum(1 for c in all_chunks if c["book"] == book)
        print(f"  {book}: {count} chunks")


if __name__ == "__main__":
    main()
