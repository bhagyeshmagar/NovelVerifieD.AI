"""
File Upload API for NovelVerified.AI

Handles file uploads in various formats:
- PDF (using PyMuPDF)
- DOCX (using python-docx)
- TXT (plain text)

Saves extracted text to data/novels/ and optionally triggers pipeline.
"""

import os
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
upload_bp = Blueprint('upload', __name__)

# Configuration
UPLOAD_FOLDER = Path(__file__).parent.parent / "data" / "novels"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Ensure upload folder exists
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from PDF using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(file_path)
        text_parts = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text_parts.append(page.get_text())
        
        doc.close()
        return "\n".join(text_parts)
        
    except ImportError:
        logger.error("PyMuPDF not installed. Run: pip install pymupdf")
        raise ValueError("PDF support requires PyMuPDF. Install with: pip install pymupdf")
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def extract_text_from_docx(file_path: Path) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document
        
        doc = Document(file_path)
        text_parts = []
        
        for paragraph in doc.paragraphs:
            text_parts.append(paragraph.text)
        
        return "\n".join(text_parts)
        
    except ImportError:
        logger.error("python-docx not installed. Run: pip install python-docx")
        raise ValueError("DOCX support requires python-docx. Install with: pip install python-docx")
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")


def extract_text_from_txt(file_path: Path) -> str:
    """Read plain text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with latin-1 encoding as fallback
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()


def extract_text(file_path: Path) -> str:
    """Extract text from file based on extension."""
    ext = file_path.suffix.lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    elif ext == '.txt':
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


@upload_bp.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Upload a novel file (PDF, DOCX, or TXT).
    
    Auto-saves previous results to history before clearing data.
    Sets the new novel as the current active novel for claims.
    
    Returns:
        JSON with success status, filename, and character count.
    """
    import shutil
    import json
    from datetime import datetime
    
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file was selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file extension
    if not allowed_file(file.filename):
        return jsonify({
            'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    try:
        # === STEP 1: Auto-save previous results to history ===
        results_file = PROJECT_ROOT / "output" / "results.csv"
        if results_file.exists():
            history_dir = PROJECT_ROOT / "history"
            history_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now()
            run_id = timestamp.strftime("%Y%m%d_%H%M%S")
            run_dir = history_dir / f"run_{run_id}"
            run_dir.mkdir(exist_ok=True)
            
            # Copy results
            shutil.copy(results_file, run_dir / "results.csv")
            
            # Copy verdicts
            verdicts_src = PROJECT_ROOT / "verdicts"
            if verdicts_src.exists():
                verdicts_dst = run_dir / "verdicts"
                verdicts_dst.mkdir(exist_ok=True)
                for f in verdicts_src.glob("*.json"):
                    shutil.copy(f, verdicts_dst / f.name)
            
            # Copy dossiers
            dossiers_src = PROJECT_ROOT / "dossiers"
            if dossiers_src.exists():
                dossiers_dst = run_dir / "dossiers"
                dossiers_dst.mkdir(exist_ok=True)
                for f in dossiers_src.glob("*.md"):
                    shutil.copy(f, dossiers_dst / f.name)
            
            # Get previous novel name
            current_novel_file = PROJECT_ROOT / "data" / ".current_novel"
            prev_novel = current_novel_file.read_text().strip() if current_novel_file.exists() else "Unknown"
            
            # Save metadata
            run_meta = {
                'id': run_id,
                'timestamp': timestamp.isoformat(),
                'display_time': timestamp.strftime("%b %d, %Y %I:%M %p"),
                'model_type': 'ollama',
                'novel_name': prev_novel,
                'auto_saved': True
            }
            with open(run_dir / "meta.json", 'w') as f:
                json.dump(run_meta, f, indent=2)
            
            # Update runs.json
            runs_file = history_dir / "runs.json"
            runs = []
            if runs_file.exists():
                with open(runs_file, 'r') as f:
                    runs = json.load(f)
            runs.insert(0, run_meta)
            with open(runs_file, 'w') as f:
                json.dump(runs, f, indent=2)
            
            logger.info(f"Auto-saved previous run to history: {run_id}")
        
        # === STEP 2: Clear previous pipeline data ===
        for dir_name in ["chunks", "index", "claims", "evidence", "verdicts", "dossiers"]:
            dir_path = PROJECT_ROOT / dir_name
            if dir_path.exists():
                for f in dir_path.glob("*"):
                    if f.is_file():
                        f.unlink()
        
        if results_file.exists():
            results_file.unlink()
        
        # === STEP 3: Process and save new file ===
        filename = secure_filename(file.filename)
        temp_path = UPLOAD_FOLDER / f"temp_{filename}"
        file.save(temp_path)
        
        # Check file size
        if temp_path.stat().st_size > MAX_FILE_SIZE:
            temp_path.unlink()
            return jsonify({'error': 'File too large. Maximum size: 50MB'}), 400
        
        # Extract text
        text = extract_text(temp_path)
        
        # Remove temp file
        temp_path.unlink()
        
        if not text.strip():
            return jsonify({'error': 'No text could be extracted from file'}), 400
        
        # Save as .txt file
        base_name = Path(filename).stem
        # Clean book name for consistency
        book_name = base_name.replace('_', ' ').replace('-', ' ')
        output_filename = f"{base_name}.txt"
        output_path = UPLOAD_FOLDER / output_filename
        
        # Handle duplicate filenames
        counter = 1
        while output_path.exists():
            output_filename = f"{base_name}_{counter}.txt"
            output_path = UPLOAD_FOLDER / output_filename
            counter += 1
        
        # Write extracted text
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # === STEP 4: Set as current novel and init empty claims ===
        current_novel_file = PROJECT_ROOT / "data" / ".current_novel"
        current_novel_file.write_text(book_name)
        
        # Init empty train.csv
        train_csv = PROJECT_ROOT / "data" / "train.csv"
        with open(train_csv, 'w', encoding='utf-8', newline='') as f:
            f.write("id,book_name,char,caption,content,label\n")
        
        logger.info(f"Uploaded and processed: {output_filename} ({len(text)} characters)")
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'book_name': book_name,
            'original_filename': filename,
            'characters': len(text),
            'words': len(text.split()),
            'history_saved': results_file.exists(),
            'message': f'File uploaded successfully. Previous data saved to history. Add claims for {book_name}.'
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@upload_bp.route('/api/novels', methods=['GET'])
def list_novels():
    """List all uploaded novels."""
    novels = []
    
    for file_path in UPLOAD_FOLDER.glob('*.txt'):
        stat = file_path.stat()
        novels.append({
            'filename': file_path.name,
            'size': stat.st_size,
            'modified': stat.st_mtime
        })
    
    return jsonify({
        'novels': sorted(novels, key=lambda x: x['modified'], reverse=True)
    })


@upload_bp.route('/api/novels/<filename>', methods=['DELETE'])
def delete_novel(filename):
    """Delete a novel file."""
    safe_filename = secure_filename(filename)
    file_path = UPLOAD_FOLDER / safe_filename
    
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
    
    try:
        file_path.unlink()
        return jsonify({'success': True, 'message': f'Deleted {safe_filename}'})
    except Exception as e:
        return jsonify({'error': f'Failed to delete: {str(e)}'}), 500





@upload_bp.route('/api/data/clear', methods=['POST'])
def clear_data():
    """
    Clear all previous pipeline data to start fresh with a new novel.
    
    Removes: chunks, index, claims, evidence, verdicts, dossiers, results
    """
    import shutil
    
    PROJECT_ROOT = Path(__file__).parent.parent
    
    directories_to_clear = [
        PROJECT_ROOT / "chunks",
        PROJECT_ROOT / "index", 
        PROJECT_ROOT / "claims",
        PROJECT_ROOT / "evidence",
        PROJECT_ROOT / "verdicts",
        PROJECT_ROOT / "dossiers",
    ]
    
    files_to_clear = [
        PROJECT_ROOT / "output" / "results.csv",
    ]
    
    cleared = []
    errors = []
    
    # Clear directories
    for dir_path in directories_to_clear:
        if dir_path.exists():
            try:
                for file in dir_path.glob("*"):
                    if file.is_file():
                        file.unlink()
                cleared.append(str(dir_path.name))
            except Exception as e:
                errors.append(f"{dir_path.name}: {str(e)}")
    
    # Clear files
    for file_path in files_to_clear:
        if file_path.exists():
            try:
                file_path.unlink()
                cleared.append(str(file_path.name))
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")
    
    if errors:
        return jsonify({
            'success': False,
            'cleared': cleared,
            'errors': errors
        }), 500
    
    logger.info(f"Cleared previous data: {cleared}")
    
    return jsonify({
        'success': True,
        'cleared': cleared,
        'message': 'Previous data cleared. Ready for new novel upload.'
    })
