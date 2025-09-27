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
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <BrainIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            DocuMind
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PrivacyIcon sx={{ fontSize: 16 }} />
            <Typography variant="caption">
              100% Local Processing
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={darkMode}
                  onChange={(e) => setDarkMode(e.target.checked)}
                />
              }
              label="Dark"
              sx={{ ml: 2 }}
            />
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Grid container spacing={4}>
          {/* Left Panel - Document Import */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
                Import Documents
              </Typography>
              <DocumentDropZone />
              
              {error && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'error.light', borderRadius: 1 }}>
                  <Typography color="error">{error}</Typography>
                </Box>
              )}
            </Paper>
          </Grid>

          {/* Right Panel - Document List */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <DocumentList />
            </Paper>
          </Grid>
        </Grid>

        {/* Privacy Notice */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            🔒 Your documents are processed locally and never leave your device
          </Typography>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;