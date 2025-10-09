"""
Unit tests for DocumentProcessor module
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from io import BytesIO

# Import the classes being tested
from modules.document_processor import (
    PlainTextLoader, 
    PDFLoader, 
    DOCXLoader, 
    TextChunker, 
    DocumentProcessor
)


@pytest.mark.unit
class TestPlainTextLoader:
    """Test PlainTextLoader class"""
    
    def test_can_process_text_files(self):
        """Test that PlainTextLoader can process .txt files"""
        loader = PlainTextLoader()
        assert loader.can_process("test.txt", "text/plain")
        assert loader.can_process("document.TXT", "text/plain")  # Case insensitive
        assert not loader.can_process("test.pdf", "application/pdf")
        assert not loader.can_process("test.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    
    @patch("builtins.open", mock_open(read_data="Hello, world!"))
    def test_extract_text_utf8(self):
        """Test text extraction with UTF-8 encoding"""
        loader = PlainTextLoader()
        text = loader.extract_text("test.txt")
        assert text == "Hello, world!"
    
    @patch("builtins.open")
    def test_extract_text_encoding_fallback(self, mock_file):
        """Test encoding fallback when UTF-8 fails"""
        # First call raises UnicodeDecodeError, second succeeds
        mock_file.side_effect = [
            UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte"),
            mock_open(read_data="Fallback text").return_value
        ]
        
        loader = PlainTextLoader()
        text = loader.extract_text("test.txt")
        assert "Fallback text" in text
    
    @patch("builtins.open", mock_open(read_data="Sample content"))
    @patch('pathlib.Path.stat')
    def test_extract_metadata(self, mock_stat):
        """Test metadata extraction"""
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 100
        mock_stat.return_value = mock_stat_result
        
        loader = PlainTextLoader()
        metadata = loader.extract_metadata("test.txt")
        
        assert metadata["format"] == "text"
        assert metadata["characters"] == len("Sample content")
        assert metadata["file_size"] == 100


@pytest.mark.unit
class TestPDFLoader:
    """Test PDFLoader class"""
    
    def test_can_process_pdf_files(self):
        """Test that PDFLoader can process .pdf files"""
        loader = PDFLoader()
        assert loader.can_process("test.pdf", "application/pdf")
        assert loader.can_process("document.PDF", "application/pdf")  # Case insensitive
        assert not loader.can_process("test.txt", "text/plain")
        assert not loader.can_process("test.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    
    @patch('pdfplumber.open')
    def test_extract_text_with_pdfplumber(self, mock_pdfplumber):
        """Test PDF text extraction using pdfplumber"""
        # Mock PDF with two pages
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page content"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page, mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdfplumber.return_value = mock_pdf
        
        loader = PDFLoader()
        text = loader.extract_text("test.pdf")
        
        assert "Page content" in text
        mock_pdfplumber.assert_called_once_with("test.pdf")
    
    def test_extract_text_fallback_message(self, temp_dir):
        """Test fallback message when PDF libraries are unavailable"""
        pdf_file = temp_dir / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\nHello PDF\n%EOF")
        
        # Mock ImportError for pdfplumber
        with patch('pdfplumber.open', side_effect=ImportError):
            loader = PDFLoader()
            text = loader.extract_text(str(pdf_file))
            
            assert "[PDF text extraction unavailable" in text
            assert str(pdf_file) in text
    
    @patch('pdfplumber.open')
    @patch('pathlib.Path.stat')
    def test_extract_metadata_with_pdfplumber(self, mock_stat, mock_pdfplumber):
        """Test PDF metadata extraction"""
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock(), MagicMock()]  # 2 pages
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdfplumber.return_value = mock_pdf
        
        # Mock file size
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1024
        mock_stat.return_value = mock_stat_result
        
        loader = PDFLoader()
        # Mock the extract_text call for character count
        with patch.object(loader, 'extract_text', return_value="Sample text"):
            metadata = loader.extract_metadata("test.pdf")
        
        assert metadata["format"] == "pdf"
        assert metadata["pages"] == 2
        assert metadata["characters"] == len("Sample text")
        assert metadata["file_size"] == 1024


@pytest.mark.unit
class TestDOCXLoader:
    """Test DOCXLoader class"""
    
    def test_can_process_docx_files(self):
        """Test that DOCXLoader can process .docx files"""
        loader = DOCXLoader()
        assert loader.can_process("test.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        assert loader.can_process("document.DOCX", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")  # Case insensitive
        assert not loader.can_process("test.txt", "text/plain")
        assert not loader.can_process("test.pdf", "application/pdf")
    
    @patch('docx.Document')
    def test_extract_text_with_python_docx(self, mock_document_class):
        """Test DOCX text extraction using python-docx"""
        # Mock document with paragraphs
        mock_paragraph = MagicMock()
        mock_paragraph.text = "Paragraph content"
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_paragraph, mock_paragraph]
        mock_document_class.return_value = mock_doc
        
        loader = DOCXLoader()
        text = loader.extract_text("test.docx")
        
        assert "Paragraph content" in text
        mock_document_class.assert_called_once_with("test.docx")
    
    def test_extract_text_fallback_message(self):
        """Test fallback message when python-docx is unavailable"""
        with patch('docx.Document', side_effect=ImportError):
            loader = DOCXLoader()
            text = loader.extract_text("test.docx")
            
            assert "[DOCX text extraction unavailable" in text
            assert "test.docx" in text
    
    @patch('docx.Document')
    @patch('pathlib.Path.stat')
    def test_extract_metadata_with_python_docx(self, mock_stat, mock_document_class):
        """Test DOCX metadata extraction"""
        mock_doc = MagicMock()
        mock_doc.paragraphs = [MagicMock(), MagicMock(), MagicMock()]  # 3 paragraphs
        mock_document_class.return_value = mock_doc
        
        # Mock file size
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 2048
        mock_stat.return_value = mock_stat_result
        
        loader = DOCXLoader()
        # Mock the extract_text call for character count
        with patch.object(loader, 'extract_text', return_value="Sample docx text"):
            metadata = loader.extract_metadata("test.docx")
        
        assert metadata["format"] == "docx"
        assert metadata["paragraphs"] == 3
        assert metadata["characters"] == len("Sample docx text")
        assert metadata["file_size"] == 2048


@pytest.mark.unit
class TestTextChunker:
    """Test TextChunker class"""
    
    def test_init_default_parameters(self):
        """Test TextChunker initialization with default parameters"""
        chunker = TextChunker()
        assert chunker.chunk_size == 1000
        assert chunker.overlap == 200
    
    def test_init_custom_parameters(self):
        """Test TextChunker initialization with custom parameters"""
        chunker = TextChunker(chunk_size=500, overlap=100)
        assert chunker.chunk_size == 500
        assert chunker.overlap == 100
    
    def test_chunk_empty_text(self):
        """Test chunking empty text"""
        chunker = TextChunker()
        chunks = chunker.chunk_text("", {"source": "test.txt"})
        assert len(chunks) == 0
    
    def test_chunk_short_text(self):
        """Test chunking text shorter than chunk size"""
        chunker = TextChunker(chunk_size=100)
        text = "Short text"
        chunks = chunker.chunk_text(text, {"source": "test.txt"})
        
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
        assert chunks[0]["metadata"]["source"] == "test.txt"
    
    def test_chunk_long_text(self):
        """Test chunking text longer than chunk size"""
        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "A" * 100  # 100 characters
        chunks = chunker.chunk_text(text, {"source": "test.txt"})
        
        assert len(chunks) > 1
        # First chunk should be close to chunk_size
        assert len(chunks[0]["text"]) <= 50
        # Check overlap exists between chunks
        if len(chunks) > 1:
            assert chunks[0]["text"][-10:] == chunks[1]["text"][:10]
    
    def test_chunk_with_metadata(self):
        """Test that metadata is preserved in chunks"""
        chunker = TextChunker(chunk_size=50)
        text = "Sample text for chunking"
        metadata = {"source": "test.txt", "author": "Test Author"}
        chunks = chunker.chunk_text(text, metadata)
        
        assert len(chunks) == 1
        assert chunks[0]["metadata"]["source"] == "test.txt"
        assert chunks[0]["metadata"]["author"] == "Test Author"
    
    def test_overlap_functionality(self):
        """Test that overlap works correctly between chunks"""
        chunker = TextChunker(chunk_size=20, overlap=5)
        text = "This is a test sentence that will be chunked with overlap functionality."
        chunks = chunker.chunk_text(text, {"source": "test"})
        
        # Should have multiple chunks due to length
        assert len(chunks) > 1
        
        # Check that consecutive chunks have overlapping text
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]["text"]
            next_chunk = chunks[i + 1]["text"]
            
            # Find overlap (last part of current should match start of next)
            overlap_found = False
            for j in range(1, min(6, len(current_chunk), len(next_chunk))):  # Check up to 5 chars
                if current_chunk[-j:] == next_chunk[:j]:
                    overlap_found = True
                    break
            assert overlap_found, f"No overlap found between chunks {i} and {i+1}"


@pytest.mark.unit
class TestDocumentProcessor:
    """Test DocumentProcessor class"""
    
    def test_init_creates_loaders_and_chunker(self):
        """Test that DocumentProcessor initializes with all loaders and chunker"""
        processor = DocumentProcessor()
        
        assert len(processor.loaders) == 3  # txt, pdf, docx loaders
        # Note: chunker removed from DocumentProcessor as chunking is now handled by RAG pipeline
    
    def test_get_loader_for_text_file(self):
        """Test getting loader for text files"""
        processor = DocumentProcessor()
        loader = processor.get_loader_for_file("test.txt")
        assert isinstance(loader, PlainTextLoader)
    
    def test_get_loader_for_pdf_file(self):
        """Test getting loader for PDF files"""
        processor = DocumentProcessor()
        loader = processor.get_loader_for_file("test.pdf")
        assert isinstance(loader, PDFLoader)
    
    def test_get_loader_for_docx_file(self):
        """Test getting loader for DOCX files"""
        processor = DocumentProcessor()
        loader = processor.get_loader_for_file("test.docx")
        assert isinstance(loader, DOCXLoader)
    
    def test_get_loader_for_unsupported_file(self):
        """Test getting loader for unsupported file type"""
        processor = DocumentProcessor()
        loader = processor.get_loader_for_file("test.xyz")
        assert loader is None
    
    @patch("builtins.open", mock_open(read_data="Test content"))
    @patch('pathlib.Path.stat')
    def test_process_document_success(self, mock_stat):
        """Test successful document processing"""
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 100
        mock_stat.return_value = mock_stat_result
        
        processor = DocumentProcessor()
        result = processor.process_document("test.txt")
        
        assert result["status"] == "processed"
        assert "text" in result
        assert "metadata" in result
        assert result["text"] == "Test content"
    
    def test_process_unsupported_document(self):
        """Test processing unsupported document type"""
        processor = DocumentProcessor()
        result = processor.process_document("test.xyz")
        
        assert result["status"] == "unsupported"
        assert "error" in result
        assert "Unsupported file type" in result["error"]
    
    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_process_document_with_error(self, mock_open):
        """Test document processing with file error"""
        processor = DocumentProcessor()
        result = processor.process_document("nonexistent.txt")
        
        assert result["status"] == "error"
        assert "error" in result
    
    def test_get_supported_formats(self):
        """Test getting supported file formats"""
        processor = DocumentProcessor()
        formats = processor.get_supported_formats()
        
        assert ".txt" in formats
        assert ".pdf" in formats
        assert ".docx" in formats
        assert len(formats) >= 3
    
    def test_is_supported_true(self):
        """Test is_supported returns True for supported formats"""
        processor = DocumentProcessor()
        assert processor.is_supported("test.txt")
        assert processor.is_supported("test.pdf")
        assert processor.is_supported("test.docx")
        assert processor.is_supported("TEST.TXT")  # Case insensitive
    
    def test_is_supported_false(self):
        """Test is_supported returns False for unsupported formats"""
        processor = DocumentProcessor()
        assert not processor.is_supported("test.xyz")
        assert not processor.is_supported("test.doc")
        assert not processor.is_supported("test")  # No extension
    
    @patch("builtins.open", mock_open(read_data="Test content"))
    @patch('pathlib.Path.stat')
    def test_process_document_with_different_content(self, mock_stat):
        """Test processing document with different content"""
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 100
        mock_stat.return_value = mock_stat_result
        
        processor = DocumentProcessor()
        result = processor.process_document("test.txt")
        
        assert result["status"] == "processed"
        assert result["text"] == "Test content"
    
    @patch("builtins.open", mock_open(read_data="Content 1"))
    @patch('pathlib.Path.stat')
    def test_process_multiple_documents(self, mock_stat):
        """Test processing multiple documents"""
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 100
        mock_stat.return_value = mock_stat_result
        
        processor = DocumentProcessor()
        files = ["test1.txt", "test2.txt"]
        results = []
        
        for file in files:
            result = processor.process_document(file)
            results.append(result)
        
        assert len(results) == 2
        assert all(r["status"] == "processed" for r in results)