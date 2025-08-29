import os, re
from werkzeug.utils import secure_filename

def normalize_file_key(filename: str) -> str:
    name = os.path.splitext(filename)[0].strip().lower()
    name = re.sub(r"[^a-z0-9._-]+", "-", name)
    return name or "file"

def safe_store_name(original_filename: str, version: int) -> str:
    stem, ext = os.path.splitext(original_filename)
    stem = secure_filename(stem) or "file"
    return f"{stem}__v{version}{ext}"
