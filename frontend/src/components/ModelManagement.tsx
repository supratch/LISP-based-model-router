import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Box,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  IconButton,
  Tooltip,
  Alert
} from '@mui/material';
import {
  Psychology as ModelIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  TrendingUp as PerformanceIcon,
  Speed as SpeedIcon,
  AttachMoney as CostIcon
} from '@mui/icons-material';
import { useAPI } from '../hooks/useAPI';

interface Model {
  name: string;
  endpoint: string;
  model_id: string;
  available: boolean;
  current_load: number;
  max_tokens: number;
  cost_per_token: number;
  avg_response_time: number;
  rate_limit: number;
  current_requests: number;
  capabilities: { [key: string]: string };
}

interface ConfigDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (config: any) => void;
}

const ConfigDialog: React.FC<ConfigDialogProps> = ({ open, onClose, onSave }) => {
  const [config, setConfig] = useState({
    capability: 0.4,
    load: 0.3,
    cost: 0.2,
    response_time: 0.1
  });
  
  const handleSave = () => {
    onSave({ load_balancing_weights: config });
    onClose();
  };
  
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Load Balancing Configuration</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Adjust the weights for different factors in model selection. All weights should sum to 1.0.
          </Typography>
          
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Capability Weight"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.1 }}
                value={config.capability}
                onChange={(e) => setConfig({ ...config, capability: parseFloat(e.target.value) })}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Load Weight"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.1 }}
                value={config.load}
                onChange={(e) => setConfig({ ...config, load: parseFloat(e.target.value) })}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Cost Weight"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.1 }}
                value={config.cost}
                onChange={(e) => setConfig({ ...config, cost: parseFloat(e.target.value) })}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Response Time Weight"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.1 }}
                value={config.response_time}
                onChange={(e) => setConfig({ ...config, response_time: parseFloat(e.target.value) })}
              />
            </Grid>
          </Grid>
          
          <Alert 
            severity={Math.abs((config.capability + config.load + config.cost + config.response_time) - 1.0) < 0.01 ? 'success' : 'warning'} 
            sx={{ mt: 2 }}
          >
            Total weight: {(config.capability + config.load + config.cost + config.response_time).toFixed(2)}
            {Math.abs((config.capability + config.load + config.cost + config.response_time) - 1.0) >= 0.01 && 
              ' (should sum to 1.0)'}
          </Alert>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button 
          onClick={handleSave} 
          variant="contained"
          disabled={Math.abs((config.capability + config.load + config.cost + config.response_time) - 1.0) >= 0.01}
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const ModelManagement: React.FC = () => {
  const [models, setModels] = useState<{ [key: string]: Model }>({});
  const [loading, setLoading] = useState(true);
  const [configOpen, setConfigOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const api = useAPI();
  
  useEffect(() => {
    fetchModels();
    const interval = setInterval(fetchModels, 10000); // Refresh every 10 seconds
    
    return () => clearInterval(interval);
  }, []);
  
  const fetchModels = async () => {
    try {
      const response = await api.getModels();
      setModels(response.models);
    } catch (error) {
      console.error('Failed to fetch models:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleConfigSave = async (config: any) => {
    try {
      await api.updateConfiguration('llm', config);
      setSuccessMessage('Configuration updated successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      console.error('Failed to update configuration:', error);
    }
  };
  
  const getStatusColor = (available: boolean, load: number) => {
    if (!available) return 'error';
    if (load > 0.8) return 'warning';
    return 'success';
  };
  
  const getStatusLabel = (available: boolean, load: number) => {
    if (!available) return 'Offline';
    if (load > 0.8) return 'High Load';
    return 'Available';
  };
  
  const getCapabilityColor = (capability: string) => {
    switch (capability.toLowerCase()) {
      case 'excellent': return 'success';
      case 'good': return 'primary';
      case 'fair': return 'warning';
      case 'poor': return 'error';
      default: return 'default';
    }
  };
  
  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>Loading models...</Typography>
      </Box>
    );
  }
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Model Management
        </Typography>
        <Box>
          <Tooltip title="Refresh models">
            <IconButton onClick={fetchModels}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            onClick={() => setConfigOpen(true)}
            sx={{ ml: 1 }}
          >
            Configure
          </Button>
        </Box>
      </Box>
      
      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {successMessage}
        </Alert>
      )}
      
      {/* Model Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {Object.entries(models).map(([modelName, model]) => (
          <Grid size={{ xs: 12, md: 6, lg: 4 }} key={modelName}>
            <Card elevation={2}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                  <Box display="flex" alignItems="center">
                    <ModelIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6">{model.name}</Typography>
                  </Box>
                  <Chip
                    label={getStatusLabel(model.available, model.current_load)}
                    color={getStatusColor(model.available, model.current_load)}
                    size="small"
                  />
                </Box>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {model.endpoint}
                </Typography>

                <Box sx={{ mt: 2 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Typography variant="body2">Load</Typography>
                    <Typography variant="body2">{(model.current_load * 100).toFixed(1)}%</Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={model.current_load * 100}
                    color={model.current_load > 0.8 ? 'warning' : 'primary'}
                    sx={{ height: 6, borderRadius: 3 }}
                  />
                </Box>

                <Grid container spacing={1} sx={{ mt: 2 }}>
                  <Grid size={4}>
                    <Box textAlign="center">
                      <SpeedIcon fontSize="small" color="action" />
                      <Typography variant="caption" display="block">
                        {model.avg_response_time}s
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid size={4}>
                    <Box textAlign="center">
                      <CostIcon fontSize="small" color="action" />
                      <Typography variant="caption" display="block">
                        ${model.cost_per_token.toFixed(6)}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid size={4}>
                    <Box textAlign="center">
                      <PerformanceIcon fontSize="small" color="action" />
                      <Typography variant="caption" display="block">
                        {model.current_requests}/{model.rate_limit}
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      
      {/* Detailed Model Table */}
      <Paper elevation={2}>
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Model Details & Capabilities
          </Typography>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Model</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Load</TableCell>
                <TableCell>Response Time</TableCell>
                <TableCell>Cost/Token</TableCell>
                <TableCell>Rate Limit</TableCell>
                <TableCell>Capabilities</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(models).map(([modelName, model]) => (
                <TableRow key={modelName}>
                  <TableCell>
                    <Box>
                      <Typography variant="subtitle2">{model.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {model.model_id}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={getStatusLabel(model.available, model.current_load)}
                      color={getStatusColor(model.available, model.current_load)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ width: 100 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={model.current_load * 100}
                        color={model.current_load > 0.8 ? 'warning' : 'primary'}
                        sx={{ height: 6, borderRadius: 3 }}
                      />
                      <Typography variant="caption">
                        {(model.current_load * 100).toFixed(1)}%
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{model.avg_response_time}s</TableCell>
                  <TableCell>${model.cost_per_token.toFixed(6)}</TableCell>
                  <TableCell>{model.current_requests}/{model.rate_limit}/min</TableCell>
                  <TableCell>
                    <Box display="flex" gap={0.5} flexWrap="wrap">
                      {Object.entries(model.capabilities).slice(0, 3).map(([capability, level]) => (
                        <Chip
                          key={capability}
                          label={`${capability}: ${level}`}
                          color={getCapabilityColor(level)}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                      {Object.entries(model.capabilities).length > 3 && (
                        <Chip
                          label={`+${Object.entries(model.capabilities).length - 3} more`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
      
      {/* Configuration Dialog */}
      <ConfigDialog
        open={configOpen}
        onClose={() => setConfigOpen(false)}
        onSave={handleConfigSave}
      />
    </Box>
  );
};

export default ModelManagement;