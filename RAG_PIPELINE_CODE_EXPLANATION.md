# DocuMind RAG Pipeline Code Explanation

## Overview
This document provides a line-by-line explanation of the RAG pipeline implementation in `rag_pipeline.py`, including design decisions, technical choices, and rationale.

## Module Header & Imports

```python
"""
RAG Pipeline Module for DocuMind

Implements the complete Retrieval-Augmented Generation pipeline:
1. Document chunking
2. Embedding generation using sentence-transformers
3. Vector storage using FAISS
4. Semantic search and retrieval
5. Reranking using cross-encoder
6. LLM generation using local TinyLlama
"""
```

**Decision**: Comprehensive docstring explaining the complete pipeline. This helps developers understand the full scope and ensures the module serves as the single source of truth for RAG functionality.

```python
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss
import json
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer, CrossEncoder
import threading
from datetime import datetime
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None
```

**Decisions**:
- **Type hints**: Using `typing` for better code maintainability and IDE support
- **Optional imports**: `llama_cpp` wrapped in try/except to gracefully handle missing dependencies
- **Threading**: Imported for thread-safe vector store operations
- **Path operations**: Using `pathlib.Path` for modern, cross-platform file handling

## TextChunker Class

```python
class TextChunker:
    """Handles semantic text splitting for RAG processing"""
```

**Decision**: Separate class for text chunking to keep concerns separated and allow for future enhancements (semantic chunking, different strategies).

```python
def __init__(self, chunk_size: int = 1000, overlap: int = 200):
    self.chunk_size = chunk_size
    self.overlap = overlap
```

**Decisions**:
- **chunk_size=1000**: Balances context preservation with embedding efficiency. Too small loses context, too large reduces granularity.
- **overlap=200**: 20% overlap ensures continuity between chunks and prevents information loss at boundaries.

```python
def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Split text into semantic chunks for RAG processing"""
    if not text.strip():
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + self.chunk_size
        if end > len(text):
            end = len(text)
        
        chunk_text = text[start:end]
        
        # Add chunk to the list
        chunks.append({
            "text": chunk_text,
            "length": len(chunk_text),
            "metadata": metadata or {}
        })
        
        # Move start position for the next chunk
        start += self.chunk_size - self.overlap
        if start >= len(text):
            break

    return chunks
```

**Decisions**:
- **Simple sliding window**: Chose fixed-size chunks over more complex semantic splitting for simplicity and predictability
- **Metadata preservation**: Each chunk carries document metadata for traceability
- **Overlap calculation**: `start += chunk_size - overlap` ensures proper sliding window progression

## VectorStore Class

```python
class VectorStore:
    """FAISS-based vector store for document embeddings"""
```

**Decision**: Dedicated vector store class to encapsulate FAISS operations, persistence, and thread safety.

```python
def __init__(self, dimension: int = 384, index_file: str = "vector_index.faiss"):
    self.dimension = dimension
    self.index_file = Path(index_file)
    self.index = None
    self.chunks = []  # Store chunk metadata
    self.doc_mapping = {}  # Map chunk indices to document IDs
    self._lock = threading.RLock()
    self._load_or_create_index()
```

