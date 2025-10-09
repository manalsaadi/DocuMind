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

# LINE 12-22: Import Statements - Import all necessary libraries for the RAG pipeline
# Import type hints for better code documentation and IDE support
from typing import List, Dict, Any, Optional, Tuple
# NumPy for numerical operations and array manipulations (required by FAISS and sentence-transformers)
import numpy as np
# Facebook AI Similarity Search library - core vector search engine for the RAG system
import faiss
# JSON library for data serialization (used to save/load chunk metadata alongside FAISS indices)
import json
# Operating system interface for file path operations and environment checks
import os
# Modern path handling from pathlib (preferred over os.path for cleaner, more intuitive path operations)
from pathlib import Path
# ML models: SentenceTransformer for converting text to vector embeddings, CrossEncoder for reranking
from sentence_transformers import SentenceTransformer, CrossEncoder
# Threading module for thread synchronization (makes vector store operations thread-safe)
import threading
# DateTime class (could be used for timestamps in metadata or logging)
from datetime import datetime
# Optional import for local LLM inference - try/except allows module to load even if not installed
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None


# LINE 26-27: TextChunker Class Definition - Define class to handle semantic text splitting for RAG processing
class TextChunker:
    """
    Handles semantic text splitting for RAG processing.

    Uses a sliding window approach with overlap to ensure complete text coverage
    while maintaining context continuity between chunks.
    """

# LINE 29-32: TextChunker.__init__ - Constructor method with default parameters for chunk size and overlap
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize text chunker with configurable parameters.

        Args:
            chunk_size: Maximum characters per chunk (default 1000)
            overlap: Characters to overlap between adjacent chunks (default 200)
        """
        self.chunk_size = chunk_size  # Each chunk will be approximately 1000 characters
        self.overlap = overlap        # Adjacent chunks overlap by 200 characters

    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Split text into semantic chunks for RAG processing.

        Uses sliding window with overlap to ensure no information loss at boundaries.
        Each chunk includes text content, length, and optional metadata.

        Args:
            text: Input text to be chunked
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of dictionaries, each containing chunk text, length, and metadata
        """
        # Handle empty input gracefully
        if not text.strip():
            return []

        chunks = []  # Will store all generated chunks
        start = 0    # Starting position for first chunk

        # Continue until we've processed entire text
        while start < len(text):
            # Calculate end position of current chunk
            end = start + self.chunk_size
            # Adjust end if it exceeds text length (for final chunk)
            if end > len(text):
                end = len(text)

            # Extract chunk text using slice notation
            chunk_text = text[start:end]

            # Create chunk dictionary with text, length, and metadata
            chunks.append({
                "text": chunk_text,
                "length": len(chunk_text),
                "metadata": metadata or {}  # Use empty dict if no metadata provided
            })

            # Advance start position with overlap for sliding window
            start += self.chunk_size - self.overlap
            # Break if we've reached the end of text
            if start >= len(text):
                break

        return chunks


