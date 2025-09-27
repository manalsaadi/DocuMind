// Shared TypeScript interfaces for the entire application

export interface Document {
  id: string;
  name: string;
  path: string;
  type: 'pdf' | 'docx' | 'txt' | 'md';
  size: number;
  lastModified: Date;
  content?: string;
  summary?: string;
  isIndexed: boolean;
}

export interface DocumentChunk {
  id: string;
  documentId: string;
  content: string;
  startIndex: number;
  endIndex: number;
  embedding?: number[];
}

export interface SearchResult {
  document: Document;
  chunks: DocumentChunk[];
  relevanceScore: number;
  summary: string;
}

export interface Query {
  text: string;
  type: 'keyword' | 'semantic' | 'rag';
  filters?: {
    documentTypes?: string[];
    dateRange?: {
      start: Date;
      end: Date;
    };
  };
}

export interface AppState {
  documents: Document[];
  isLoading: boolean;
  error: string | null;
  searchResults: SearchResult[];
  indexingProgress: number;
}

export interface RAGConfig {
  embeddingModel: string;
  llmModel: string;
  chunkSize: number;
  chunkOverlap: number;
  maxResults: number;
}