import React, { useEffect } from 'react';
import {
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  InsertDriveFile as FileIcon,
  PictureAsPdf as PdfIcon,
  Description as DocxIcon,
  TextSnippet as TextIcon,
  Delete as DeleteIcon,
  CheckCircle as ProcessedIcon,
  Schedule as PendingIcon,
} from '@mui/icons-material';
import { Document } from '../../types';
import { useAppStore } from '../../stores/appStore';
import { apiService } from '../../services/api';

/**
 * Modular Document List Component
 * Displays imported documents with their status
 * 
 * Responsibilities:
 * - Display document metadata
 * - Show indexing status
 * - Handle document removal
 * - Sync with backend API
 * - File type icons
 */
export const DocumentList: React.FC = () => {
  const { documents, indexingProgress, setError, syncWithBackend } = useAppStore();

  // Fetch documents from backend on component mount
  useEffect(() => {
    console.log('🔍 DocumentList: Component mounted, syncing with backend...');
    syncWithBackend();
  }, [syncWithBackend]);

  const handleDeleteDocument = async (documentId: string) => {
    try {
      await apiService.deleteDocument(documentId);
      console.log('✅ Document deleted from backend:', documentId);
      
      // Sync with backend to ensure state consistency
      await syncWithBackend();
      console.log('✅ Frontend-Backend sync completed after delete');
    } catch (error) {
      setError('Failed to delete document');
      console.error('Error deleting document:', error);
    }
  };

  const getFileIcon = (type: Document['type']) => {
    switch (type) {
      case 'pdf': return <PdfIcon color="error" />;
      case 'docx': return <DocxIcon color="primary" />;
      case 'txt': return <TextIcon color="info" />;
      case 'md': return <TextIcon color="info" />;
      default: return <FileIcon />;
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (documents.length === 0) {
    return (
      <Box
        sx={{
          textAlign: 'center',
          py: 3,
          color: 'text.secondary',
          border: '2px dashed',
          borderColor: 'primary.light',
          borderRadius: 2,
          backgroundColor: 'primary.50',
        }}
      >
        <FileIcon sx={{ fontSize: 32, color: 'primary.main', mb: 1 }} />
        <Typography variant="subtitle1" gutterBottom sx={{ color: 'primary.main', fontWeight: 'bold' }}>
          No documents imported yet
        </Typography>
        <Typography variant="body2" sx={{ mb: 1, color: 'text.primary' }}>
          Upload some documents above to start asking questions about your content
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Supported formats: PDF, DOCX, TXT, MD • Max size: 50MB per file
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="subtitle1" gutterBottom sx={{ fontSize: '1rem' }}>
        Imported Documents ({documents.length})
      </Typography>
      
      {indexingProgress > 0 && indexingProgress < 100 && (
        <Box sx={{ mb: 1 }}>
          <Typography variant="caption" gutterBottom>
            Indexing documents... {Math.round(indexingProgress)}%
          </Typography>
          <LinearProgress
            variant="determinate"
            value={indexingProgress}
            sx={{ mb: 0.5 }}
          />
        </Box>
      )}

      <List>
        {documents.map((document) => (
          <ListItem
            key={document.id}
            divider
            sx={{
              bgcolor: document.isIndexed ? 'success.light' : 'background.paper',
              mb: 0.5,
              borderRadius: 1,
              py: 1,
            }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>
              {getFileIcon(document.type)}
            </ListItemIcon>
            
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2" noWrap fontWeight="medium">
                    {document.name}
                  </Typography>
                  <Chip
                    size="small"
                    label={document.type.toUpperCase()}
                    variant="outlined"
                    sx={{ fontSize: '0.7rem', height: 20 }}
                  />
                </Box>
              }
              secondary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.25 }}>
                  <Typography variant="caption">
                    {formatFileSize(document.size)}
                  </Typography>
                  <Typography variant="caption">
                    Modified: {document.lastModified.toLocaleDateString()}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
                    {document.isIndexed ? (
                      <>
                        <ProcessedIcon sx={{ fontSize: 14 }} color="success" />
                        <Typography variant="caption" color="success.main">
                          Processed
                        </Typography>
                      </>
                    ) : (
                      <>
                        <PendingIcon sx={{ fontSize: 14 }} color="warning" />
                        <Typography variant="caption" color="warning.main">
                          Pending
                        </Typography>
                      </>
                    )}
                  </Box>
                </Box>
              }
            />
            
            <ListItemSecondaryAction>
              <IconButton
                edge="end"
                aria-label="delete"
                onClick={() => handleDeleteDocument(document.id)}
                size="small"
              >
                <DeleteIcon sx={{ fontSize: 18 }} />
              </IconButton>
            </ListItemSecondaryAction>
          </ListItem>
        ))}
      </List>
    </Box>
  );
};