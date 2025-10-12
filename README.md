# DocuMind: Local, Private, and Powerful RAG Document Intelligence

DocuMind is a next-generation, privacy-first Retrieval-Augmented Generation (RAG) platform for semantic search and question answering over your own documents. It is designed for researchers, professionals, and teams who demand full control, transparency, and performance—without ever sending data to the cloud.

---

## 🚀 Quick Start

```bash
# Backend (Python, FastAPI)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (React, Vite, TypeScript)
cd ../frontend
npm install
npm run dev
```

---

## Why DocuMind?

- **Truly Private:** All processing is 100% local. No cloud, no telemetry, no vendor lock-in.
- **Production-Grade RAG:** Modern pipeline with chunking, embedding, vector search, reranking, and LLM generation.
- **Fast & Efficient:** Optimized for laptops and desktops (4–8GB RAM, modern CPU).
- **Open Source:** Built on top of the best open-source models and libraries (FAISS, sentence-transformers, llama-cpp, TinyLlama).
- **Extensible:** Modular backend and frontend for easy customization and research.

---

## 🏗️ Technical Architecture

### 1. Document Upload, Chunking & Embedding (at Ingest)
- **DocumentProcessor** extracts text, splits into semantic chunks, and generates embeddings at upload time using `sentence-transformers`.
- Chunks and embeddings are immediately stored in a persistent FAISS vector index.

### 2. Vector Store (FAISS, Persistent)
- All chunk embeddings and metadata are stored in FAISS, persisted to disk.
- Deletion of a document removes all its chunks/embeddings from the vector index.

### 3. Query Pipeline (RAGPipeline)
- At query time, only retrieval, rerank, and LLM generation are performed.
- No corpus embedding or chunking is ever done at query time.
- Query is embedded, top-k chunks are retrieved from FAISS, reranked with a cross-encoder, and passed to a local LLM (TinyLlama) for answer generation.

### 4. Local LLM Generation
- Uses TinyLlama-1.1B-Chat (runs on CPU via llama-cpp-python) for fast, private, and high-quality answer generation.

---

## 🔒 Privacy & Security

- **100% Local:** No data ever leaves your device.
- **No Telemetry:** No analytics, no tracking, no cloud APIs.
- **Encryption:** (Planned) AES-256 for document storage.
- **Open Source:** Inspect, audit, and extend every line of code.

---

## ✨ Features

- Drag & drop document upload (PDF, DOCX, TXT)
- Semantic chunking and embedding at upload
- Fast vector search (FAISS)
- Cross-encoder reranking for true semantic relevance
- Local LLM answer generation (TinyLlama)
- Delete documents and instantly remove all associated vectors
- Modern, responsive React UI (Material-UI)
- No cloud, no vendor lock-in

---

## � Project Structure

```
project-root/
├── backend/    # FastAPI, RAG pipeline, vector store, LLM
├── frontend/   # React, Vite, TypeScript, Material-UI
├── docs/       # Architecture, design, and usage docs
└── tests/      # Integration and unit tests
```

---

## 🧑‍💻 Technical Deep Dive

### Backend Stack
- **FastAPI**: High-performance Python API
- **DocumentProcessor**: Handles text extraction, chunking, and embedding at upload
- **FAISS**: Persistent, on-disk vector store for fast similarity search
- **sentence-transformers**: all-MiniLM-L6-v2 for chunk/query embeddings
- **CrossEncoder**: ms-marco-MiniLM-L-6-v2 for reranking
- **llama-cpp-python**: Local LLM inference (TinyLlama-1.1B-Chat)

### Frontend Stack
- **React + Vite**: Modern, fast UI
- **TypeScript**: Type safety everywhere
- **Material-UI**: Beautiful, accessible components
- **Zustand**: Local state management

### Pipeline Diagram

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

## 📝 Usage

1. **Start the backend:**
	- `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`
2. **Start the frontend:**
	- `cd frontend && npm install && npm run dev`
3. **Upload documents:**
	- Drag & drop or use the upload button in the UI
4. **Ask questions:**
	- Enter your query in the search bar; get instant, LLM-powered answers
5. **Delete documents:**
	- Remove any document and all its vectors with one click

---

## �️ System Requirements

- **RAM:** 4–8GB recommended
- **CPU:** Modern dual/quad-core (Intel i5/Ryzen 5 or better)
- **Disk:** ~2–3GB for models, plus your documents

---

## 📚 References

- [sentence-transformers](https://www.sbert.net/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- [TinyLlama](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF)

---

## 💡 Contributing & Extending

DocuMind is designed to be modular and hackable. PRs, issues, and feature requests are welcome!

---

## License

MIT License. See LICENSE for details.

---

## 🧑‍💻 Backend Stack: Technical Choices & Rationale

### FastAPI
- **Why:** FastAPI is a modern, high-performance Python web framework. It provides automatic OpenAPI docs, async support, and is easy to scale. Its type hints and validation make it robust for production APIs.

### DocumentProcessor
- **Why:** Centralizes all document ingestion logic. Handles text extraction, chunking, and embedding at upload time, ensuring that all downstream RAG steps operate on pre-processed, semantically meaningful data. This separation of concerns improves maintainability and performance.

### Text Extraction Libraries (pdfplumber, python-docx, plain text)
- **Why:** These libraries are lightweight, open-source, and reliable for extracting text from the most common document formats. They allow for easy extension to new formats if needed.

### TextChunker
- **Why:** Implements a sliding window chunking strategy with overlap, which preserves context and improves retrieval quality. Chunking at upload time ensures no repeated computation and enables fast query-time performance.

### sentence-transformers (all-MiniLM-L6-v2)
- **Why:** This model is small (80MB), CPU-friendly, and provides state-of-the-art semantic embeddings. It is fast enough for real-time use on laptops and is open-source, with no licensing restrictions.

### FAISS (VectorStore)
- **Why:** FAISS is the gold standard for vector similarity search. It is highly optimized, supports both in-memory and on-disk indexes, and is free/open-source. It enables sub-second retrieval even for large document collections.

### CrossEncoder (ms-marco-MiniLM-L-6-v2)
- **Why:** Reranking with a cross-encoder provides much higher semantic relevance than vector search alone. This model is CPU-friendly and open-source, and can be swapped for larger models if needed.

### llama-cpp-python (TinyLlama-1.1B-Chat)
- **Why:** Enables local LLM inference with a small, quantized model that runs on CPU. No cloud, no API keys, and fast enough for interactive use. TinyLlama is open, efficient, and can be replaced with larger models as hardware allows.

### Design Philosophy
- **Local-First:** All computation is performed on your device for privacy and speed.
- **Modular:** Each component (extraction, chunking, embedding, retrieval, rerank, generation) is swappable and independently testable.
- **Open Source:** All dependencies are free, open, and have permissive licenses.
- **Performance:** Choices are made to ensure the system runs well on consumer hardware, with no GPU required.