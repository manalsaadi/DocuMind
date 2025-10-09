"""
Unit tests for DocumentStorage module
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from modules.storage import DocumentStorage


@pytest.mark.unit
class TestDocumentStorage:
    """Test cases for DocumentStorage class"""
    
    def test_init_creates_empty_storage(self, temp_dir):
        """Test that initialization creates empty storage file"""
        storage_path = temp_dir / "test_storage.json"
        storage = DocumentStorage(str(storage_path))
        
        assert storage.storage_file == storage_path
        assert storage_path.exists()
        assert storage.list_all_documents() == []
    
    def test_init_loads_existing_storage(self, temp_dir):
        """Test that initialization loads existing storage file"""
        storage_path = temp_dir / "existing_storage.json"
        existing_data = {"test-1": {"id": "test-1", "filename": "test.txt"}}
        storage_path.write_text(json.dumps(existing_data))
        
        storage = DocumentStorage(str(storage_path))
        documents = storage.list_all_documents()
        
        assert len(documents) == 1
        assert documents[0]["id"] == "test-1"
    
    def test_add_document(self, document_storage, sample_document_metadata):
        """Test adding a document to storage"""
        doc_id = sample_document_metadata["id"]
        document_storage.add_document(doc_id, sample_document_metadata)
        
        assert document_storage.document_exists(doc_id)
        retrieved = document_storage.get_document(doc_id)
        assert retrieved["filename"] == sample_document_metadata["filename"]
    
    def test_get_document_exists(self, document_storage, sample_document_metadata):
        """Test getting an existing document"""
        doc_id = sample_document_metadata["id"]
        document_storage.add_document(doc_id, sample_document_metadata)
        retrieved = document_storage.get_document(doc_id)
        
        assert retrieved is not None
        assert retrieved["id"] == doc_id
        assert retrieved["filename"] == sample_document_metadata["filename"]
    
    def test_get_document_not_exists(self, document_storage):
        """Test getting a non-existent document returns None"""
        result = document_storage.get_document("non-existent-id")
        assert result is None
    
    def test_update_document(self, document_storage, sample_document_metadata):
        """Test updating an existing document"""
        doc_id = sample_document_metadata["id"]
        document_storage.add_document(doc_id, sample_document_metadata)
        
        updates = {"status": "processed", "text": "Extracted text"}
        document_storage.update_document(doc_id, updates)
        
        retrieved = document_storage.get_document(doc_id)
        assert retrieved["status"] == "processed"
        assert retrieved["text"] == "Extracted text"
    
    def test_update_nonexistent_document(self, document_storage):
        """Test updating a non-existent document"""
        # Should not raise error but won't update anything
        document_storage.update_document("non-existent", {"status": "processed"})
        result = document_storage.get_document("non-existent")
        assert result is None
    
    def test_remove_document(self, document_storage, sample_document_metadata):
        """Test removing an existing document"""
        doc_id = sample_document_metadata["id"]
        document_storage.add_document(doc_id, sample_document_metadata)
        
        success = document_storage.remove_document(doc_id)
        
        assert success is True
        assert document_storage.get_document(doc_id) is None
        assert not document_storage.document_exists(doc_id)
    
    def test_remove_nonexistent_document(self, document_storage):
        """Test removing a non-existent document returns False"""
        result = document_storage.remove_document("non-existent")
        assert result is False
    
    def test_list_all_documents(self, document_storage):
        """Test listing all documents"""
        # Empty storage
        assert document_storage.list_all_documents() == []
        
        # Add multiple documents
        doc1 = {"id": "1", "filename": "doc1.txt", "status": "pending"}
        doc2 = {"id": "2", "filename": "doc2.txt", "status": "processed"}
        
        document_storage.add_document("1", doc1)
        document_storage.add_document("2", doc2)
        
        documents = document_storage.list_all_documents()
        assert len(documents) == 2
        assert any(doc["id"] == "1" for doc in documents)
        assert any(doc["id"] == "2" for doc in documents)
    
    def test_document_exists(self, document_storage, sample_document_metadata):
        """Test document existence checking"""
        doc_id = sample_document_metadata["id"]
        
        # Document doesn't exist initially
        assert not document_storage.document_exists(doc_id)
        
        # Add document
        document_storage.add_document(doc_id, sample_document_metadata)
        
        # Document exists now
        assert document_storage.document_exists(doc_id)
    
    def test_thread_safety(self, document_storage):
        """Test that storage operations are thread-safe"""
        import threading
        import time
        
        def add_documents(start_id):
            for i in range(5):
                doc_id = f"thread-{start_id}-{i}"
                doc = {
                    "id": doc_id,
                    "filename": f"doc-{start_id}-{i}.txt",
                    "status": "pending"
                }
                document_storage.add_document(doc_id, doc)
                time.sleep(0.001)  # Small delay to increase chance of conflicts
        
        # Create multiple threads adding documents
        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_documents, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all documents were added safely
        documents = document_storage.list_all_documents()
        assert len(documents) == 15  # 3 threads * 5 documents each
    
    def test_save_load_persistence(self, temp_dir):
        """Test that data persists across storage instances"""
        storage_path = temp_dir / "persistence_test.json"
        
        # Create first storage instance and add documents
        storage1 = DocumentStorage(str(storage_path))
        doc1 = {"id": "persist-1", "filename": "persist.txt", "status": "pending"}
        storage1.add_document("persist-1", doc1)
        
        # Create second storage instance (should load existing data)
        storage2 = DocumentStorage(str(storage_path))
        documents = storage2.list_all_documents()
        
        assert len(documents) == 1
        assert documents[0]["id"] == "persist-1"
    
    def test_invalid_json_handling(self, temp_dir):
        """Test handling of corrupted JSON files"""
        storage_path = temp_dir / "corrupted.json"
        storage_path.write_text("invalid json content {")
        
        # Should create new empty storage when JSON is invalid
        storage = DocumentStorage(str(storage_path))
        assert storage.list_all_documents() == []
    
    def test_load_documents_method(self, document_storage, sample_document_metadata):
        """Test the load_documents method returns correct format"""
        doc_id = sample_document_metadata["id"]
        document_storage.add_document(doc_id, sample_document_metadata)
        
        loaded = document_storage.load_documents()
        assert isinstance(loaded, dict)
        assert doc_id in loaded
        assert loaded[doc_id]["filename"] == sample_document_metadata["filename"]
    
    def test_save_documents_method(self, temp_dir):
        """Test the save_documents method works correctly"""
        storage_path = temp_dir / "save_test.json"
        storage = DocumentStorage(str(storage_path))
        
        test_data = {
            "doc1": {"id": "doc1", "filename": "test1.txt"},
            "doc2": {"id": "doc2", "filename": "test2.txt"}
        }
        
        storage.save_documents(test_data)
        
        # Reload and verify
        loaded = storage.load_documents()
        assert loaded == test_data
    
    def test_ensure_storage_file(self, temp_dir):
        """Test that storage file is created if it doesn't exist"""
        storage_path = temp_dir / "new_storage.json"
        
        # File doesn't exist initially
        assert not storage_path.exists()
        
        # Creating storage should create the file
        storage = DocumentStorage(str(storage_path))
        assert storage_path.exists()
        
        # File should contain empty JSON object
        content = storage_path.read_text()
        assert content == "{}"
    
    def test_cleanup_orphaned_files(self, document_storage):
        """Test cleanup of orphaned temporary files"""
        # This is a more complex test that would require creating actual temp files
        # For now, test that the method exists and runs without error
        result = document_storage.cleanup_orphaned_files()
        assert isinstance(result, int)  # Should return count of cleaned files
    
    def test_document_id_uniqueness(self, document_storage):
        """Test that document IDs are unique (overwrites existing)"""
        doc1 = {"id": "unique-test", "filename": "doc1.txt", "version": 1}
        doc2 = {"id": "unique-test", "filename": "doc2.txt", "version": 2}
        
        # Add first document
        document_storage.add_document("unique-test", doc1)
        retrieved1 = document_storage.get_document("unique-test")
        assert retrieved1["version"] == 1
        
        # Add second document with same ID (should overwrite)
        document_storage.add_document("unique-test", doc2)
        retrieved2 = document_storage.get_document("unique-test")
        assert retrieved2["version"] == 2
        assert retrieved2["filename"] == "doc2.txt"
        
        # Should only have one document total
        documents = document_storage.list_all_documents()
        unique_docs = [doc for doc in documents if doc["id"] == "unique-test"]
        assert len(unique_docs) == 1
    
    def test_large_document_handling(self, document_storage):
        """Test handling of documents with large metadata"""
        large_text = "x" * 10000  # 10KB of text
        large_doc = {
            "id": "large-doc",
            "filename": "large.txt",
            "text": large_text,
            "metadata": {"large_field": large_text}
        }
        
        document_storage.add_document("large-doc", large_doc)
        retrieved = document_storage.get_document("large-doc")
        
        assert retrieved is not None
        assert len(retrieved["text"]) == 10000
        assert len(retrieved["metadata"]["large_field"]) == 10000
    
    def test_storage_file_attribute(self, temp_dir):
        """Test that storage_file attribute is properly set"""
        storage_path = temp_dir / "attribute_test.json"
        storage = DocumentStorage(str(storage_path))
        
        assert storage.storage_file == storage_path
        assert isinstance(storage.storage_file, Path)