import React, { useState } from 'react';
import {
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Chip,
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  QuestionAnswer as QuestionIcon,
} from '@mui/icons-material';
import { useAppStore } from '../../stores/appStore';
import { apiService } from '../../services/api';

interface SearchResult {
  document_id: string;
  filename: string;
  relevance_score: number;
  snippet: string;
  chunk_text: string;
}

interface SearchResponse {
  query: string;
  answer?: string; // Only present in RAG responses
  results: SearchResult[];
  total_results: number;
  pipeline_used: boolean;
  fallback?: string; // Only present in fallback responses
}

export const SearchComponent: React.FC = () => {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  const { documents } = useAppStore();

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    setSearchError(null);
    setSearchResponse(null);

    try {
      const response = await apiService.searchDocuments(query.trim());
      setSearchResponse(response);
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : 'Search failed');
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSearch();
    }
  };

  return (
    <Paper sx={{ p: 3, mt: 2 }}>
      <Typography variant="h5" gutterBottom sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <QuestionIcon sx={{ mr: 1 }} />
        Ask Questions
      </Typography>

      {/* Search Input */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <TextField
          fullWidth
          multiline
          rows={2}
          placeholder="Ask a question about your documents..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isSearching}
          variant="outlined"
        />
        <Button
          variant="contained"
          onClick={handleSearch}
          disabled={!query.trim() || isSearching || documents.length === 0}
          sx={{ minWidth: 120, height: 'fit-content', alignSelf: 'flex-end' }}
          startIcon={isSearching ? <CircularProgress size={20} /> : <SearchIcon />}
        >
          {isSearching ? 'Searching...' : 'Ask'}
        </Button>
      </Box>

      {/* No documents warning */}
      {documents.length === 0 && (
        <Alert severity="info" sx={{ mb: 1, py: 1 }}>
          <Typography variant="body2">
            Upload some documents first to start asking questions.
          </Typography>
        </Alert>
      )}

      {/* Search Error */}
      {searchError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {searchError}
        </Alert>
      )}

      {/* Search Results */}
      {searchResponse && (
        <Box>
          <Divider sx={{ mb: 2 }} />

          {/* Answer Section */}
          {searchResponse.answer && (
            <Card sx={{ mb: 2, bgcolor: 'primary.light' }}>
              <CardContent sx={{ py: 2 }}>
                <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <QuestionIcon sx={{ mr: 1, fontSize: 20 }} />
                  Answer
                </Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {searchResponse.answer}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Chip
                    size="small"
                    label={`Found in ${searchResponse.total_results} document${searchResponse.total_results !== 1 ? 's' : ''}`}
                    color="primary"
                    variant="outlined"
                  />
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Fallback message if no RAG answer */}
          {!searchResponse.answer && searchResponse.fallback && (
            <Alert severity="info" sx={{ mb: 2 }}>
              RAG search unavailable, showing text-based results.
            </Alert>
          )}

          {/* Source Documents */}
          {searchResponse.results.length > 0 && (
            <Box>
              <Typography variant="subtitle1" gutterBottom sx={{ fontSize: '1rem' }}>
                Source Documents
              </Typography>
              {searchResponse.results.map((result, index) => (
                <Card key={index} sx={{ mb: 1 }}>
                  <CardContent sx={{ py: 1.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 0.5 }}>
                      <Typography variant="subtitle2" fontWeight="bold" sx={{ fontSize: '0.9rem' }}>
                        {result.filename}
                      </Typography>
                      <Chip
                        size="small"
                        label={`Score: ${(result.relevance_score * 100).toFixed(1)}%`}
                        color="secondary"
                        variant="outlined"
                      />
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
                      {result.snippet}
                    </Typography>
                    <Typography variant="caption" sx={{ fontStyle: 'italic' }}>
                      Document ID: {result.document_id}
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}

          {/* Pipeline Info */}
          <Box sx={{ mt: 1, p: 0.5, bgcolor: 'grey.100', borderRadius: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Search powered by {searchResponse.pipeline_used ? 'RAG Pipeline' : 'Text Search'}
            </Typography>
          </Box>
        </Box>
      )}
    </Paper>
  );
};