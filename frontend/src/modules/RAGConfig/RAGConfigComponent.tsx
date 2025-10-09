import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Grid,
  Alert,
  CircularProgress,
  Divider,
  Card,
  CardContent,
  Slider,
  InputAdornment,
  Tooltip,
  Chip,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon,
  RestartAlt as ResetIcon,
  Info as InfoIcon,
  Science as ScienceIcon,
  Search as SearchIcon,
  Psychology as PsychologyIcon,
} from '@mui/icons-material';
import { apiService } from '../../services/api';

interface RAGConfig {
  chunk_size: number;
  chunk_overlap: number;
  retrieve_k: number;
  rerank_k: number;
  llm_max_tokens: number;
  llm_temperature: number;
  llm_top_p: number;
}

interface ConfigResponse {
  config: RAGConfig;
  description: Record<string, string>;
}

export const RAGConfigComponent: React.FC = () => {
  const [config, setConfig] = useState<RAGConfig | null>(null);
  const [originalConfig, setOriginalConfig] = useState<RAGConfig | null>(null);
  const [descriptions, setDescriptions] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    setLoading(true);
    setError(null);
    try {
      const response: ConfigResponse = await apiService.getRAGConfig();
      setConfig(response.config);
      setOriginalConfig(response.config);
      setDescriptions(response.description);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to load config');
    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = (key: keyof RAGConfig, value: number) => {
    if (!config) return;
    setConfig({ ...config, [key]: value });
  };

  const saveConfig = async () => {
    if (!config) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await apiService.updateRAGConfig(config);
      setOriginalConfig(config);
      setSuccess('Configuration saved successfully!');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to save config');
    } finally {
      setSaving(false);
    }
  };

  const resetPipeline = async () => {
    setResetting(true);
    setError(null);
    setSuccess(null);
    try {
      await apiService.resetRAGPipeline();
      setSuccess('RAG pipeline reset with new configuration!');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to reset pipeline');
    } finally {
      setResetting(false);
    }
  };

  const hasChanges = () => {
    if (!config || !originalConfig) return false;
    return JSON.stringify(config) !== JSON.stringify(originalConfig);
  };

  if (loading) {
    return (
      <Paper sx={{ p: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading configuration...</Typography>
      </Paper>
    );
  }

  if (!config) {
    return (
      <Paper sx={{ p: 3 }}>
        <Alert severity="error">Failed to load RAG configuration</Alert>
      </Paper>
    );
  }

  return (
    <Box>
      {/* Header with Action Buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SettingsIcon color="primary" fontSize="small" />
          <Typography variant="subtitle1" fontWeight="medium">
            RAG Configuration
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            size="small"
            onClick={loadConfig}
            disabled={loading}
            startIcon={<RefreshIcon fontSize="small" />}
          >
            Reload
          </Button>

          <Button
            variant="contained"
            size="small"
            onClick={saveConfig}
            disabled={!hasChanges() || saving}
            startIcon={saving ? <CircularProgress size={14} /> : <SaveIcon fontSize="small" />}
            color="primary"
          >
            {saving ? 'Saving...' : 'Save'}
          </Button>

          <Button
            variant="contained"
            size="small"
            color="secondary"
            onClick={resetPipeline}
            disabled={resetting}
            startIcon={resetting ? <CircularProgress size={14} /> : <ResetIcon fontSize="small" />}
          >
            {resetting ? 'Resetting...' : 'Reset'}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      {hasChanges() && (
        <Alert severity="info" sx={{ mb: 3 }}>
          You have unsaved changes. Click "Save" to apply them.
        </Alert>
      )}

      {/* Configuration Controls in Single Horizontal Row */}
      <Box sx={{ mb: 2, width: '100%', overflowX: 'auto' }}>
  <Box sx={{ display: 'flex', flexDirection: 'row', alignItems: 'flex-end', gap: 1.5, width: '100%', flexWrap: 'nowrap', overflowX: 'auto' }}>
          {/* Chunk Size */}
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 200, minWidth: 200, maxWidth: 200, flexShrink: 0 }}>
            <ScienceIcon fontSize="small" color="primary" />
            <Typography variant="body2" fontWeight="medium">Chunk Size</Typography>
            <TextField
              size="small"
              type="number"
              value={config.chunk_size}
              onChange={(e) => handleConfigChange('chunk_size', parseInt(e.target.value) || 100)}
              sx={{ width: '200px', mt: 0.5 }}
              InputProps={{
                endAdornment: <InputAdornment position="end">chars</InputAdornment>,
              }}
            />
          </Box>
          {/* Overlap */}
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 200, minWidth: 200, maxWidth: 200, flexShrink: 0 }}>
            <ScienceIcon fontSize="small" color="primary" />
            <Typography variant="body2" fontWeight="medium">Overlap</Typography>
            <TextField
              size="small"
              type="number"
              value={config.chunk_overlap}
              onChange={(e) => handleConfigChange('chunk_overlap', parseInt(e.target.value) || 0)}
              sx={{ width: '200px', mt: 0.5 }}
              InputProps={{
                endAdornment: <InputAdornment position="end">chars</InputAdornment>,
              }}
            />
          </Box>
          {/* Retrieve K */}
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 200, minWidth: 200, maxWidth: 200, flexShrink: 0 }}>
            <SearchIcon fontSize="small" color="primary" />
            <Typography variant="body2" fontWeight="medium">Retrieve K</Typography>
            <TextField
              size="small"
              type="number"
              value={config.retrieve_k}
              onChange={(e) => handleConfigChange('retrieve_k', parseInt(e.target.value) || 1)}
              sx={{ width: '200px', mt: 0.5 }}
              InputProps={{
                endAdornment: <InputAdornment position="end">#</InputAdornment>,
              }}
            />
          </Box>
          {/* Rerank K */}
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 200, minWidth: 200, maxWidth: 200, flexShrink: 0 }}>
            <SearchIcon fontSize="small" color="primary" />
            <Typography variant="body2" fontWeight="medium">Rerank K</Typography>
            <TextField
              size="small"
              type="number"
              value={config.rerank_k}
              onChange={(e) => handleConfigChange('rerank_k', parseInt(e.target.value) || 1)}
              sx={{ width: '200px', mt: 0.5 }}
              InputProps={{
                endAdornment: <InputAdornment position="end">#</InputAdornment>,
              }}
            />
          </Box>
          {/* Max Tokens */}
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 200, minWidth: 200, maxWidth: 200, flexShrink: 0 }}>
            <PsychologyIcon fontSize="small" color="primary" />
            <Typography variant="body2" fontWeight="medium">Max Tokens</Typography>
            <TextField
              size="small"
              type="number"
              value={config.llm_max_tokens}
              onChange={(e) => handleConfigChange('llm_max_tokens', parseInt(e.target.value) || 1)}
              sx={{ width: '200px', mt: 0.5 }}
              InputProps={{
                endAdornment: <InputAdornment position="end">tokens</InputAdornment>,
              }}
            />
          </Box>
          {/* Temperature */}
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 200, minWidth: 200, maxWidth: 200, flexShrink: 0 }}>
            <PsychologyIcon fontSize="small" color="primary" />
            <Typography variant="body2" fontWeight="medium">Temperature</Typography>
            <Box sx={{ width: '200px', mt: 0.5, display: 'flex', alignItems: 'center' }}>
              <Slider
                size="small"
                value={config.llm_temperature}
                onChange={(_, value) => handleConfigChange('llm_temperature', value as number)}
                min={0.0}
                max={1.0}
                step={0.1}
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => `${value.toFixed(1)}`}
                sx={{ mr: 1 }}
              />
            </Box>
          </Box>
          {/* Top P */}
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 200, minWidth: 200, maxWidth: 200, flexShrink: 0 }}>
            <PsychologyIcon fontSize="small" color="primary" />
            <Typography variant="body2" fontWeight="medium">Top P</Typography>
            <Box sx={{ width: '200px', mt: 0.5, display: 'flex', alignItems: 'center' }}>
              <Slider
                size="small"
                value={config.llm_top_p}
                onChange={(_, value) => handleConfigChange('llm_top_p', value as number)}
                min={0.0}
                max={1.0}
                step={0.1}
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => `${value.toFixed(1)}`}
                sx={{ mr: 1 }}
              />
            </Box>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};