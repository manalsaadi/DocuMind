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
- **Orchestrator Module**: Coordinates RAG pipeline (coming next)
- **Data Manager Module**: Local state management (Zustand)

### Core RAG Modules (Phase 2)
- **Document Loader**: Multi-format file processing
- **Text Chunker**: Semantic text splitting
- **Embedding Module**: Vector generation
- **Vector DB Module**: ChromaDB integration
- **LLM Module**: Qwen 3 4B integration

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