**Decisions**:
- **dimension=384**: Matches sentence-transformers/all-MiniLM-L6-v2 output dimension
- **Dual storage**: FAISS for vectors, JSON for metadata (FAISS doesn't store text)
- **RLock**: Reentrant lock allows same thread to acquire multiple times, safer for complex operations

```python
def _load_or_create_index(self):
    """Load existing index or create new one"""
    if self.index_file.exists():
        try:
            self.index = faiss.read_index(str(self.index_file))
            # Load chunk metadata
            metadata_file = self.index_file.with_suffix('.json')
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    self.chunks = data.get('chunks', [])
                    self.doc_mapping = data.get('doc_mapping', {})
        except Exception as e:
            print(f"Warning: Could not load existing index: {e}")
            self._create_new_index()
    else:
        self._create_new_index()
```

**Decision**: Robust persistence with error handling. If index loading fails, recreate rather than crash.

```python
def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray, doc_id: str):
    """Add document chunks and their embeddings to the vector store"""
    with self._lock:
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension {embeddings.shape[1]} doesn't match index dimension {self.dimension}")
        
        start_idx = len(self.chunks)
        self.index.add(embeddings)
        
        # Add chunk metadata
        for i, chunk in enumerate(chunks):
            chunk_info = {
                'text': chunk['text'],
                'doc_id': doc_id,
                'chunk_idx': i,
                'metadata': chunk.get('metadata', {})
            }
            self.chunks.append(chunk_info)
            self.doc_mapping[start_idx + i] = doc_id
        
        self._save_index()
```

**Decisions**:
- **Thread safety**: All operations locked to prevent race conditions
- **Validation**: Check embedding dimensions to catch configuration mismatches
- **Metadata tracking**: Store chunk index within document for potential reordering needs

```python
def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
    """Search for similar chunks using vector similarity"""
    with self._lock:
        if self.index.ntotal == 0:
            return []
        
        # Ensure query_embedding is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1:  # Valid result
                chunk_info = self.chunks[idx]
                results.append((chunk_info, float(dist)))
        
        return results
```

**Decisions**:
- **2D reshaping**: FAISS expects batched inputs, ensures compatibility
- **min(top_k, ntotal)**: Prevents requesting more results than available
- **Distance conversion**: Convert numpy float32 to Python float for JSON serialization

## RAGPipeline Class

```python
class RAGPipeline:
    """Complete RAG pipeline orchestrator"""
```

**Decision**: Main orchestrator class that coordinates all RAG components.

```python
def __init__(self):
    # Initialize models
    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    try:
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    except Exception as e:
        print(f"Warning: Could not load reranker: {e}")
        self.reranker = None
    
    # Initialize text chunker
    self.chunker = TextChunker()
    
    # Initialize vector store
    self.vector_store = VectorStore(dimension=self.embedding_model.get_sentence_embedding_dimension())
    
    # Initialize LLM
    self.llm_model = self._initialize_llm()
```

**Decisions**:
- **Graceful degradation**: Models load with error handling, system continues with reduced functionality
- **Dynamic dimension**: Vector store dimension matches embedding model output
- **Component separation**: Each component is independently initializable

### LLM Initialization

```python
def _initialize_llm(self):
    """Initialize local LLM for generation"""
    if Llama is None:
        print("Warning: llama-cpp-python not installed. LLM generation will be limited.")
        return None
    
    try:
        # Try to load TinyLlama model
        model_path = os.path.join(os.path.dirname(__file__), "..", "models", "tinyllama-1.1b-chat.gguf")
        if not os.path.exists(model_path):
            # Try common locations or download
            model_path = self._find_or_download_model()
        
        if model_path and os.path.exists(model_path):
            llm = Llama(
                model_path=model_path,
                n_ctx=2048,  # Context window
                n_threads=4,  # Number of CPU threads
                verbose=False
            )
            print("Successfully loaded TinyLlama model for generation")
            return llm
        else:
            print("Warning: TinyLlama model not found. Using fallback generation.")
            return None
    except Exception as e:
        print(f"Warning: Could not initialize LLM: {e}")
        return None
```

**Decisions**:
- **n_ctx=2048**: Sufficient for document Q&A while staying within model limits
- **n_threads=4**: Balances CPU usage with responsiveness
- **verbose=False**: Reduces log noise during operation
- **Multiple path checks**: Flexible model discovery

### Core Pipeline Methods

```python
def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None):
    """Add a document to the RAG pipeline (includes chunking)"""
    if not text.strip():
        return
    
    # Chunk the text
    chunks = self.chunk_text(text, metadata)
    if not chunks:
        return
    
    # Generate embeddings
    embeddings = self.embed_chunks(chunks)
    
    # Add to vector store
    self.vector_store.add_chunks(chunks, embeddings, doc_id)
```

**Decision**: Single method that handles the complete ingestion pipeline (chunk → embed → store).

```python
def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Retrieve relevant chunks for a query"""
    # Generate query embedding
    query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)[0]
    
    # Search vector store
    search_results = self.vector_store.search(query_embedding, top_k=top_k)
    
    # Convert to dict format
    retrieved_chunks = []
    for chunk_info, distance in search_results:
        retrieved_chunks.append({
            'text': chunk_info['text'],
            'doc_id': chunk_info['doc_id'],
            'score': distance,
            'metadata': chunk_info.get('metadata', {})
        })
    
    return retrieved_chunks
```

**Decision**: Clean separation between vector search and result formatting.

```python
def rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
    """Rerank retrieved chunks using cross-encoder"""
    if not self.reranker or not chunks:
        return chunks[:top_k]
    
    # Prepare pairs for reranking
    pairs = [(query, chunk['text']) for chunk in chunks]
    
    # Get reranking scores
    scores = self.reranker.predict(pairs)
    
    # Sort by score (higher is better for cross-encoder)
    reranked = []
    for chunk, score in sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True):
        chunk_copy = chunk.copy()
        chunk_copy['rerank_score'] = float(score)
        reranked.append(chunk_copy)
    
    return reranked[:top_k]
```

**Decisions**:
- **Fallback behavior**: If reranker unavailable, return top chunks unchanged
- **Score preservation**: Add rerank_score to chunk metadata for transparency
- **Top-k limiting**: Ensure only requested number of results returned

### LLM Generation

```python
def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """Generate answer using retrieved context and local LLM"""
    if not context_chunks:
        return "No relevant information found in the documents."
    
    # Combine context from top chunks
    context = "\n\n".join([chunk['text'] for chunk in context_chunks[:3]])  # Use top 3 chunks
    
    if self.llm_model:
        try:
            # Create prompt for the LLM
            prompt = f"""You are a helpful assistant that answers questions based on the provided context. 
If the context doesn't contain enough information to answer the question, say so clearly.

Context:
{context}

Question: {query}

Answer:"""
            
            # Generate response using TinyLlama
            response = self.llm_model(
                prompt,
                max_tokens=256,
                temperature=0.7,
                top_p=0.9,
                stop=["Question:", "\n\n"],
                echo=False
            )
            
            if response and 'choices' in response and len(response['choices']) > 0:
                answer = response['choices'][0]['text'].strip()
                if answer:
                    return answer
            
        except Exception as e:
            print(f"LLM generation failed: {e}")
    
    # Fallback: Simple extractive answer
    return f"Based on the retrieved information:\n\n{context[:500]}{'...' if len(context) > 500 else ''}"
```

**Decisions**:
- **Context limiting**: Use only top 3 chunks to stay within model context limits
- **Structured prompting**: Clear instructions for the LLM
- **Parameter tuning**: temperature=0.7 for creativity, top_p=0.9 for coherence
- **Robust fallback**: Extractive answer if LLM fails
- **Error handling**: Graceful degradation with logging

### Main Query Method

```python
def query(self, query: str, retrieve_k: int = 10, rerank_k: int = 3) -> Dict[str, Any]:
    """Complete RAG query pipeline"""
    # 1. Retrieve
    retrieved = self.retrieve(query, top_k=retrieve_k)
    
    # 2. Rerank
    reranked = self.rerank(query, retrieved, top_k=rerank_k)
    
    # 3. Generate answer
    answer = self.generate_answer(query, reranked)
    
    return {
        'query': query,
        'answer': answer,
        'retrieved_chunks': retrieved,
        'reranked_chunks': reranked,
        'pipeline_steps': ['retrieve', 'rerank', 'generate']
    }
```

**Decisions**:
- **Configurable parameters**: Allow tuning retrieval vs reranking depth
- **Complete pipeline**: Single method for end-to-end RAG
- **Rich response**: Return all intermediate results for debugging/transparency

## Global Instance

```python
# Global RAG pipeline instance
rag_pipeline = RAGPipeline()
```

**Decision**: Singleton pattern for the RAG pipeline, ensuring consistent state across the application while allowing import-based access.

## Key Design Decisions Summary

### 1. **Modular Architecture**
- Each component (chunking, embedding, storage, reranking, generation) is separate
- Allows independent testing, upgrading, and replacement
- Clear interfaces between components

### 2. **Graceful Degradation**
- System continues working even if some components fail
- LLM fallback to extractive answers
- Reranker fallback to retrieval-only results

### 3. **Thread Safety**
- All vector store operations are locked
- Prevents race conditions in multi-threaded FastAPI environment

### 4. **Persistence Strategy**
- FAISS for vectors (fast, compressed)
- JSON for metadata (human-readable, flexible)
- Automatic save/load on startup

### 5. **Performance Optimizations**
- Chunk overlap for continuity
- Configurable retrieval depth
- Efficient embedding batching

### 6. **Local-First Design**
- All models run locally (no API costs)
- TinyLlama chosen for size/speed balance
- CPU-only operation for broad compatibility

### 7. **Error Resilience**
- Try/catch blocks around all model operations
- Clear error messages and fallback behaviors
- System remains functional during partial failures

This implementation provides a robust, scalable RAG system that balances performance, reliability, and maintainability while staying true to the requirements of being free, lightweight, and local.</content>
<parameter name="filePath">c:\Users\manal\Coding\project1\RAG_PIPELINE_CODE_EXPLANATION.md