# LINE 60-61: VectorStore Class Definition - Define FAISS-based vector store class for document embeddings
class VectorStore:
    """
    FAISS-based vector store for document embeddings.

    Provides thread-safe vector storage, persistence, and similarity search.
    Uses dual persistence: FAISS for efficient vector storage, JSON for human-readable metadata.
    """

    def __init__(self, dimension: int = 384, index_file: str = "vector_index.faiss"):
        """
        Initialize vector store with specified dimensions.

        Args:
            dimension: Vector dimensionality (default 384 matches sentence-transformers/all-MiniLM-L6-v2)
            index_file: Path for FAISS index persistence
        """
        self.dimension = dimension                    # Vector dimensionality (384D for MiniLM)
        self.index_file = Path(index_file)           # Convert to Path object for modern path handling
        self.index = None                            # FAISS index (loaded/created later)
        self.chunks = []                             # List storing chunk metadata (text, doc_id, etc.)
        self.doc_mapping = {}                        # Maps chunk indices to document IDs
        self.embeddings = np.empty((0, dimension), dtype=np.float32)  # Store all embeddings for rebuilding
        self._lock = threading.RLock()               # Reentrant lock for thread safety in FastAPI
        self._load_or_create_index()                 # Initialize index on startup

    def _load_or_create_index(self):
        """
        Load existing FAISS index and metadata, or create new ones.

        Attempts to restore previous state from disk. Falls back to empty index if loading fails.
        This ensures system continuity across restarts while being resilient to corruption.
        """
        # Check if FAISS index file exists on disk
        if self.index_file.exists():
            try:
                # Load FAISS index from disk (contains vector data)
                self.index = faiss.read_index(str(self.index_file))

                # Load associated metadata (human-readable chunk information)
                metadata_file = self.index_file.with_suffix('.json')
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        data = json.load(f)
                        self.chunks = data.get('chunks', [])          # Restore chunk metadata
                        self.doc_mapping = data.get('doc_mapping', {}) # Restore doc-to-chunk mapping
                        embeddings_list = data.get('embeddings', [])
                        if embeddings_list:
                            self.embeddings = np.array(embeddings_list, dtype=np.float32)
                        else:
                            # Fallback: create empty embeddings array
                            self.embeddings = np.empty((0, self.dimension), dtype=np.float32)
            except Exception as e:
                # Log warning and create fresh index if loading fails
                print(f"Warning: Could not load existing index: {e}")
                self._create_new_index()
        else:
            # No existing index found, create new empty one
            self._create_new_index()

    def _create_new_index(self):
        """
        Create a new empty FAISS index.

        Uses IndexFlatL2 for exact L2 (Euclidean) distance search.
        Suitable for small-to-medium document collections where exact search is preferred.
        """
        self.index = faiss.IndexFlatL2(self.dimension)  # L2 distance = Euclidean distance
        self.chunks = []                                # Reset chunk metadata
        self.doc_mapping = {}                           # Reset document mapping
        self.embeddings = np.empty((0, self.dimension), dtype=np.float32)  # Reset embeddings

    def _save_index(self):
        """
        Persist index and metadata to disk.

        Saves both FAISS vectors and JSON metadata for complete state restoration.
        Uses indentation for human-readable JSON debugging.
        """
        if self.index:  # Only save if index exists
            # Save FAISS index (binary format, efficient for vectors)
            faiss.write_index(self.index, str(self.index_file))

            # Save metadata as formatted JSON (human-readable)
            metadata_file = self.index_file.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump({
                    'chunks': self.chunks,
                    'doc_mapping': self.doc_mapping,
                    'embeddings': self.embeddings.tolist() if self.embeddings.size > 0 else [],
                    'dimension': self.dimension
                }, f, indent=2)  # indent=2 for readability
    
    def _rebuild_embeddings_from_chunks(self):
        """
        Rebuild embeddings array from chunk texts (fallback method).
        
        Used when embeddings are not stored in metadata but chunks exist.
        This is a slower fallback that re-encodes all chunk texts.
        """
        if not self.chunks:
            self.embeddings = np.empty((0, self.dimension), dtype=np.float32)
            return
            
        # Re-encode all chunk texts (expensive operation)
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        texts = [chunk['text'] for chunk in self.chunks]
        self.embeddings = model.encode(texts, convert_to_numpy=True)
    
    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray, doc_id: str):
        """
        Add document chunks and their embeddings to the vector store.

        Thread-safe operation that validates dimensions, adds vectors to FAISS,
        stores metadata, and persists changes to disk.

        Args:
            chunks: List of chunk dictionaries with text and metadata
            embeddings: NumPy array of chunk embeddings (shape: n_chunks x dimension)
            doc_id: Unique identifier for the source document

        Raises:
            ValueError: If embedding dimensions don't match index dimensions
        """
        with self._lock:  # Thread-safe operation for FastAPI compatibility
            # Validate embedding dimensions to prevent corruption
            if embeddings.shape[1] != self.dimension:
                raise ValueError(f"Embedding dimension {embeddings.shape[1]} doesn't match index dimension {self.dimension}")

            start_idx = len(self.chunks)  # Record starting index for new chunks
            self.index.add(embeddings)    # Add vectors to FAISS index
            
            # Store embeddings for potential rebuilding
            self.embeddings = np.vstack([self.embeddings, embeddings.astype(np.float32)]) if self.embeddings.size > 0 else embeddings.astype(np.float32)

            # Store metadata for each chunk
            for i, chunk in enumerate(chunks):
                chunk_info = {
                    'text': chunk['text'],           # Actual chunk text
                    'doc_id': doc_id,                # Source document identifier
                    'chunk_idx': i,                  # Index within document
                    'metadata': chunk.get('metadata', {})  # Additional metadata
                }
                self.chunks.append(chunk_info)
                # Map global chunk index to document ID for efficient lookup
                self.doc_mapping[start_idx + i] = doc_id

            self._save_index()  # Persist all changes to disk

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for similar chunks using vector similarity.

        Performs k-nearest neighbor search using L2 distance (Euclidean).
        Returns chunks with their similarity scores.

        Args:
            query_embedding: Query vector (1D or 2D array)
            top_k: Number of most similar chunks to return

        Returns:
            List of (chunk_info, distance) tuples, sorted by similarity
        """
        with self._lock:  # Thread-safe search operation
            # Handle empty index
            if self.index.ntotal == 0:
                return []

            # FAISS expects 2D input even for single queries - reshape if needed
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)

            # Perform FAISS search, limiting to available vectors
            distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))

            results = []
            # Process search results, filtering out invalid indices
            for dist, idx in zip(distances[0], indices[0]):
                if idx != -1:  # -1 indicates no valid result
                    chunk_info = self.chunks[idx]
                    results.append((chunk_info, float(dist)))

            return results

    def remove_document(self, doc_id: str):
        """
        Remove all chunks for a document (rebuilds index with remaining vectors).

        FAISS doesn't support efficient deletion, so we rebuild the index
        with remaining chunks using stored embeddings. This ensures remaining
        documents stay searchable after deletion.

        Args:
            doc_id: Document identifier to remove
        """
        with self._lock:  # Thread-safe operation
            # Find all chunk indices belonging to this document
            indices_to_remove = [i for i, chunk in enumerate(self.chunks) if chunk['doc_id'] == doc_id]

            if not indices_to_remove:
                return  # Document not found, nothing to do

            # Get indices of chunks to keep (all except those being removed)
            all_indices = set(range(len(self.chunks)))
            keep_indices = sorted(all_indices - set(indices_to_remove))

            # Rebuild index with remaining vectors
            if keep_indices:
                # Keep only the embeddings and chunks that are not being removed
                remaining_embeddings = self.embeddings[keep_indices]
                remaining_chunks = [self.chunks[i] for i in keep_indices]
                remaining_doc_mapping = {new_idx: self.doc_mapping[old_idx] for new_idx, old_idx in enumerate(keep_indices)}
                
                # Create new index with remaining vectors
                new_index = faiss.IndexFlatL2(self.dimension)
                new_index.add(remaining_embeddings)
                
                # Update instance variables
                self.index = new_index
                self.chunks = remaining_chunks
                self.doc_mapping = remaining_doc_mapping
                self.embeddings = remaining_embeddings
            else:
                # No chunks remaining, create empty index
                self._create_new_index()

            self._save_index()  # Persist changes


# LINE 172-173: RAGPipeline Class Definition - Define main RAG pipeline orchestrator class
class RAGPipeline:
    """
    Complete RAG pipeline orchestrator.

    Coordinates all RAG components (chunking, embedding, storage, reranking, generation)
    into a single, easy-to-use interface. Implements graceful degradation for missing components.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the complete RAG pipeline with all components.

        Loads ML models, initializes components, and sets up graceful degradation
        for optional components that may not be available.

        Args:
            config: Optional configuration dictionary for pipeline parameters
        """
        # Default configuration
        self.config = {
            "llm_max_tokens": 256,
            "llm_temperature": 0.7,
            "llm_top_p": 0.9,
            "chunk_size": 1000,
            "chunk_overlap": 200
        }
        
        # Update with provided config
        if config:
            self.config.update(config)
        
        # Initialize core embedding model (always required)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize reranker with graceful degradation
        try:
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        except Exception as e:
            print(f"Warning: Could not load reranker: {e}")
            self.reranker = None  # System works without reranker

        # Initialize text chunker with configurable parameters
        self.chunker = TextChunker(
            chunk_size=self.config["chunk_size"],
            overlap=self.config["chunk_overlap"]
        )

        # Initialize vector store with correct embedding dimensions
        self.vector_store = VectorStore(dimension=self.embedding_model.get_sentence_embedding_dimension())

        # Initialize LLM (may be None if not available)
        self.llm_model = self._initialize_llm()

    def _initialize_llm(self):
        """
        Initialize local LLM for generation.

        Attempts to load TinyLlama model from various locations.
        Returns None if model unavailable, enabling graceful degradation.

        Returns:
            Llama instance or None if initialization fails
        """
        # Check if llama-cpp-python library is available
        if Llama is None:
            print("Warning: llama-cpp-python not installed. LLM generation will be limited.")
            return None

        try:
            # Try to load TinyLlama model from expected location
            model_path = os.path.join(os.path.dirname(__file__), "..", "models", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
            if not os.path.exists(model_path):
                # Search other common locations
                model_path = self._find_or_download_model()

            # Load model if path found and file exists
            if model_path and os.path.exists(model_path):
                llm = Llama(
                    model_path=model_path,
                    n_ctx=2048,      # Context window (sufficient for document Q&A)
                    n_threads=4,     # CPU threads (balances speed vs resource usage)
                    verbose=False    # Reduce log noise
                )
                print("Successfully loaded TinyLlama model for generation")
                return llm
            else:
                print("Warning: TinyLlama model not found. Using fallback generation.")
                return None
        except Exception as e:
            print(f"Warning: Could not initialize LLM: {e}")
            return None

    def _find_or_download_model(self):
        """
        Find existing TinyLlama model or provide download instructions.

        Checks common locations where the model might be stored.
        Provides user-friendly download instructions if not found.

        Returns:
            Model path string or None if not found
        """
        # Check multiple possible locations for flexibility
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "..", "models", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"),  # Project models dir
            os.path.join(os.path.expanduser("~"), ".cache", "llama.cpp", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"),  # User cache
            "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"  # Current directory
        ]

        # Return first found path
        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Provide download instructions if model not found
        print("TinyLlama model not found. Please download from:")
        print("https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
        print("And place it in the backend/models/ directory")
        return None
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces for RAG processing.

        Delegates to internal TextChunker instance for clean API.
        """
        return self.chunker.chunk_text(text, metadata)

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> np.ndarray:
        """
        Generate embeddings for text chunks.

        Uses sentence-transformers to convert chunk texts to vectors.
        Processes all chunks in batch for efficiency.

        Args:
            chunks: List of chunk dictionaries with 'text' key

        Returns:
            NumPy array of embeddings (shape: n_chunks x embedding_dim)
        """
        texts = [chunk['text'] for chunk in chunks]  # Extract texts from chunks
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings

    # LINE 240-251: RAGPipeline.add_document - Method to add a document to the RAG pipeline (includes chunking)
    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None):
        """
        Deprecated: Chunking and embedding are now performed in DocumentProcessor at upload time.
        This method is a no-op and should not be used.
        """
        print(f"[WARNING] RAGPipeline.add_document is deprecated. Chunking/embedding should be done in DocumentProcessor.")
        return

    def remove_document(self, doc_id: str):
        """
        Remove a document from the RAG pipeline.

        Delegates to vector store for document removal.
        """
        self.vector_store.remove_document(doc_id)

    # LINE 257-275: RAGPipeline.retrieve - Method to retrieve relevant chunks for a query using vector similarity
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query using vector similarity.

        Converts query to embedding, searches vector store, and formats results.

        Args:
            query: Search query string
            top_k: Number of top chunks to retrieve

        Returns:
            List of chunk dictionaries with text, doc_id, score, and metadata
        """
        # Generate embedding for the query
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)[0]

        # Search vector store for similar chunks
        search_results = self.vector_store.search(query_embedding, top_k=top_k)

        # Convert FAISS results to standardized dictionary format
        retrieved_chunks = []
        for chunk_info, distance in search_results:
            retrieved_chunks.append({
                'text': chunk_info['text'],
                'doc_id': chunk_info['doc_id'],
                'score': distance,  # L2 distance (lower = more similar)
                'metadata': chunk_info.get('metadata', {})
            })

        return retrieved_chunks

    # LINE 277-295: RAGPipeline.rerank - Method to rerank retrieved chunks using cross-encoder for better relevance
    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Rerank retrieved chunks using cross-encoder for better relevance.

        Uses more sophisticated cross-encoder model to score query-chunk pairs.
        Falls back to original ranking if reranker unavailable.

        Args:
            query: Search query string
            chunks: Retrieved chunks to rerank
            top_k: Number of top chunks to return after reranking

        Returns:
            Reranked chunks with rerank_score added to metadata
        """
        # Graceful degradation: return top chunks if reranker unavailable
        if not self.reranker or not chunks:
            return chunks[:top_k]

        # Prepare (query, chunk_text) pairs for cross-encoder
        pairs = [(query, chunk['text']) for chunk in chunks]

        # Get relevance scores from cross-encoder
        scores = self.reranker.predict(pairs)

        # Sort by score (higher = more relevant for cross-encoder)
        reranked = []
        for chunk, score in sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True):
            chunk_copy = chunk.copy()
            chunk_copy['rerank_score'] = float(score)  # Add reranking score
            reranked.append(chunk_copy)

        return reranked[:top_k]

    # LINE 297-327: RAGPipeline.generate_answer - Method to generate answer using retrieved context and local LLM
    def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate answer using retrieved context and local LLM.

        Creates structured prompt with context and query, generates response.
        Falls back to extractive answer if LLM unavailable or fails.

        Args:
            query: User question
            context_chunks: Relevant chunks from retrieval/reranking

        Returns:
            Generated answer string
        """
        # Handle empty context
        if not context_chunks:
            return "No relevant information found in the documents."

        # Combine context from top 3 chunks (balance richness vs token limits)
        context = "\n\n".join([chunk['text'] for chunk in context_chunks[:3]])

        # Attempt LLM generation if available
        if self.llm_model:
            try:
                # Create structured prompt for consistent responses
                prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided context. 
If the context doesn't contain enough information to answer the question, say so clearly and never speculate or make assumptions.

Context:
{context}

Question: {query}

Answer:"""

                # Generate response with configurable parameters
                response = self.llm_model(
                    prompt,
                    max_tokens=self.config["llm_max_tokens"],    # Configurable response length
                    temperature=self.config["llm_temperature"],   # Configurable creativity
                    top_p=self.config["llm_top_p"],         # Configurable nucleus sampling
                    stop=["Question:", "\n\n"],  # Prevent rambling
                    echo=False         # Don't echo the prompt
                )

                # Extract and validate answer from response
                if response and 'choices' in response and len(response['choices']) > 0:
                    answer = response['choices'][0]['text'].strip()
                    if answer:
                        return answer

            except Exception as e:
                print(f"LLM generation failed: {e}")

        # Fallback: Return extractive answer from context
        return f"Based on the retrieved information:\n\n{context[:500]}{'...' if len(context) > 500 else ''}"

    # LINE 332-349: RAGPipeline.query - Method implementing complete RAG query pipeline: Retrieve -> Rerank -> Generate
    def query(self, query: str, retrieve_k: int = 10, rerank_k: int = 3) -> Dict[str, Any]:
        """
        Complete RAG query pipeline: Retrieve -> Rerank -> Generate.

        Orchestrates the full RAG workflow in correct sequence.
        Retrieves more candidates than needed, then selects best via reranking.

        Args:
            query: User question
            retrieve_k: Number of chunks to retrieve initially (default 10)
            rerank_k: Number of chunks to rerank and use for generation (default 3)

        Returns:
            Dictionary with query, answer, retrieved chunks, reranked chunks, and pipeline steps
        """
        # Step 1: Retrieve - Get candidate chunks using vector similarity
        retrieved = self.retrieve(query, top_k=retrieve_k)

        # Step 2: Rerank - Select most relevant chunks using cross-encoder
        reranked = self.rerank(query, retrieved, top_k=rerank_k)

        # Step 3: Generate - Create answer using reranked context
        answer = self.generate_answer(query, reranked)

        # Return comprehensive result
        return {
            'query': query,
            'answer': answer,
            'retrieved_chunks': retrieved,
            'reranked_chunks': reranked,
            'pipeline_steps': ['retrieve', 'rerank', 'generate']
        }


# Global RAG pipeline instance for easy import-based access across the application
rag_pipeline = RAGPipeline()