#!/usr/bin/env python3
"""
Test script for Document Processor
Demonstrates how the document processor extracts text, metadata, and creates chunks
"""

from modules.document_processor import DocumentProcessor
import json
from pathlib import Path

def test_document_processor():
    """Test the document processor with a sample file"""

    # Initialize the document processor
    processor = DocumentProcessor()

    # Test file path
    test_file = "test_document.txt"

    print("🧪 Testing Document Processor")
    print("=" * 50)

    # Check if file exists
    if not Path(test_file).exists():
        print(f"❌ Test file '{test_file}' not found!")
        return

    # Check if format is supported
    if not processor.is_supported(test_file):
        print(f"❌ File format not supported: {test_file}")
        return

    print(f"✅ Processing file: {test_file}")

    # Process the document
    result = processor.process_document(test_file)

    # Display results
    print(f"\n📊 Processing Status: {result['status']}")

    if result['status'] == 'processed':
        print("✅ Document processed successfully!")

        # Show metadata
        print("\n📋 Metadata:")
        for key, value in result['metadata'].items():
            print(f"  {key}: {value}")

        # Show text preview
        text = result['text']
        print("\n📄 Text Preview (first 200 chars):")
        print(f"  {text[:200]}{'...' if len(text) > 200 else ''}")

        # Show supported formats
        print(f"\n📁 Supported Formats: {', '.join(processor.get_supported_formats())}")

    else:
        print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 50)
    print("✅ Document Processor Test Complete!")

if __name__ == "__main__":
    test_document_processor()