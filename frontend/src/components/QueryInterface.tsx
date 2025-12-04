import React, { useState } from 'react';
import {
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  Box,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Send as SendIcon,
  ExpandMore as ExpandMoreIcon,
  Psychology as ModelIcon,
  Router as RouterIcon,
  Speed as SpeedIcon
} from '@mui/icons-material';
import { useAPI } from '../hooks/useAPI';

interface RoutingResponse {
  selected_model: string;
  routing_method: string;
  endpoint: string;
  confidence_score: number;
  reasoning: string;
  estimated_cost: number;
  estimated_response_time: number;
  alternative_models: string[];
  routing_metadata: any;
  llm_response?: string;
  generation_time?: number;
}

const QueryInterface: React.FC = () => {
  const [query, setQuery] = useState('');
  const [priority, setPriority] = useState('medium');
  const [sourceEid, setSourceEid] = useState('10.1.0.1');
  const [preferredModel, setPreferredModel] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RoutingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const api = useAPI();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }
    
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const response = await api.routeQuery({
        query: query.trim(),
        priority,
        source_eid: sourceEid,
        preferred_model: preferredModel || undefined,
        context: {
          timestamp: new Date().toISOString(),
          user_interface: true
        }
      });
      
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to route query');
    } finally {
      setLoading(false);
    }
  };
  
  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };
  
  return (
    <Grid container spacing={3}>
      {/* Query Input Form */}
      <Grid size={{ xs: 12, lg: 6 }}>
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Query Routing Interface
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Submit queries to test the AI workload routing system with LISP and DNS-based routing.
          </Typography>

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Query"
              placeholder="Enter your AI query here..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              sx={{ mb: 3 }}
            />

            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid size={{ xs: 12, md: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Priority</InputLabel>
                  <Select
                    value={priority}
                    label="Priority"
                    onChange={(e) => setPriority(e.target.value)}
                  >
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Source EID"
                  value={sourceEid}
                  onChange={(e) => setSourceEid(e.target.value)}
                  placeholder="10.1.0.1"
                />
              </Grid>
            </Grid>

            <TextField
              fullWidth
              label="Preferred Model (Optional)"
              value={preferredModel}
              onChange={(e) => setPreferredModel(e.target.value)}
              placeholder="gpt-4, claude-3, etc."
              sx={{ mb: 3 }}
            />

            <Button
              type="submit"
              variant="contained"
              size="large"
              startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
              disabled={loading || !query.trim()}
              fullWidth
            >
              {loading ? 'Routing...' : 'Route Query'}
            </Button>
          </form>
        </Paper>
      </Grid>

      {/* Results */}
      <Grid size={{ xs: 12, lg: 6 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        {result && (
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Routing Result
            </Typography>
            
            {/* Summary Cards */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid size={{ xs: 12, md: 4 }}>
                <Card variant="outlined">
                  <CardContent sx={{ textAlign: 'center', py: 2 }}>
                    <ModelIcon color="primary" sx={{ fontSize: 32, mb: 1 }} />
                    <Typography variant="h6" color="primary">
                      {result.selected_model}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Selected Model
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 4 }}>
                <Card variant="outlined">
                  <CardContent sx={{ textAlign: 'center', py: 2 }}>
                    <RouterIcon color="secondary" sx={{ fontSize: 32, mb: 1 }} />
                    <Typography variant="h6" color="secondary">
                      {result.routing_method}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Routing Method
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 4 }}>
                <Card variant="outlined">
                  <CardContent sx={{ textAlign: 'center', py: 2 }}>
                    <SpeedIcon color="success" sx={{ fontSize: 32, mb: 1 }} />
                    <Typography variant="h6" color="success.main">
                      {result.estimated_response_time.toFixed(2)}s
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Est. Response Time
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
            
            {/* LLM Generated Response */}
            {result.llm_response && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ModelIcon color="primary" />
                  Generated Response from {result.selected_model}
                </Typography>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    backgroundColor: '#000000',
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 2,
                    maxHeight: '400px',
                    overflow: 'auto'
                  }}
                >
                  <Typography
                    variant="body2"
                    sx={{
                      whiteSpace: 'pre-wrap',
                      fontFamily: 'monospace',
                      fontSize: '0.9rem',
                      lineHeight: 1.6,
                      color: '#ffffff'
                    }}
                  >
                    {result.llm_response}
                  </Typography>
                </Paper>
                {result.generation_time !== undefined && (
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Generation time: {result.generation_time.toFixed(2)}s
                  </Typography>
                )}
              </Box>
            )}

            {/* Detailed Information */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Routing Details
              </Typography>
              <Box display="flex" alignItems="center" mb={1}>
                <Typography variant="body2" sx={{ mr: 1 }}>Confidence:</Typography>
                <Chip
                  label={`${(result.confidence_score * 100).toFixed(1)}%`}
                  color={getConfidenceColor(result.confidence_score)}
                  size="small"
                />
              </Box>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Endpoint:</strong> {result.endpoint}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Estimated Cost:</strong> ${result.estimated_cost.toFixed(6)}
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                <strong>Reasoning:</strong> {result.reasoning}
              </Typography>
            </Box>
            
            {/* Alternative Models */}
            {result.alternative_models.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Alternative Models
                </Typography>
                <Box display="flex" gap={1} flexWrap="wrap">
                  {result.alternative_models.map((model, index) => (
                    <Chip key={index} label={model} variant="outlined" size="small" />
                  ))}
                </Box>
              </Box>
            )}
            
            {/* Technical Details */}
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">Technical Details</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Query Analysis:</strong>
                  </Typography>
                  <Box sx={{ pl: 2, mb: 2 }}>
                    <Typography variant="body2">
                      • Type: {result.routing_metadata.query_analysis?.query_type || 'N/A'}
                    </Typography>
                    <Typography variant="body2">
                      • Complexity: {((result.routing_metadata.query_analysis?.complexity_score || 0) * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2">
                      • Estimated Tokens: {result.routing_metadata.query_analysis?.estimated_tokens || 'N/A'}
                    </Typography>
                  </Box>
                  
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>LISP Routing:</strong>
                  </Typography>
                  <Box sx={{ pl: 2, mb: 2 }}>
                    <Typography variant="body2">
                      • Used: {result.routing_metadata.lisp_routing?.used ? 'Yes' : 'No'}
                    </Typography>
                    <Typography variant="body2">
                      • Source EID: {result.routing_metadata.lisp_routing?.source_eid || 'N/A'}
                    </Typography>
                    <Typography variant="body2">
                      • Endpoint: {result.routing_metadata.lisp_routing?.endpoint || 'N/A'}
                    </Typography>
                  </Box>
                  
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>DNS Routing:</strong>
                  </Typography>
                  <Box sx={{ pl: 2, mb: 2 }}>
                    <Typography variant="body2">
                      • Used: {result.routing_metadata.dns_routing?.used ? 'Yes' : 'No'}
                    </Typography>
                    <Typography variant="body2">
                      • Service: {result.routing_metadata.dns_routing?.service_name || 'N/A'}
                    </Typography>
                    <Typography variant="body2">
                      • Record: {result.routing_metadata.dns_routing?.record_name || 'N/A'}
                    </Typography>
                  </Box>
                  
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Performance:</strong>
                  </Typography>
                  <Box sx={{ pl: 2 }}>
                    <Typography variant="body2">
                      • Processing Time: {result.routing_metadata.processing_time_ms?.toFixed(2) || 'N/A'} ms
                    </Typography>
                  </Box>
                </Box>
              </AccordionDetails>
            </Accordion>
          </Paper>
        )}
        
        {!result && !loading && (
          <Paper 
            elevation={1} 
            sx={{ 
              p: 4, 
              textAlign: 'center',
              border: '2px dashed',
              borderColor: 'divider',
              backgroundColor: 'background.default'
            }}
          >
            <ModelIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No Query Submitted
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Submit a query to see routing results and technical details.
            </Typography>
          </Paper>
        )}
      </Grid>
    </Grid>
  );
};

export default QueryInterface;