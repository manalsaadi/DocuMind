# DocuMind - Privacy-First Document Analysis Platform

A local-first document analysis application that keeps your data private while providing intelligent search and summarization capabilities.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Install frontend dependencies
cd frontend
npm install

# Start development server
npm run dev
```

## 📁 Project Structure

```
documind/
├── frontend/          # React + TypeScript UI
├── backend/           # FastAPI Python backend (coming next)
├── shared/           # Shared types and utilities
├── docs/             # Documentation
└── tests/            # Integration tests
```

## 🏗️ Architecture


**Modular RAG System** with clear separation of concerns:

### Application-Level Modules
- **UI Module**: React components with Material-UI
- **Orchestrator Module**: Coordinates RAG pipeline
- **Data Manager Module**: Local state management (Zustand)

### Backend Pipeline (Current)
- **DocumentProcessor**: Handles text extraction, chunking, and embedding at upload time. As soon as a document is uploaded, it is split into semantic chunks and embedded using sentence-transformers. Chunks and embeddings are immediately stored in the vector index (FAISS).
- **RAGPipeline**: Handles only retrieval, rerank, and LLM generation at query time. No corpus embedding or chunking is performed at query time.
- **VectorStore (FAISS)**: Stores all chunk embeddings and metadata. Deletion of a document removes all its chunks/embeddings from the vector index.

**Key Principle:**
- Chunking and embedding are performed once at upload. Querying never triggers corpus embedding or chunking—only retrieval, rerank, and generation.

## 🔒 Privacy First

- **100% Local Processing**: No data leaves your machine
- **Encryption**: AES-256 for document storage (coming soon)
- **No Telemetry**: Zero external connections for processing

## 📊 Development Progress

- [x] Project setup & architecture
- [x] Basic UI components  
- [x] Document import (drag & drop)
- [ ] Directory analysis
- [ ] Basic keyword search
- [ ] RAG search with LLM
- [ ] Document summarization

## 🧪 Testing

```bash
npm test              # Run all tests
npm run test:frontend # Frontend tests only
npm run test:backend  # Backend tests only
```

## 📝 Documentation

See `DECISIONS.md` for architectural decisions and `docs/` for detailed documentation.