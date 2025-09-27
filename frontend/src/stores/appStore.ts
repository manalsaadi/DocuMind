import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { Document, SearchResult, AppState, RAGConfig } from '../types';

// Modular store following single responsibility principle
interface AppStore extends AppState {
  // Document Management
  addDocuments: (documents: Document[]) => void;
  setDocuments: (documents: Document[]) => void; // For syncing with backend
  syncWithBackend: () => Promise<void>; // Force sync with backend
  removeDocument: (documentId: string) => void;
  updateDocument: (documentId: string, updates: Partial<Document>) => void;
  
  // Search
  setSearchResults: (results: SearchResult[]) => void;
  clearSearchResults: () => void;
  
  // UI State
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  setIndexingProgress: (progress: number) => void;
  
  // Configuration
  ragConfig: RAGConfig;
  updateRAGConfig: (config: Partial<RAGConfig>) => void;
}

export const useAppStore = create<AppStore>()(
  subscribeWithSelector((set, get) => ({
    // Initial State
    documents: [],
    isLoading: false,
    error: null,
    searchResults: [],
    indexingProgress: 0,
    ragConfig: {
      embeddingModel: 'all-mpnet-base-v2',
      llmModel: 'qwen3:4b',
      chunkSize: 1000,
      chunkOverlap: 200,
      maxResults: 5,
    },

    // Document Management Actions
    addDocuments: (documents: Document[]) =>
      set((state) => {
        // Avoid duplicates by checking IDs
        const existingIds = new Set(state.documents.map(doc => doc.id));
        const newDocuments = documents.filter(doc => !existingIds.has(doc.id));
        return {
          documents: [...state.documents, ...newDocuments],
        };
      }),

    setDocuments: (documents: Document[]) =>
      set({ documents }),

    syncWithBackend: async () => {
      const { setLoading, setError } = get();
      setLoading(true);
      try {
        // Import apiService dynamically to avoid circular imports
        const { apiService } = await import('../services/api');
        const response = await apiService.getDocuments();
        const backendDocuments = response.documents.map(doc => 
          apiService.backendToFrontendDocument(doc)
        );
        set({ documents: backendDocuments });
        setError(null);
      } catch (error) {
        setError('Failed to sync with backend');
        console.error('Backend sync error:', error);
      } finally {
        setLoading(false);
      }
    },

    removeDocument: (documentId: string) =>
      set((state) => ({
        documents: state.documents.filter((doc) => doc.id !== documentId),
      })),

    updateDocument: (documentId: string, updates: Partial<Document>) =>
      set((state) => ({
        documents: state.documents.map((doc) =>
          doc.id === documentId ? { ...doc, ...updates } : doc
        ),
      })),

    // Search Actions
    setSearchResults: (results: SearchResult[]) =>
      set({ searchResults: results }),

    clearSearchResults: () => set({ searchResults: [] }),

    // UI State Actions
    setLoading: (isLoading: boolean) => set({ isLoading }),

    setError: (error: string | null) => set({ error }),

    setIndexingProgress: (progress: number) => 
      set({ indexingProgress: Math.max(0, Math.min(100, progress)) }),

    // Configuration Actions
    updateRAGConfig: (config: Partial<RAGConfig>) =>
      set((state) => ({
        ragConfig: { ...state.ragConfig, ...config },
      })),
  }))
);

// Selectors for optimized re-renders
export const useDocuments = () => useAppStore((state) => state.documents);
export const useSearchResults = () => useAppStore((state) => state.searchResults);
export const useLoading = () => useAppStore((state) => state.isLoading);
export const useError = () => useAppStore((state) => state.error);
export const useIndexingProgress = () => useAppStore((state) => state.indexingProgress);
export const useRAGConfig = () => useAppStore((state) => state.ragConfig);