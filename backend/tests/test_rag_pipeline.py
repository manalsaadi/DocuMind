"""
Test script for each step of the RAG pipeline (DocuMind)
Run: python tests/test_rag_pipeline.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.rag_pipeline import rag_pipeline
from modules.document_processor import DocumentProcessor

def test_chunking():
    print("\n[1] Testing Chunking...")
    test_text = "This is a test document. It contains several sentences. The quick brown fox jumps over the lazy dog. RAG pipelines are awesome for document processing and retrieval."
    
    # Test chunking directly in RAG pipeline
    chunks = rag_pipeline.chunk_text(test_text)
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}: {repr(chunk['text'])}")
    
    return chunks

def test_faiss(chunks, test_text):
    print("\n[3] Testing FAISS Vector Store...")
    # Create a temporary test document ID
    test_doc_id = "test_doc_123"
    
    # Add document text directly (chunking happens internally)
    rag_pipeline.add_document(test_doc_id, test_text)
    
    # Test search
    query = "What is a RAG pipeline?"
    query_embedding = rag_pipeline.embedding_model.encode([query], convert_to_numpy=True)
    search_results = rag_pipeline.vector_store.search(query_embedding, top_k=3)
    
    print(f"Top 3 search results:")
    for chunk_info, distance in search_results:
        print(f"- Distance: {distance:.4f}")
        print(f"  Text: {repr(chunk_info['text'])}")
    
    return search_results

def test_rerank(query, retrieved_chunks):
    print("\n[4] Testing Reranking...")
    reranked = rag_pipeline.rerank(query, retrieved_chunks)
    
    print("Reranked chunks (best first):")
    for i, chunk in enumerate(reranked):
        score = chunk.get('rerank_score', 'N/A')
        print(f"{i+1}. Score: {score}")
        print(f"   Text: {repr(chunk['text'])}")
    
    return reranked

def test_llm(context, query):
    print("\n[5] Testing LLM Generation...")
    print(f"Query: {query}")
    print(f"Context length: {len(context)} characters")
    
    # Test the actual LLM generation
    answer = rag_pipeline.generate_answer(query, [{'text': context}])
    print(f"Generated Answer: {answer}")
    
    if rag_pipeline.llm_model:
        print("✅ LLM is loaded and working")
    else:
        print("⚠️  LLM not available, using fallback generation")

if __name__ == "__main__":
    # 1. Chunking
    test_text = "This is a test document. It contains several sentences. The quick brown fox jumps over the lazy dog. RAG pipelines are awesome for document processing and retrieval."
    chunks = test_chunking()
    
    # 2. Embedding (now done internally in add_document)
    print("\n[2] Embedding is now handled internally in the RAG pipeline")
    
    # 3. FAISS Vector Store
    search_results = test_faiss(chunks, test_text)
    
    # Convert search results to dict format for reranking
    retrieved_chunks = []
    for chunk_info, distance in search_results:
        retrieved_chunks.append({
            'text': chunk_info['text'],
            'doc_id': chunk_info['doc_id'],
            'score': distance,
            'metadata': chunk_info.get('metadata', {})
        })
    
    # 4. Reranking
    query = "What is a RAG pipeline?"
    reranked = test_rerank(query, retrieved_chunks)
    
    # 5. LLM Generation
    context = "\n".join([chunk['text'] for chunk in reranked])
    test_llm(context, query)
    
    print("\n✅ All RAG pipeline steps tested successfully!")
