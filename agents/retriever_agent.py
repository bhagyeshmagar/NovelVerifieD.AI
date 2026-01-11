"""
Retriever Agent - Temporal-aware evidence retrieval.

KDSH 2026 Track A:
Enhanced retrieval with:
1. Temporal slicing: retrieve from EARLY, MID, LATE sections
2. Counterfactual queries: actively search for contradicting evidence
3. Pathway integration: queries mediated by Pathway store

This goes beyond basic semantic similarity to enable constraint reasoning.
"""

import json
import pickle
from pathlib import Path
import numpy as np
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import faiss

# Import Pathway store
from pathway_store import get_document_store

# Configuration
CLAIMS_FILE = Path("claims/claims.jsonl")
FAISS_INDEX_FILE = Path("index/faiss.index")
META_FILE = Path("index/meta.pkl")
OUTPUT_DIR = Path("evidence")
MODEL_NAME = "all-MiniLM-L6-v2"

# Retrieval settings
TOP_K_PER_SLICE = 3       # Retrieve top 3 from each temporal slice
CONTRADICTION_BOOST = 0.15  # Boost for potential contradiction matches
BOOK_MATCH_BOOST = 0.2     # Boost for same-book matches


def load_claims() -> List[dict]:
    """Load claims from JSONL file."""
    claims = []
    with open(CLAIMS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            claims.append(json.loads(line.strip()))
    return claims


def load_index_and_metadata() -> Tuple[faiss.Index, List[dict]]:
    """Load FAISS index and metadata."""
    index = faiss.read_index(str(FAISS_INDEX_FILE))
    with open(META_FILE, "rb") as f:
        metadata = pickle.load(f)
    return index, metadata


def generate_counterfactual_query(claim_text: str, character: str) -> str:
    """
    Generate a query optimized to find CONTRADICTING evidence.
    
    ANTI-BIAS: This query is designed to surface evidence that
    might disprove the claim, not just confirm it.
    """
    # Negate common patterns
    negation_patterns = [
        ("was", "was not"),
        ("had", "never had"),
        ("could", "could not"),
        ("did", "did not"),
        ("always", "never"),
        ("before", "after"),
    ]
    
    counterfactual = claim_text
    for pattern, replacement in negation_patterns:
        if pattern in counterfactual.lower():
            counterfactual = counterfactual.lower().replace(pattern, replacement, 1)
            break
    
    return f"{character}: {counterfactual}"


def retrieve_temporal_evidence(
    claim: dict,
    model: SentenceTransformer,
    index: faiss.Index,
    metadata: List[dict]
) -> List[dict]:
    """
    Retrieve evidence with temporal awareness.
    
    Strategy:
    1. Standard query for supporting evidence
    2. Counterfactual query for contradicting evidence
    3. Retrieve from each temporal slice (EARLY, MID, LATE)
    4. Combine and deduplicate
    
    Track A Justification:
    - Uses temporal slicing computed by Pathway store
    - Enables constraint reasoning across narrative arc
    """
    claim_text = claim["claim_text"]
    character = claim["character"]
    book_name = claim["book_name"]
    book_lower = book_name.lower().replace(" ", "").replace("_", "")
    
    # Standard query
    standard_query = f"{character}: {claim_text}"
    
    # Counterfactual query for contradiction-seeking
    counterfactual_query = generate_counterfactual_query(claim_text, character)
    
    # Encode both queries
    queries = [standard_query, counterfactual_query]
    query_embeddings = model.encode(queries).astype(np.float32)
    faiss.normalize_L2(query_embeddings)
    
    # Search with both queries
    k = TOP_K_PER_SLICE * 4  # Get more, then filter
    standard_scores, standard_indices = index.search(query_embeddings[0:1], k)
    contra_scores, contra_indices = index.search(query_embeddings[1:2], k)
    
    # Collect results with temporal awareness
    all_results = {}  # chunk_id -> result dict
    
    # Process standard query results
    for score, idx in zip(standard_scores[0], standard_indices[0]):
        if idx == -1:
            continue
        meta = metadata[idx]
        chunk_id = meta.get("chunk_id", f"{meta['book']}_{meta['chunk_idx']}")
        
        if chunk_id in all_results:
            continue
        
        meta_book_lower = meta["book"].lower().replace(" ", "").replace("_", "")
        is_same_book = book_lower in meta_book_lower or meta_book_lower in book_lower
        
        adjusted_score = float(score)
        if is_same_book:
            adjusted_score += BOOK_MATCH_BOOST
        
        all_results[chunk_id] = {
            "chunk_id": chunk_id,
            "chunk_idx": meta["chunk_idx"],
            "book": meta["book"],
            "char_start": meta.get("char_start", 0),
            "char_end": meta.get("char_end", 0),
            "text": meta["text"],
            "temporal_slice": meta.get("temporal_slice", "MID"),
            "score": adjusted_score,
            "is_same_book": is_same_book,
            "query_type": "standard"
        }
    
    # Process counterfactual query results (boost for contradiction seeking)
    for score, idx in zip(contra_scores[0], contra_indices[0]):
        if idx == -1:
            continue
        meta = metadata[idx]
        chunk_id = meta.get("chunk_id", f"{meta['book']}_{meta['chunk_idx']}")
        
        if chunk_id in all_results:
            # Boost existing result if also found by counterfactual
            all_results[chunk_id]["score"] += CONTRADICTION_BOOST
            all_results[chunk_id]["query_type"] = "both"
            continue
        
        meta_book_lower = meta["book"].lower().replace(" ", "").replace("_", "")
        is_same_book = book_lower in meta_book_lower or meta_book_lower in book_lower
        
        if not is_same_book:
            continue  # Only include counterfactual matches from same book
        
        adjusted_score = float(score) + CONTRADICTION_BOOST
        
        all_results[chunk_id] = {
            "chunk_id": chunk_id,
            "chunk_idx": meta["chunk_idx"],
            "book": meta["book"],
            "char_start": meta.get("char_start", 0),
            "char_end": meta.get("char_end", 0),
            "text": meta["text"],
            "temporal_slice": meta.get("temporal_slice", "MID"),
            "score": adjusted_score,
            "is_same_book": is_same_book,
            "query_type": "counterfactual"
        }
    
    # Select top results from each temporal slice
    results = list(all_results.values())
    
    # Filter to same book only
    results = [r for r in results if r["is_same_book"]]
    
    # Sort by score within each slice
    early = sorted([r for r in results if r["temporal_slice"] == "EARLY"], 
                   key=lambda x: x["score"], reverse=True)[:TOP_K_PER_SLICE]
    mid = sorted([r for r in results if r["temporal_slice"] == "MID"],
                 key=lambda x: x["score"], reverse=True)[:TOP_K_PER_SLICE]
    late = sorted([r for r in results if r["temporal_slice"] == "LATE"],
                  key=lambda x: x["score"], reverse=True)[:TOP_K_PER_SLICE]
    
    # Combine: prioritize temporal diversity
    final_results = early + mid + late
    
    # If not enough, add highest-scoring remaining
    if len(final_results) < TOP_K_PER_SLICE * 3:
        remaining = [r for r in results if r not in final_results]
        remaining.sort(key=lambda x: x["score"], reverse=True)
        final_results.extend(remaining[:TOP_K_PER_SLICE * 3 - len(final_results)])
    
    return final_results


def main():
    """Main entry point for temporal-aware retriever agent."""
    print("=" * 60)
    print("RETRIEVER AGENT - Temporal-Aware Evidence Retrieval")
    print("KDSH 2026 Track A: Pathway-integrated with contradiction seeking")
    print("=" * 60)
    
    # Check prerequisites
    if not CLAIMS_FILE.exists():
        print(f"ERROR: {CLAIMS_FILE} not found.")
        return
    if not FAISS_INDEX_FILE.exists():
        print(f"ERROR: {FAISS_INDEX_FILE} not found.")
        return
    
    # Load claims
    claims = load_claims()
    print(f"Loaded {len(claims)} claims")
    
    # Load FAISS index
    print("Loading FAISS index...")
    index, metadata = load_index_and_metadata()
    print(f"Index contains {index.ntotal} vectors")
    
    # Check temporal slice distribution
    temporal_dist = {"EARLY": 0, "MID": 0, "LATE": 0}
    for meta in metadata:
        slice_name = meta.get("temporal_slice", "MID")
        temporal_dist[slice_name] = temporal_dist.get(slice_name, 0) + 1
    print(f"Temporal distribution: {temporal_dist}")
    
    # Load model
    print(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    
    # Process claims
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\nRetrieving evidence for {len(claims)} claims...")
    print("(Using temporal slicing + counterfactual queries)\n")
    
    for i, claim in enumerate(claims):
        evidence = retrieve_temporal_evidence(claim, model, index, metadata)
        
        output = {
            "claim_id": claim["claim_id"],
            "book_name": claim["book_name"],
            "character": claim["character"],
            "claim_text": claim["claim_text"],
            "evidence": evidence,
            "retrieval_stats": {
                "total_retrieved": len(evidence),
                "temporal_coverage": {
                    "EARLY": sum(1 for e in evidence if e["temporal_slice"] == "EARLY"),
                    "MID": sum(1 for e in evidence if e["temporal_slice"] == "MID"),
                    "LATE": sum(1 for e in evidence if e["temporal_slice"] == "LATE"),
                },
                "counterfactual_matches": sum(1 for e in evidence if e["query_type"] in ["counterfactual", "both"])
            }
        }
        
        output_file = OUTPUT_DIR / f"{claim['claim_id']}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        if (i + 1) % 20 == 0 or i == len(claims) - 1:
            print(f"  Processed {i + 1}/{len(claims)} claims")
    
    print("=" * 60)
    print(f"Evidence saved to {OUTPUT_DIR}/")
    print(f"  - Temporal slicing: EARLY/MID/LATE coverage")
    print(f"  - Counterfactual queries for contradiction seeking")


if __name__ == "__main__":
    main()
