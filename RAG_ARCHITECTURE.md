# DocuMind RAG Architecture (Lightweight, Free, Local)

## Overview
This document describes the architecture and pipeline of the DocuMind Retrieval-Augmented Generation (RAG) system, designed to run efficiently on a typical laptop using only free and open-source tools.

---

## Pipeline Steps

### 1. Document Ingestion & Chunking
- **Description:**
  - Users upload documents (PDF, DOCX, TXT, etc.) via FastAPI endpoints.
  - Text is extracted and split into semantic chunks for downstream processing.
- **Tools:**
  - FastAPI (API)
  - pdfplumber, python-docx (text extraction)
  - Integrated `TextChunker` in RAG pipeline (configurable chunk size 1000 chars, overlap 200 chars)

### 2. Embedding Generation
- **Description:**
  - Each chunk is converted into a vector embedding for semantic search.
- **Tools:**
  - [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) (80MB, fast, CPU-friendly)
  - `sentence-transformers` Python library

### 3. Vector Store
- **Description:**
  - Embeddings are stored in a vector database for efficient similarity search.
- **Tools:**
  - [FAISS](https://github.com/facebookresearch/faiss) (local, in-memory, free)
  - Optionally, [ChromaDB](https://www.trychroma.com/) (free, persistent)

### 4. Retrieval
- **Description:**
  - For a user query, generate its embedding and retrieve the top-N most similar chunks from the vector store.
- **Tools:**
  - `sentence-transformers` (for query embedding)
  - FAISS (for similarity search)

### 5. Reranking
- **Description:**
  - Retrieved chunks are reranked for true semantic relevance using a cross-encoder reranker.
- **Tools:**
  - [cross-encoder/ms-marco-MiniLM-L-6-v2](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2) (420MB, CPU-friendly)
  - `sentence-transformers` or `transformers` library

### 6. Augmentation & Generation
- **Description:**
  - The top reranked chunks are concatenated as context and sent to a local LLM to generate an answer.
- **Tools:**
  - [TinyLlama-1.1B-Chat](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF) (1.5GB, runs on CPU)
  - `llama-cpp-python` library with GGUF model support
  - Parameters: 2048 context window, temperature 0.7, top-p 0.9
  - `llama-cpp-python` (for local inference)

---

## System Requirements
- **RAM:** 4–8GB (recommended)
- **CPU:** Any modern dual/quad-core (Intel i5/Ryzen 5 or better)
- **Disk:** ~2–3GB for models, plus your document and embedding data

---

## Summary Table
| Step         | Tool/Model                                 | Size    | Notes                |
|--------------|--------------------------------------------|---------|----------------------|
| Embedding    | all-MiniLM-L6-v2 (sentence-transformers)   | 80MB    | Fast, CPU-friendly   |
| Vector Store | FAISS                                      | -       | In-memory, free      |
| Reranker     | cross-encoder/ms-marco-MiniLM-L-6-v2       | 420MB   | Fast, CPU-friendly   |
| LLM          | TinyLlama-1.1B-Chat (GGUF, llama-cpp)      | 1.5GB   | Local, CPU-friendly  |

---

## Pipeline Diagram

```
[User Uploads] → [Text Extraction & Chunking] → [Embedding Model]
      ↓                                             ↓
[Document Storage] ← [FAISS Vector DB] ← [Embeddings]
      ↓                                             ↑
[User Query] → [Query Embedding] → [FAISS Search] → [Reranker]
      ↓
[Top Chunks] → [LLM Generation] → [Answer]
```

---

## All Tools Are Free & Local
- No paid APIs, no cloud required.
- All models and databases run on your own machine.

---

## References
- [sentence-transformers](https://www.sbert.net/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [HuggingFace Transformers](https://huggingface.co/transformers/)
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- [TinyLlama](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF)
