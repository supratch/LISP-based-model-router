import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AppBar, Toolbar, Typography, Container, Box } from '@mui/material';
import Dashboard from './components/Dashboard';
import QueryInterface from './components/QueryInterface';
import MonitoringDashboard from './components/MonitoringDashboard';
import ModelManagement from './components/ModelManagement';
import Navigation from './components/Navigation';
import { PacketViewer } from './components/PacketViewer';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <AppBar position="static" elevation={0}>
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                AI Workload Routing System
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.7 }}>
                Enterprise LISP & DNS Routing
              </Typography>
            </Toolbar>
          </AppBar>
          
          <Navigation />
          
          <Container maxWidth="xl" sx={{ mt: 2, mb: 2 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/query" element={<QueryInterface />} />
              <Route path="/monitoring" element={<MonitoringDashboard />} />
              <Route path="/models" element={<ModelManagement />} />
              <Route path="/packets" element={<PacketViewer />} />
            </Routes>
          </Container>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
