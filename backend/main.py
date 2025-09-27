from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="DocuMind API",
    description="Privacy-first document processing API",
    version="0.1.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "DocuMind API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import os
import tempfile
import shutil
from modules.storage import document_storage
from modules.document_processor import DocumentProcessor

app = FastAPI(
    title="Document Processing API",
    description="API for document upload, processing, and search functionality",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server default
        "http://localhost:3000",  # Alternative port
        "http://localhost:3001",  # Current frontend port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent storage replaces in-memory storage
# documents_store: Dict[str, Dict[str, Any]] = {}

# Initialize document processor
doc_processor = DocumentProcessor()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Document Processing API is running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint for frontend"""
    return {"status": "healthy", "service": "document-processing-api"}

@app.post("/api/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload multiple documents"""
    uploaded_files = []
    
    for file in files:
        if not file.filename:
            continue
            
        # Create a temporary file to store the upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        # Store document metadata in persistent storage
        documents = document_storage.load_documents()
        doc_id = f"doc_{len(documents) + 1}"
        
        document_data = {
            "id": doc_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": os.path.getsize(temp_path),
            "temp_path": temp_path,
            "status": "processing"  # Start with processing status
        }
        
        document_storage.add_document(doc_id, document_data)
        
        # Process the document to extract text
        try:
            processing_result = doc_processor.process_document(temp_path)
            
            # Update document with processing results
            document_storage.update_document(doc_id, {
                "status": processing_result["status"],
                "text": processing_result.get("text", ""),
                "metadata": processing_result.get("metadata", {}),
                "chunks": processing_result.get("chunks", []),
                "error": processing_result.get("error")
            })
            
            final_status = processing_result["status"]
        except Exception as e:
            # If processing fails, mark as error but keep the file
            document_storage.update_document(doc_id, {
                "status": "error",
                "error": f"Processing failed: {str(e)}"
            })
            final_status = "error"
        
        uploaded_files.append({
            "id": doc_id,
            "filename": file.filename,
            "size": os.path.getsize(temp_path),
            "status": final_status
        })
    
    return {"message": f"Successfully uploaded {len(uploaded_files)} files", "files": uploaded_files}

@app.get("/api/documents")
async def list_documents():
    """Get list of all uploaded documents"""
    documents = document_storage.list_all_documents()
    return {"documents": documents}

@app.get("/api/documents/{doc_id}")
async def get_document_details(doc_id: str):
    """Get detailed information about a specific document"""
    doc = document_storage.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "document": doc
    }

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a specific document"""
    doc = document_storage.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Clean up temporary file
    if doc.get("temp_path") and os.path.exists(doc["temp_path"]):
        os.unlink(doc["temp_path"])
    
    # Remove from storage
    document_storage.remove_document(doc_id)
    return {"message": "Document deleted successfully"}

@app.post("/api/search")
async def search_documents(query: Dict[str, str]):
    """Search through documents (placeholder for RAG implementation)"""
    search_query = query.get("query", "")
    
    if not search_query:
        raise HTTPException(status_code=400, detail="Search query is required")
    
    # Placeholder search logic
    results = []
    documents = document_storage.load_documents()
    for doc_id, doc in documents.items():
        # Simple filename matching for demo
        if search_query.lower() in doc["filename"].lower():
            results.append({
                "document_id": doc_id,
                "filename": doc["filename"],
                "relevance_score": 0.8,
                "snippet": f"Found match in {doc['filename']}"
            })
    
    return {
        "query": search_query,
        "results": results,
        "total_results": len(results)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
@app.post("/documents/upload")
async def upload_document():
    return {"message": "Document upload endpoint - coming soon"}

@app.get("/documents")
async def list_documents():
    return {"documents": [], "message": "Document listing - coming soon"}