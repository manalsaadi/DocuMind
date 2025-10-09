"""
Integration tests for FastAPI endpoints
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app


@pytest.mark.integration
class TestDocumentUploadAPI:
    """Integration tests for document upload endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_upload_text_file_success(self, client, temp_dir):
        """Test successful text file upload"""
        # Create a test file
        test_content = "This is a test document for upload."
        
        # Upload the file
        files = {"file": ("test.txt", test_content, "text/plain")}
        response = client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "document" in data
        assert data["document"]["filename"] == "test.txt"
        assert data["document"]["status"] == "processed"
    
    def test_upload_multiple_files(self, client):
        """Test uploading multiple files"""
        files = [
            ("files", ("doc1.txt", "Content 1", "text/plain")),
            ("files", ("doc2.txt", "Content 2", "text/plain"))
        ]
        
        response = client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["documents"]) == 2
    
    def test_upload_empty_file(self, client):
        """Test uploading empty file"""
        files = {"file": ("empty.txt", "", "text/plain")}
        response = client.post("/api/documents/upload", files=files)
        
        # Should still accept empty files
        assert response.status_code == 200
    
    def test_upload_unsupported_file_type(self, client):
        """Test uploading unsupported file type"""
        files = {"file": ("test.exe", b"binary content", "application/octet-stream")}
        response = client.post("/api/documents/upload", files=files)
        
        # Should accept but mark as unsupported
        assert response.status_code == 200
        data = response.json()
        # The processor should handle unsupported files gracefully
    
    def test_upload_no_file(self, client):
        """Test upload request without file"""
        response = client.post("/api/documents/upload", files={})
        
        assert response.status_code == 422  # Validation error
    
    @patch('modules.document_processor.DocumentProcessor.process_document')
    def test_upload_with_processing_error(self, mock_process, client):
        """Test upload when document processing fails"""
        # Mock processing to return error
        mock_process.return_value = {
            "status": "error",
            "error": "Processing failed",
            "text": "",
            "metadata": {},
            "chunks": []
        }
        
        files = {"file": ("test.txt", "content", "text/plain")}
        response = client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["document"]["status"] == "error"
    
    def test_upload_large_file(self, client, temp_dir):
        """Test uploading a large file"""
        # Create a large text content (1MB)
        large_content = "x" * (1024 * 1024)
        
        files = {"file": ("large.txt", large_content, "text/plain")}
        response = client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["document"]["size"] == len(large_content)


