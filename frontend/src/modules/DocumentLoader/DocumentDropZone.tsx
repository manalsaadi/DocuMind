import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Paper,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  InsertDriveFile as FileIcon,
} from '@mui/icons-material';
import { useAppStore } from '../../stores/appStore';
import { apiService } from '../../services/api';
import { Document } from '../../types';

interface DocumentDropZoneProps {
  onFilesAdded?: (files: File[]) => void;
}

/**
 * Modular Document Drop Zone Component
 * Handles drag & drop file import with validation
 * 
 * Responsibilities:
 * - File drop validation
 * - File type filtering
 * - Visual feedback during drag operations
 * - Integration with document store
 */
export const DocumentDropZone: React.FC<DocumentDropZoneProps> = ({
  onFilesAdded = undefined,
}) => {
  const { setLoading, setError, isLoading, syncWithBackend } = useAppStore();

  const processFiles = useCallback(async (acceptedFiles: File[]) => {
    setLoading(true);
    setError(null);

    try {
      // Upload files to backend
      const uploadResponse = await apiService.uploadDocuments(acceptedFiles);
      console.log('✅ Upload successful:', uploadResponse);

      onFilesAdded?.(acceptedFiles);

      // Force sync with backend to ensure perfect state alignment
      await syncWithBackend();

      console.log('✅ Frontend-Backend sync completed');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to upload files to backend');
      console.error('Upload error:', error);
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError, onFilesAdded, syncWithBackend]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop: processFiles,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
    },
    maxFiles: 50,
    maxSize: 50 * 1024 * 1024, // 50MB per file
  });

  const getFileType = (filename: string): Document['type'] => {
    const extension = filename.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf': return 'pdf';
      case 'docx': return 'docx';
      case 'txt': return 'txt';
      case 'md': return 'md';
      default: return 'txt';
    }
  };

  return (
    <Box>
      <Paper
        {...getRootProps()}
        elevation={isDragActive ? 8 : 2}
        sx={{
          p: 4,
          textAlign: 'center',
          cursor: 'pointer',
          border: '2px dashed',
          borderColor: isDragReject
            ? 'error.main'
            : isDragActive
            ? 'primary.main'
            : 'grey.300',
          backgroundColor: isDragActive
            ? 'action.hover'
            : 'background.paper',
          transition: 'all 0.2s ease',
          '&:hover': {
            backgroundColor: 'action.hover',
            borderColor: 'primary.main',
          },
        }}
      >
        <input {...getInputProps()} />
        
        <Box sx={{ mb: 2 }}>
          {isDragActive ? (
            <UploadIcon sx={{ fontSize: 64, color: 'primary.main' }} />
          ) : (
            <FileIcon sx={{ fontSize: 64, color: 'text.secondary' }} />
          )}
        </Box>

        <Typography variant="subtitle1" gutterBottom>
          {isDragActive
            ? 'Drop your documents here'
            : 'Drop documents or click to browse'}
        </Typography>

        <Typography variant="caption" color="text.secondary" sx={{ mb: 1 }}>
          Supported formats: PDF, DOCX, TXT, MD
          <br />
          Maximum file size: 50MB
        </Typography>

        {isDragReject && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Some files are not supported. Please use PDF, DOCX, TXT, or MD files.
          </Alert>
        )}

        {isLoading && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>
              Processing files...
            </Typography>
            <LinearProgress />
          </Box>
        )}
      </Paper>
    </Box>
  );
};