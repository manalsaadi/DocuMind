/**
 * API Services Module
 * 
 * Handles all backend communication for DocuMind
 * Following modular architecture with clear separation of concerns
 */

import { Document } from '../types';

const API_BASE_URL = 'http://localhost:8000';

export interface UploadResponse {
  message: string;
  files: Array<{
    id: string;
    filename: string;
    size: number;
    status: string;
  }>;
}

export interface BackendDocument {
  id: string;
  filename: string;
  size: number;
  status: string;
}

export interface DocumentsListResponse {
  documents: BackendDocument[];
}

export interface SearchRequest {
  query: string;
}

export interface SearchResponse {
  query: string;
  results: Array<{
    document_id: string;
    filename: string;
    relevance_score: number;
    snippet: string;
  }>;
  total_results: number;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Upload multiple documents to the backend
   */
  async uploadDocuments(files: File[]): Promise<UploadResponse> {
    const formData = new FormData();
    
    files.forEach(file => {
      formData.append('files', file);
    });

    const response = await fetch(`${this.baseUrl}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get list of all documents from backend
   */
  async getDocuments(): Promise<DocumentsListResponse> {
    const response = await fetch(`${this.baseUrl}/api/documents`);

    if (!response.ok) {
      throw new Error(`Failed to fetch documents: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Delete a document by ID
   */
  async deleteDocument(documentId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/documents/${documentId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to delete document: ${response.statusText}`);
    }
  }

  /**
   * Search documents using RAG
   */
  async searchDocuments(query: string): Promise<SearchResponse> {
    const response = await fetch(`${this.baseUrl}/api/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`Search failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await fetch(`${this.baseUrl}/api/health`);
    
    if (!response.ok) {
      throw new Error('Backend health check failed');
    }

    return response.json();
  }

  /**
   * Convert backend document to frontend document format
   */
  backendToFrontendDocument(backendDoc: BackendDocument): Document {
    return {
      id: backendDoc.id,
      name: backendDoc.filename,
      path: backendDoc.filename,
      type: this.getFileType(backendDoc.filename),
      size: backendDoc.size,
      lastModified: new Date(), // Backend doesn't provide this yet
      isIndexed: backendDoc.status === 'processed',
    };
  }

  private getFileType(filename: string): Document['type'] {
    const extension = filename.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf': return 'pdf';
      case 'docx': return 'docx';
      case 'txt': return 'txt';
      case 'md': return 'md';
      default: return 'txt';
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();