@pytest.mark.integration
class TestDocumentListAPI:
    """Integration tests for document listing endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_list_empty_documents(self, client):
        """Test listing when no documents exist"""
        # Clear any existing documents first
        with patch('modules.storage.DocumentStorage.list_documents', return_value=[]):
            response = client.get("/api/documents")
            
            assert response.status_code == 200
            data = response.json()
            assert data["documents"] == []
    
    def test_list_with_documents(self, client):
        """Test listing with existing documents"""
        # First upload some documents
        files = [
            ("files", ("doc1.txt", "Content 1", "text/plain")),
            ("files", ("doc2.txt", "Content 2", "text/plain"))
        ]
        upload_response = client.post("/api/documents/upload", files=files)
        assert upload_response.status_code == 200
        
        # Then list documents
        response = client.get("/api/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) >= 2  # At least the ones we uploaded
    
    @patch('modules.storage.DocumentStorage.list_documents')
    def test_list_with_storage_error(self, mock_list, client):
        """Test listing when storage error occurs"""
        mock_list.side_effect = Exception("Storage error")
        
        response = client.get("/api/documents")
        
        assert response.status_code == 500


@pytest.mark.integration  
class TestDocumentDeleteAPI:
    """Integration tests for document deletion endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_delete_existing_document(self, client):
        """Test deleting an existing document"""
        # First upload a document
        files = {"file": ("delete_me.txt", "Delete this content", "text/plain")}
        upload_response = client.post("/api/documents/upload", files=files)
        assert upload_response.status_code == 200
        
        document_id = upload_response.json()["document"]["id"]
        
        # Then delete it
        response = client.delete(f"/api/documents/{document_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Document deleted successfully"
    
    def test_delete_nonexistent_document(self, client):
        """Test deleting a document that doesn't exist"""
        response = client.delete("/api/documents/nonexistent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Document not found"
    
    @patch('modules.storage.DocumentStorage.delete_document')
    def test_delete_with_storage_error(self, mock_delete, client):
        """Test deletion when storage error occurs"""
        mock_delete.side_effect = Exception("Storage error")
        
        response = client.delete("/api/documents/test-id")
        
        assert response.status_code == 500


@pytest.mark.integration
class TestAPIErrorHandling:
    """Integration tests for API error handling"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_invalid_request_method(self, client):
        """Test invalid HTTP methods on endpoints"""
        # Try POST on list endpoint (should be GET)
        response = client.post("/api/documents")
        assert response.status_code == 405
        
        # Try GET on upload endpoint (should be POST)
        response = client.get("/api/documents/upload")
        assert response.status_code == 405
    
    def test_malformed_json_request(self, client):
        """Test handling of malformed JSON in requests"""
        # This would be for endpoints that accept JSON, if we add any
        pass  # Currently all endpoints use form data or path params
    
    def test_cors_headers(self, client):
        """Test that CORS headers are properly set"""
        response = client.options("/api/documents")
        
        # Check for CORS headers (should be set by middleware)
        assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()]
    
    def test_rate_limiting_headers(self, client):
        """Test for rate limiting headers if implemented"""
        response = client.get("/api/documents")
        
        # This would test rate limiting if implemented
        # For now, just ensure the endpoint responds
        assert response.status_code in [200, 500]  # Either success or server error


@pytest.mark.integration
class TestDocumentProcessingWorkflow:
    """Integration tests for complete document processing workflow"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_complete_workflow_text_file(self, client):
        """Test complete workflow: upload -> list -> delete"""
        # 1. Upload a document
        test_content = "This is a complete workflow test document."
        files = {"file": ("workflow.txt", test_content, "text/plain")}
        
        upload_response = client.post("/api/documents/upload", files=files)
        assert upload_response.status_code == 200
        
        upload_data = upload_response.json()
        document_id = upload_data["document"]["id"]
        assert upload_data["document"]["status"] == "processed"
        
        # 2. List documents and verify it's there
        list_response = client.get("/api/documents")
        assert list_response.status_code == 200
        
        list_data = list_response.json()
        uploaded_doc = next(
            (doc for doc in list_data["documents"] if doc["id"] == document_id),
            None
        )
        assert uploaded_doc is not None
        assert uploaded_doc["filename"] == "workflow.txt"
        
        # 3. Delete the document
        delete_response = client.delete(f"/api/documents/{document_id}")
        assert delete_response.status_code == 200
        
        # 4. Verify it's gone
        list_response2 = client.get("/api/documents")
        assert list_response2.status_code == 200
        
        list_data2 = list_response2.json()
        deleted_doc = next(
            (doc for doc in list_data2["documents"] if doc["id"] == document_id),
            None
        )
        assert deleted_doc is None
    
    def test_parallel_uploads(self, client):
        """Test handling multiple concurrent uploads"""
        import concurrent.futures
        import threading
        
        def upload_file(filename, content):
            files = {"file": (filename, content, "text/plain")}
            return client.post("/api/documents/upload", files=files)
        
        # Create multiple upload tasks
        upload_tasks = []
        for i in range(5):
            filename = f"parallel_{i}.txt"
            content = f"Content for parallel file {i}"
            upload_tasks.append((filename, content))
        
        # Execute uploads in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(upload_file, filename, content)
                for filename, content in upload_tasks
            ]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all uploads succeeded
        for response in responses:
            assert response.status_code == 200
            assert response.json()["status"] == "success"
    
    def test_storage_persistence(self, client):
        """Test that documents persist across application restarts"""
        # This would require actually restarting the app, which is complex
        # For now, we test that storage operations work correctly
        
        # Upload a document
        files = {"file": ("persist.txt", "Persistent content", "text/plain")}
        upload_response = client.post("/api/documents/upload", files=files)
        assert upload_response.status_code == 200
        
        document_id = upload_response.json()["document"]["id"]
        
        # Verify it can be retrieved
        list_response = client.get("/api/documents")
        assert list_response.status_code == 200
        
        documents = list_response.json()["documents"]
        found_doc = next((doc for doc in documents if doc["id"] == document_id), None)
        assert found_doc is not None
        assert found_doc["filename"] == "persist.txt"


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceAndLimits:
    """Integration tests for performance and system limits"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_large_file_upload_performance(self, client):
        """Test performance with large file uploads"""
        import time
        
        # Create a moderately large file (100KB)
        large_content = "x" * (100 * 1024)
        
        start_time = time.time()
        files = {"file": ("large_perf.txt", large_content, "text/plain")}
        response = client.post("/api/documents/upload", files=files)
        end_time = time.time()
        
        assert response.status_code == 200
        # Should complete within reasonable time (adjust as needed)
        assert (end_time - start_time) < 10.0  # 10 seconds max
    
    def test_many_small_files(self, client):
        """Test uploading many small files"""
        responses = []
        
        for i in range(20):  # Upload 20 small files
            files = {"file": (f"small_{i}.txt", f"Content {i}", "text/plain")}
            response = client.post("/api/documents/upload", files=files)
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
        
        # List should show all files
        list_response = client.get("/api/documents")
        assert list_response.status_code == 200
        
        documents = list_response.json()["documents"]
        small_files = [doc for doc in documents if doc["filename"].startswith("small_")]
        assert len(small_files) >= 20