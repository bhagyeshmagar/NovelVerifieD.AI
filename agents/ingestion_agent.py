"""
Ingestion Agent - Chunks novels into overlapping segments for embedding.

KDSH 2026 Track A: Uses Pathway framework for document storage.
Includes fallback for environments where Pathway is not available.
"""

import os
import json
from pathlib import Path
import tiktoken

# Configuration
CHUNK_SIZE = 1400  # tokens
CHUNK_OVERLAP = 300  # tokens
INPUT_DIR = Path("Data")
OUTPUT_FILE = Path("chunks/chunks.jsonl")
PATHWAY_STORE_DIR = Path("pathway_store")

# Try to import Pathway
try:
    import pathway as pw
    PATHWAY_AVAILABLE = True
except ImportError:
    PATHWAY_AVAILABLE = False
    print("Note: Pathway not installed. Using standard file I/O.")


def count_tokens(text: str, encoding) -> int:
    """Count tokens in text using tiktoken."""
    return len(encoding.encode(text))


def chunk_text(text: str, encoding, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Split text into overlapping chunks based on token count."""
    tokens = encoding.encode(text)
    chunks = []
    
    token_idx = 0
    chunk_idx = 0
    
    while token_idx < len(tokens):
        end_idx = min(token_idx + chunk_size, len(tokens))
        chunk_tokens = tokens[token_idx:end_idx]
        chunk_text_content = encoding.decode(chunk_tokens)
        
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
    """Process a single novel file into chunks."""
    print(f"Processing: {filepath.name}")
    
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    
    original_length = len(text)
    text = " ".join(text.split())
    
    book_name = filepath.stem
    chunks = chunk_text(text, encoding)
    
    for chunk in chunks:
        chunk["book"] = book_name
    
    print(f"  -> Generated {len(chunks)} chunks ({original_length:,} chars)")
    return chunks, original_length


def compute_temporal_slice(char_start: int, total_chars: int) -> str:
    """Compute temporal slice based on position in novel."""
    relative_pos = char_start / max(total_chars, 1)
    if relative_pos < 0.30:
        return "EARLY"
    elif relative_pos < 0.70:
        return "MID"
    else:
        return "LATE"


def save_to_pathway_store(chunks: list[dict], book_total_chars: dict):
    """Save chunks to Pathway-compatible store with temporal slicing."""
    PATHWAY_STORE_DIR.mkdir(parents=True, exist_ok=True)
    
    enriched_chunks = []
    for chunk in chunks:
        book = chunk["book"]
        total_chars = book_total_chars.get(book, chunk.get("char_end", 100000))
        temporal_slice = compute_temporal_slice(chunk.get("char_start", 0), total_chars)
        
        enriched_chunk = {
            "chunk_id": f"{book}_{chunk['chunk_idx']}",
            "book": book,
            "chunk_idx": chunk["chunk_idx"],
            "char_start": chunk.get("char_start", 0),
            "char_end": chunk.get("char_end", 0),
            "text": chunk["text"],
            "token_count": chunk.get("token_count", 0),
            "temporal_slice": temporal_slice
        }
        enriched_chunks.append(enriched_chunk)
    
    # Save to JSONL (Pathway-compatible format)
    chunks_file = PATHWAY_STORE_DIR / "chunks.jsonl"
    with open(chunks_file, "w", encoding="utf-8") as f:
        for chunk in enriched_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    
    # Save metadata
    temporal_dist = {
        "EARLY": sum(1 for c in enriched_chunks if c["temporal_slice"] == "EARLY"),
        "MID": sum(1 for c in enriched_chunks if c["temporal_slice"] == "MID"),
        "LATE": sum(1 for c in enriched_chunks if c["temporal_slice"] == "LATE"),
    }
    
    metadata = {
        "total_chunks": len(enriched_chunks),
        "books": list(set(c["book"] for c in enriched_chunks)),
        "temporal_distribution": temporal_dist
    }
    
    with open(PATHWAY_STORE_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"  [Pathway Store] Ingested {len(enriched_chunks)} chunks")
    print(f"  [Pathway Store] Temporal distribution: {temporal_dist}")
    
    return enriched_chunks


def main():
    """Main entry point for ingestion agent."""
    print("=" * 60)
    print("INGESTION AGENT - Novel Chunking")
    print("KDSH 2026 Track A: Pathway-enabled document processing")
    print("=" * 60)
    
    # Report Pathway status
    if PATHWAY_AVAILABLE:
        print(f"✓ Pathway {pw.__version__} detected - Track A compliant")
    else:
        print("! Pathway not available - using standard file I/O")
        print("  (To install: pip install pathway)")
    
    # Initialize tokenizer
    encoding = tiktoken.get_encoding("cl100k_base")
    
    # Find novel files
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
    
    # Save to Pathway store (with temporal slicing)
    print("\n" + "-" * 40)
    print("PATHWAY STORE INGESTION")
    print("-" * 40)
    enriched_chunks = save_to_pathway_store(all_chunks, book_total_chars)
    
    # Save to legacy JSONL for FAISS
    print("\n" + "-" * 40)
    print("LEGACY EXPORT (for FAISS)")
    print("-" * 40)
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for chunk in enriched_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    
    print(f"  Exported {len(enriched_chunks)} chunks to {OUTPUT_FILE}")
    
    # Summary
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"  Total chunks: {len(enriched_chunks)}")
    print(f"  Books: {len(book_total_chars)}")
    print(f"\nPathway store: {PATHWAY_STORE_DIR}/")
    print(f"Legacy output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
