"""
Claim Parser Agent - Parses train/test CSV files into structured claims.

Reads data/train.csv and data/test.csv, extracts claims,
and outputs claims/claims.jsonl.
"""

import csv
import json
from pathlib import Path

# Configuration
TRAIN_FILE = Path("Data/train.csv")
TEST_FILE = Path("Data/test.csv")
OUTPUT_FILE = Path("claims/claims.jsonl")


def parse_csv(filepath: Path, has_label: bool) -> list[dict]:
    """Parse a CSV file into claim records."""
    claims = []
    
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            claim = {
                "claim_id": row["id"],
                "book_name": row["book_name"],
                "character": row["char"],
                "caption": row.get("caption", ""),
                "claim_text": row["content"],
                "source": filepath.stem  # "train" or "test"
            }
            
            # Add label if available (train set only)
            if has_label and "label" in row:
                claim["label"] = row["label"]
            
            claims.append(claim)
    
    return claims


def main():
    """Main entry point for claim parser agent."""
    print("=" * 60)
    print("CLAIM PARSER AGENT - CSV to JSONL")
    print("=" * 60)
    
    all_claims = []
    
    # Parse train.csv
    if TRAIN_FILE.exists():
        train_claims = parse_csv(TRAIN_FILE, has_label=True)
        print(f"Parsed {len(train_claims)} claims from train.csv")
        all_claims.extend(train_claims)
    else:
        print(f"WARNING: {TRAIN_FILE} not found")
    
    # Parse test.csv
    if TEST_FILE.exists():
        test_claims = parse_csv(TEST_FILE, has_label=False)
        print(f"Parsed {len(test_claims)} claims from test.csv")
        all_claims.extend(test_claims)
    else:
        print(f"WARNING: {TEST_FILE} not found")
    
    if not all_claims:
        print("ERROR: No claims found!")
        return
    
    # Save to JSONL
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for claim in all_claims:
            f.write(json.dumps(claim, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_claims)} claims to {OUTPUT_FILE}")
    
    # Summary
    print("=" * 60)
    train_count = sum(1 for c in all_claims if c["source"] == "train")
    test_count = sum(1 for c in all_claims if c["source"] == "test")
    print(f"  Train claims: {train_count}")
    print(f"  Test claims: {test_count}")
    
    books = set(c["book_name"] for c in all_claims)
    print(f"  Books: {', '.join(sorted(books))}")
    
    characters = set(c["character"] for c in all_claims)
    print(f"  Characters: {len(characters)} unique")


if __name__ == "__main__":
    main()
