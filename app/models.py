from datetime import datetime
from .db import db

class File(db.Model):
    __tablename__ = "files"
    id = db.Column(db.Integer, primary_key=True)
    file_key = db.Column(db.String(255), index=True, nullable=False)
    original_filename = db.Column(db.String(512), nullable=False)
    stored_filename = db.Column(db.String(512), nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    size_bytes = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(128), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
