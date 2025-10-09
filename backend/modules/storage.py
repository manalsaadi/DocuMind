"""
Persistent Storage Module for DocuMind Backend

Handles document metadata persistence using JSON file storage.
This ensures document information survives server restarts.
"""

import json
import os
from typing import Dict, Any, List
from pathlib import Path
import threading
from contextlib import contextmanager


class DocumentStorage:
    """
    Simple JSON-based persistent storage for document metadata
    Thread-safe with threading locks (cross-platform)
    """
    
    def __init__(self, storage_file: str = "documents.json"):
        self.storage_file = Path(storage_file)
        self._lock = threading.RLock()
        self.ensure_storage_file()
    
    def ensure_storage_file(self):
        """Create storage file if it doesn't exist"""
        if not self.storage_file.exists():
            with self._lock:
                self.storage_file.write_text('{}')
    
    def load_documents(self) -> Dict[str, Dict[str, Any]]:
        """Load all documents from storage"""
        with self._lock:
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    return data
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
    
    def save_documents(self, documents: Dict[str, Dict[str, Any]]):
        """Save all documents to storage"""
        with self._lock:
            with open(self.storage_file, 'w') as f:
                json.dump(documents, f, indent=2, default=str)
    
    def add_document(self, doc_id: str, document_data: Dict[str, Any]):
        """Add a single document to storage"""
        with self._lock:
            documents = self.load_documents()
            documents[doc_id] = document_data
            self.save_documents(documents)
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from storage"""
        with self._lock:
            documents = self.load_documents()
            if doc_id in documents:
                del documents[doc_id]
                self.save_documents(documents)
                return True
            return False
    
    def get_document(self, doc_id: str) -> Dict[str, Any] | None:
        """Get a specific document by ID"""
        with self._lock:
            documents = self.load_documents()
            return documents.get(doc_id)
    
    def document_exists(self, doc_id: str) -> bool:
        """Check if document exists in storage"""
        with self._lock:
            documents = self.load_documents()
            return doc_id in documents
    
    def update_document(self, doc_id: str, updates: Dict[str, Any]):
        """Update specific fields of a document"""
        with self._lock:
            documents = self.load_documents()
            if doc_id in documents:
                documents[doc_id].update(updates)
                self.save_documents(documents)
    
    def list_all_documents(self) -> List[Dict[str, Any]]:
        """Get list of all documents"""
        with self._lock:
            documents = self.load_documents()
            return list(documents.values())
    
    def cleanup_orphaned_files(self):
        """Remove temporary files for documents not in storage"""
        import tempfile
        import glob
        
        documents = self.load_documents()
        active_temp_paths = {doc.get('temp_path') for doc in documents.values() if doc.get('temp_path')}
        
        # Find all temp files with our pattern
        temp_dir = tempfile.gettempdir()
        our_temp_files = glob.glob(os.path.join(temp_dir, "tmp*_*"))
        
        cleaned_count = 0
        for temp_file in our_temp_files:
            if temp_file not in active_temp_paths:
                try:
                    os.unlink(temp_file)
                    cleaned_count += 1
                except OSError:
                    pass  # File might already be deleted
        
        return cleaned_count


# Global storage instance
document_storage = DocumentStorage("documents.json")