#!/usr/bin/env python3
"""
KDSH 2026 Submission Package Creator

Creates the submission ZIP file with all required components:
- Code (reproducible)
- Results file (results.csv)
- Report (to be added manually)

Usage:
    python create_submission.py
"""

import subprocess
import sys
import zipfile
from pathlib import Path
from datetime import datetime

# Team name
TEAM_NAME = "StrawHats"

# Directories and files to include
INCLUDE_DIRS = [
    "agents",
    "flask_api",
    "frontend",
    "data",
    "tests",
    "scripts",
]

INCLUDE_FILES = [
    "run_all.py",
    "requirements.txt",
    "pytest.ini",
    ".env.example",
    "README.md",
    "output/results.csv",  # KDSH submission format
]

# Directories to exclude
EXCLUDE_PATTERNS = [
    "__pycache__",
    ".git",
    ".venv",
    "node_modules",
    ".pytest_cache",
    "*.pyc",
    "*.log",
    ".env",  # Don't include actual API keys
    "pathway",  # Too large, use submodule
    "llm-app",  # Too large, use submodule
    "history",  # Run history
    "chunks",
    "index",
    "claims",
    "evidence",
    "verdicts",
    "dossiers",
]


def should_exclude(path: Path) -> bool:
    """Check if path should be excluded."""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in str(path):
            return True
    return False


def run_pipeline():
    """Run the full pipeline to generate results."""
    print("Running full pipeline...")
    result = subprocess.run(
        [sys.executable, "run_all.py"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Pipeline failed:\n{result.stderr}")
        return False
    print("Pipeline completed successfully!")
    return True


def create_submission_zip():
    """Create the KDSH submission ZIP file."""
    zip_name = f"{TEAM_NAME}_KDSH_2026.zip"
    zip_path = Path(zip_name)
    
    print(f"\nCreating submission: {zip_name}")
    print("=" * 50)
    
    # Check if results.csv exists
    results_file = Path("output/results.csv")
    if not results_file.exists():
        print("WARNING: results.csv not found. Run the pipeline first.")
        print("  You can run: python run_all.py")
        # Don't fail, user might add it manually
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add directories
        for dir_name in INCLUDE_DIRS:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                print(f"  Skipping missing directory: {dir_name}")
                continue
            
            for file_path in dir_path.rglob("*"):
                if file_path.is_file() and not should_exclude(file_path):
                    arcname = str(file_path)
                    zf.write(file_path, arcname)
                    print(f"  Added: {arcname}")
        
        # Add individual files
        for file_name in INCLUDE_FILES:
            file_path = Path(file_name)
            if file_path.exists():
                zf.write(file_path, file_name)
                print(f"  Added: {file_name}")
            else:
                print(f"  Skipping missing file: {file_name}")
    
    print("=" * 50)
    print(f"\n✅ Created: {zip_path.absolute()}")
    print(f"   Size: {zip_path.stat().st_size / 1024:.1f} KB")
    
    # Remind about report
    print("\n" + "=" * 50)
    print("📝 REMINDER: Add your report to the ZIP file!")
    print("   Required: Max 10 pages PDF describing your approach")
    print("=" * 50)
    
    return zip_path


def verify_results_format():
    """Verify results.csv has correct KDSH format."""
    results_file = Path("output/results.csv")
    if not results_file.exists():
        return False
    
    with open(results_file, "r", encoding="utf-8") as f:
        header = f.readline().strip()
    
    expected = "Story ID,Prediction,Rationale"
    if header != expected:
        print(f"WARNING: results.csv header mismatch!")
        print(f"  Expected: {expected}")
        print(f"  Found: {header}")
        return False
    
    print("✅ results.csv format verified!")
    return True


def main():
    print("=" * 60)
    print(f"KDSH 2026 Submission Creator - Team {TEAM_NAME}")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Verify results format
    if Path("output/results.csv").exists():
        verify_results_format()
    
    # Create ZIP
    zip_path = create_submission_zip()
    
    # List contents
    print("\n📦 ZIP Contents:")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for info in zf.infolist()[:20]:  # Show first 20
            print(f"  {info.filename}")
        total = len(zf.infolist())
        if total > 20:
            print(f"  ... and {total - 20} more files")
        print(f"\n  Total files: {total}")


if __name__ == "__main__":
    main()
