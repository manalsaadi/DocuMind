# DocuMind RAG Architecture (Lightweight, Free, Local)

## Overview
This document describes the architecture and pipeline of the DocuMind Retrieval-Augmented Generation (RAG) system, designed to run efficiently on a typical laptop using only free and open-source tools.

---

## Pipeline Steps


### 1. Document Ingestion, Chunking & Embedding (at Upload)
- **Description:**
  - Users upload documents (PDF, DOCX, TXT, etc.) via FastAPI endpoints.
  - Text is extracted, split into semantic chunks, and embedded immediately at upload time.
  - Chunking and embedding are performed in the `DocumentProcessor` as soon as the document is uploaded.
- **Tools:**
  - FastAPI (API)
  - pdfplumber, python-docx (text extraction)
  - `TextChunker` (for chunking)
  - `sentence-transformers/all-MiniLM-L6-v2` (for embedding)


### 2. Vector Store
- **Description:**
  - Embeddings for all document chunks are stored in a vector database (FAISS) at upload time.
  - No embedding or chunking is performed at query time.
- **Tools:**
  - [FAISS](https://github.com/facebookresearch/faiss) (local, in-memory, free)


### 3. Retrieval (at Query Time)
- **Description:**
  - For a user query, generate its embedding and retrieve the top-N most similar chunks from the vector store.
  - No corpus embedding or chunking is performed at query time—only retrieval, rerank, and generation.
- **Tools:**
  - `sentence-transformers` (for query embedding)
  - FAISS (for similarity search)


### 4. Reranking & Generation (at Query Time)
- **Description:**
  - Retrieved chunks are reranked for semantic relevance using a cross-encoder reranker.
  - The top reranked chunks are concatenated as context and sent to a local LLM to generate an answer.
- **Tools:**
  - [cross-encoder/ms-marco-MiniLM-L-6-v2](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2) (420MB, CPU-friendly)
  - [TinyLlama-1.1B-Chat](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF) (1.5GB, runs on CPU)
  - `sentence-transformers` or `transformers` library
  - `llama-cpp-python` library with GGUF model support
  - Parameters: 2048 context window, temperature 0.7, top-p 0.9

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
[User Uploads]
  ↓
[Text Extraction, Chunking & Embedding (DocumentProcessor)]
  ↓
[FAISS Vector DB] ← [Document Storage]
  ↑
[User Query] → [Query Embedding] → [FAISS Search] → [Reranker]
  ↓
[Top Chunks] → [LLM Generation] → [Answer]
```

---


## All Tools Are Free & Local
- No paid APIs, no cloud required.
- All models and databases run on your own machine.

## Key Principle
- Chunking and embedding are performed once at upload. Querying never triggers corpus embedding or chunking—only retrieval, rerank, and generation.

---

## References
- [sentence-transformers](https://www.sbert.net/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [HuggingFace Transformers](https://huggingface.co/transformers/)
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- [TinyLlama](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF)
