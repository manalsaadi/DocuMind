"""
Test fixtures and utilities for DocuMind testing
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
import json
from io import BytesIO

from main import app
from modules.storage import DocumentStorage
from modules.document_processor import DocumentProcessor


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_text_content() -> str:
    """Sample text content for testing"""
    return """This is a sample document for testing purposes.
    
It contains multiple paragraphs with different content.
The document includes various formatting and structures.

This helps us test text extraction and processing capabilities.
We can verify that our document processor handles text correctly."""


@pytest.fixture
def sample_txt_file(temp_dir: Path, sample_text_content: str) -> Path:
    """Create a sample TXT file for testing"""
    txt_file = temp_dir / "sample.txt"
    txt_file.write_text(sample_text_content, encoding='utf-8')
    return txt_file


@pytest.fixture
def sample_pdf_file(temp_dir: Path) -> Path:
    """Create a simple PDF file for testing"""
    pdf_file = temp_dir / "sample.pdf"
    
    # Create a minimal PDF using reportlab if available, otherwise create a dummy file
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(str(pdf_file), pagesize=letter)
        c.drawString(100, 750, "Sample PDF Document")
        c.drawString(100, 730, "This is a test PDF for document processing.")
        c.drawString(100, 710, "It contains sample text for extraction testing.")
        c.save()
    except ImportError:
        # Fallback: create a dummy PDF file (won't be readable but will test file handling)
        pdf_file.write_bytes(b"%PDF-1.4\n%EOF\n")  # Minimal PDF structure
    
    return pdf_file


@pytest.fixture
def sample_docx_file(temp_dir: Path) -> Path:
    """Create a sample DOCX file for testing"""
    docx_file = temp_dir / "sample.docx"
    
    try:
        from docx import Document
        
        doc = Document()
        doc.add_heading('Sample DOCX Document', 0)
        doc.add_paragraph('This is a test DOCX file for document processing.')
        doc.add_paragraph('It contains sample text for extraction testing.')
        doc.add_paragraph('We use this to verify DOCX processing capabilities.')
        doc.save(str(docx_file))
    except ImportError:
        # Create a dummy file if python-docx is not available
        docx_file.write_bytes(b"PK\x03\x04")  # ZIP file signature (DOCX is a ZIP)
    
    return docx_file


@pytest.fixture
def unsupported_file(temp_dir: Path) -> Path:
    """Create an unsupported file type for testing"""
    unsupported_file = temp_dir / "sample.unknown"
    unsupported_file.write_text("This is an unsupported file type.")
    return unsupported_file


@pytest.fixture
def document_storage(temp_dir: Path) -> DocumentStorage:
    """Create a DocumentStorage instance for testing"""
    storage_file = temp_dir / "test_documents.json"
    return DocumentStorage(str(storage_file))


@pytest.fixture
def document_processor() -> DocumentProcessor:
    """Create a DocumentProcessor instance for testing"""
    return DocumentProcessor()


@pytest.fixture
def test_client() -> TestClient:
    """Create a FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def sample_document_metadata() -> Dict[str, Any]:
    """Sample document metadata for testing"""
    return {
        "id": "test-doc-123",
        "filename": "sample.txt",
        "originalName": "sample.txt",
        "size": 1024,
        "mimeType": "text/plain",
        "uploadedAt": "2025-09-27T12:00:00Z",
        "lastModified": "2025-09-27T12:00:00Z",
        "status": "pending",
        "filePath": "/tmp/sample.txt"
    }


@pytest.fixture
def sample_upload_file():
    """Create a sample upload file for API testing"""
    from io import BytesIO
    from fastapi import UploadFile
    
    content = b"This is a sample file content for testing uploads."
    file_obj = BytesIO(content)
    return UploadFile(filename="test.txt", file=file_obj, content_type="text/plain")


# Test data constants
SAMPLE_DOCUMENTS = [
    {
        "filename": "doc1.txt",
        "content": "First sample document content.",
        "type": "text/plain"
    },
    {
        "filename": "doc2.pdf", 
        "content": "Second sample document content.",
        "type": "application/pdf"
    },
    {
        "filename": "doc3.docx",
        "content": "Third sample document content.", 
        "type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
]


class TestDataBuilder:
    """Helper class for building test data"""
    
    @staticmethod
    def create_document_dict(
        filename: str = "test.txt",
        status: str = "pending",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a document dictionary with default values"""
        base_doc = {
            "id": f"test-{filename.replace('.', '-')}",
            "filename": filename,
            "originalName": filename,
            "size": 1024,
            "mimeType": "text/plain",
            "uploadedAt": "2025-09-27T12:00:00Z",
            "lastModified": "2025-09-27T12:00:00Z",
            "status": status,
            "filePath": f"/tmp/{filename}"
        }
        base_doc.update(kwargs)
        return base_doc
    
    @staticmethod
    def create_processed_document(filename: str = "test.txt") -> Dict[str, Any]:
        """Create a processed document with text and metadata"""
        doc = TestDataBuilder.create_document_dict(filename, status="processed")
        doc.update({
            "text": "Sample extracted text content.",
            "metadata": {
                "format": "text",
                "pages": 1,
                "characters": 30,
                "file_size": 1024
            },
            "chunks": [
                {
                    "text": "Sample extracted text content.",
                    "length": 30,
                    "metadata": {"format": "text"}
                }
            ]
        })
        return doc


# Mock classes for testing
class MockUploadFile:
    """Mock UploadFile for testing"""
    
    def __init__(self, filename: str, content: bytes, content_type: str = "text/plain"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self.file = BytesIO(content)
    
    async def read(self) -> bytes:
        return self.content
    
    async def write(self, data: bytes):
        pass


class MockDocumentLoader:
    """Mock document loader for testing"""
    
    def __init__(self, should_succeed: bool = True):
        self.should_succeed = should_succeed
    
    def can_process(self, file_path: str, mime_type: str) -> bool:
        return True
    
    def extract_text(self, file_path: str) -> str:
        if not self.should_succeed:
            raise Exception("Mock processing error")
        return "Mock extracted text"
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        if not self.should_succeed:
            raise Exception("Mock metadata error") 
        return {
            "format": "mock",
            "pages": 1,
            "characters": 17,
            "file_size": 100
        }