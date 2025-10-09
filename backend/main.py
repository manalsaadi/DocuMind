from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import os
import tempfile
import shutil
from datetime import datetime
from modules.storage import document_storage
from modules.document_processor import DocumentProcessor
from modules.rag_pipeline import rag_pipeline, TextChunker

app = FastAPI(
    title="DocuMind API",
    description="Local RAG Document Processing API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server default
        "http://localhost:3000",  # Alternative port
        "http://localhost:3001",  # Another alternative port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG configuration
rag_config = {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "retrieve_k": 10,
    "rerank_k": 3,
    "llm_max_tokens": 256,
    "llm_temperature": 0.7,
    "llm_top_p": 0.9
}

# Initialize document processor
doc_processor = DocumentProcessor()

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "DocuMind API",
        "version": "1.0.0",
        "status": "running",
        "description": "Local RAG Document Processing API"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "DocuMind API",
        "version": "1.0.0"
    }

@app.get("/api/health")  
async def api_health_check():
    """Health check endpoint for frontend (API prefixed)"""
    return {
        "status": "healthy", 
        "service": "DocuMind API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload multiple documents"""
    if not files or (len(files) == 1 and not files[0].filename):
        raise HTTPException(status_code=400, detail="No files provided")
    
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
        doc_id = f"doc_{len(documents) + 1}_{int(datetime.now().timestamp())}"

        document_data = {
            "id": doc_id,
            "filename": file.filename,
            "originalName": file.filename,
            "size": os.path.getsize(temp_path),
            "mimeType": file.content_type or "application/octet-stream",
            "uploadedAt": datetime.now().isoformat(),
            "lastModified": datetime.now().isoformat(),
            "status": "processing",
            "filePath": temp_path
        }

        document_storage.add_document(doc_id, document_data)

        # Process the document to extract text, chunks, and embeddings
        try:
            processing_result = doc_processor.process_document(temp_path)

            # Update document with processing results
            document_storage.update_document(doc_id, {
                "status": processing_result["status"],
                "text": processing_result.get("text", ""),
                "metadata": processing_result.get("metadata", {}),
                "error": processing_result.get("error")
            })

            # Add to vector store if processing was successful and there are chunks/embeddings
            if (
                processing_result["status"] == "processed"
                and processing_result.get("chunks")
                and processing_result.get("embeddings") is not None
                and len(processing_result["chunks"]) == processing_result["embeddings"].shape[0]
                and processing_result["embeddings"].shape[0] > 0
            ):
                try:
                    # Add directly to vector store (bypassing chunking/embedding in RAGPipeline)
                    rag_pipeline.vector_store.add_chunks(
                        processing_result["chunks"],
                        processing_result["embeddings"],
                        doc_id
                    )
                    document_storage.update_document(doc_id, {"rag_indexed": True})
                except Exception as rag_error:
                    print(f"Warning: Failed to add document {doc_id} to vector store: {rag_error}")
                    document_storage.update_document(doc_id, {"rag_indexed": False, "rag_error": str(rag_error)})

            final_status = processing_result["status"]
        except Exception as e:
            # If processing fails, mark as error but keep the file
            document_storage.update_document(doc_id, {
                "status": "error",
                "error": f"Processing failed: {str(e)}"
            })
            final_status = "error"

        # Get the updated document for response
        final_doc = document_storage.get_document(doc_id)
        uploaded_files.append(final_doc)
    
    # For single file uploads, return single document format
    if len(uploaded_files) == 1:
        return {
            "status": "success",
            "document": uploaded_files[0]
        }
    
    # For multiple files, return array format
    return {
        "status": "success", 
        "documents": uploaded_files,
        "message": f"Successfully uploaded {len(uploaded_files)} files"
    }

@app.get("/api/documents")
async def list_documents():
    """Get list of all uploaded documents"""
    try:
        documents = document_storage.list_all_documents()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")

@app.get("/api/documents/{doc_id}")
async def get_document_details(doc_id: str):
    """Get detailed information about a specific document"""
    try:
        doc = document_storage.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"document": doc}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a specific document"""
    try:
        doc = document_storage.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Clean up temporary file
        if doc.get("filePath") and os.path.exists(doc["filePath"]):
            os.unlink(doc["filePath"])
        elif doc.get("temp_path") and os.path.exists(doc["temp_path"]):
            os.unlink(doc["temp_path"])
        
        # Remove from RAG pipeline
        try:
            rag_pipeline.remove_document(doc_id)
        except Exception as rag_error:
            print(f"Warning: Failed to remove document {doc_id} from RAG pipeline: {rag_error}")
        
        # Remove from storage
        success = document_storage.remove_document(doc_id)
        if success:
            return {"status": "success", "message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete document")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.get("/api/rag/config")
async def get_rag_config():
    """Get current RAG pipeline configuration"""
    return {
        "config": rag_config,
        "description": {
            "chunk_size": "Maximum characters per text chunk (default: 1000)",
            "chunk_overlap": "Characters to overlap between chunks (default: 200)",
            "retrieve_k": "Number of chunks to retrieve initially (default: 10)",
            "rerank_k": "Number of chunks to rerank and use for generation (default: 3)",
            "llm_max_tokens": "Maximum tokens for LLM response (default: 256)",
            "llm_temperature": "LLM creativity/randomness (0.0-1.0, default: 0.7)",
            "llm_top_p": "LLM nucleus sampling parameter (0.0-1.0, default: 0.9)"
        }
    }

@app.put("/api/rag/config")
async def update_rag_config(config: Dict[str, Any]):
    """Update RAG pipeline configuration"""
    global rag_config
    
    # Validate configuration parameters
    valid_keys = {
        "chunk_size": int,
        "chunk_overlap": int,
        "retrieve_k": int,
        "rerank_k": int,
        "llm_max_tokens": int,
        "llm_temperature": float,
        "llm_top_p": float
    }
    
    updated_config = rag_config.copy()
    
    for key, value in config.items():
        if key in valid_keys:
            expected_type = valid_keys[key]
            if isinstance(value, expected_type):
                # Additional validation
                if key in ["chunk_size", "chunk_overlap", "retrieve_k", "rerank_k", "llm_max_tokens"]:
                    if value <= 0:
                        raise HTTPException(status_code=400, detail=f"{key} must be positive")
                elif key in ["llm_temperature", "llm_top_p"]:
                    if not (0.0 <= value <= 1.0):
                        raise HTTPException(status_code=400, detail=f"{key} must be between 0.0 and 1.0")
                
                updated_config[key] = value
            else:
                raise HTTPException(status_code=400, detail=f"{key} must be of type {expected_type.__name__}")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown configuration key: {key}")
    
    rag_config = updated_config
    return {
        "status": "success",
        "message": "RAG configuration updated",
        "config": rag_config
    }

@app.post("/api/rag/reset")
async def reset_rag_pipeline():
    """Reset RAG pipeline with current configuration"""
    try:
        # Reinitialize the global RAG pipeline with new configuration
        global rag_pipeline
        rag_pipeline = None  # Clear current instance
        
        # Import and create new instance with current config
        from modules.rag_pipeline import RAGPipeline
        rag_pipeline = RAGPipeline(rag_config)
        
        return {
            "status": "success",
            "message": "RAG pipeline reset with new configuration",
            "config": rag_config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset RAG pipeline: {str(e)}")

@app.post("/api/search")
async def search_documents(query: Dict[str, str]):
    """Search through documents using RAG pipeline"""
    search_query = query.get("query", "")
    print(f"[SEARCH] Received query: '{search_query}'")
    
    if not search_query:
        raise HTTPException(status_code=400, detail="Search query is required")
    

    try:
        # Use RAG pipeline for semantic search with configurable parameters
        print(f"[SEARCH] Attempting RAG search...")
        rag_result = rag_pipeline.query(
            search_query,
            retrieve_k=rag_config["retrieve_k"],
            rerank_k=rag_config["rerank_k"]
        )
        print(f"[SEARCH] RAG result: {rag_result}")
        # Always return the LLM answer, even if no chunks are found
        results = []
        if rag_result and 'reranked_chunks' in rag_result:
            for i, chunk in enumerate(rag_result['reranked_chunks']):
                doc_id = chunk.get('doc_id')
                filename = f"Document {doc_id}"
                results.append({
                    "document_id": doc_id,
                    "filename": filename,
                    "relevance_score": chunk.get('rerank_score', chunk.get('score', 0)),
                    "snippet": chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text'],
                    "chunk_text": chunk['text']
                })
        print(f"[SEARCH] Returning LLM answer regardless of chunk count")
        return {
            "query": search_query,
            "answer": rag_result.get('answer', 'No answer generated.'),
            "results": results,
            "total_results": len(results),
            "pipeline_used": True,
            "config_used": rag_config.copy()
        }
    except Exception as e:
        print(f"[ERROR] RAG search failed: {e}")
        print(f"[ERROR] Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"RAG search failed: {str(e)}")
    

if __name__ == "__main__":
    import uvicorn
    print("Starting DocuMind API server...")
    print("API Documentation available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)