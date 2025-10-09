import React from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Container,
  AppBar,
  Toolbar,
  Typography,
  Box,
  Grid,
  Paper,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Memory as BrainIcon,
  Security as PrivacyIcon,
} from '@mui/icons-material';
import { DocumentDropZone } from './modules/DocumentLoader/DocumentDropZone';
import { DocumentList } from './modules/DocumentLoader/DocumentList';
import { SearchComponent } from './modules/Search/SearchComponent';
import { RAGConfigComponent } from './modules/RAGConfig/RAGConfigComponent';
import { useAppStore } from './stores/appStore';

/**
 * Main DocuMind Application Component
 * 
 * Architecture Decision: Start with core document import functionality
 * - Clean, privacy-focused UI
 * - Modular component structure
 * - Material-UI for consistent design
 * - Dark/Light theme support
 */
function App() {
  const [darkMode, setDarkMode] = React.useState(false);
  const { error } = useAppStore();

  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
      primary: {
        main: '#1976d2',
      },
      secondary: {
        main: '#dc004e',
      },
    },
  });

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      
      {/* Header */}
      <AppBar position="static" elevation={2} sx={{ background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)' }}>
        <Toolbar>
          <BrainIcon sx={{ mr: 2, fontSize: 28 }} />
          <Typography variant="h5" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            DocuMind
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PrivacyIcon sx={{ fontSize: 18 }} />
              <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                100% Local & Private
              </Typography>
            </Box>
            <FormControlLabel
              control={
                <Switch
                  checked={darkMode}
                  onChange={(e) => setDarkMode(e.target.checked)}
                  size="small"
                />
              }
              label={
                <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                  {darkMode ? 'Dark' : 'Light'}
                </Typography>
              }
              sx={{ ml: 1 }}
            />
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth="xl" sx={{ py: 1 }}>
        {/* Top Row - Main Functionality */}
        <Grid container spacing={2} sx={{ mb: 2 }}>
          {/* Left Panel - Document Import */}
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, boxShadow: 2, borderRadius: 2 }}>
              <Typography variant="h6" gutterBottom sx={{ mb: 2, fontWeight: 'bold', color: 'primary.main' }}>
                📁 Import Documents
              </Typography>
              <DocumentDropZone />
              
              {error && (
                <Box sx={{ mt: 2, p: 1, bgcolor: 'error.light', borderRadius: 1 }}>
                  <Typography variant="body2" color="error">{error}</Typography>
                </Box>
              )}
            </Paper>
          </Grid>

          {/* Middle Panel - Document List */}
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, boxShadow: 2, borderRadius: 2 }}>
              <Typography variant="h6" gutterBottom sx={{ mb: 2, fontWeight: 'bold', color: 'primary.main' }}>
                📋 Document Library
              </Typography>
              <DocumentList />
            </Paper>
          </Grid>

          {/* Right Panel - Search (Prominent) */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, boxShadow: 3, borderRadius: 2, border: 2, borderColor: 'primary.main' }}>
              <Typography variant="h4" gutterBottom sx={{ mb: 2, fontWeight: 'bold', color: 'primary.main' }}>
                ❓ Ask Questions
              </Typography>
              <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
                Ask questions about your documents and get AI-powered answers with source references.
              </Typography>
              <SearchComponent />
            </Paper>
          </Grid>
        </Grid>

        {/* Bottom Section - RAG Configuration (Compact) */}
        <Box sx={{ mt: 0.5, pt: 0.5, borderTop: 1, borderColor: 'divider' }}>
          <Typography variant="body1" gutterBottom sx={{ textAlign: 'center', mb: 0.5, color: 'text.secondary', fontWeight: 'medium' }}>
            ⚙️ Advanced Settings
          </Typography>
          <Grid container spacing={1}>
            <Grid item xs={12}>
              <Paper sx={{ p: 1.5, boxShadow: 1 }}>
                <RAGConfigComponent />
              </Paper>
            </Grid>
          </Grid>
        </Box>

        {/* Privacy Notice */}
        <Box sx={{ mt: 1, textAlign: 'center', p: 1, bgcolor: 'background.paper', borderRadius: 1, boxShadow: 1 }}>
          <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, fontWeight: 'medium' }}>
            🔒 <span style={{ fontWeight: 'bold' }}>Privacy First:</span> Your documents are processed locally and never leave your device
          </Typography>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;