import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Tooltip
} from '@mui/material';
import {
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Refresh as RefreshIcon,
  CloudDownload as CloudDownloadIcon
} from '@mui/icons-material';

interface PacketMetadata {
  workload_type: string;
  model_name: string;
  query_hash: string;
  payload_size: number;
}

interface PacketHeader {
  src_ip: string;
  dst_ip: string;
  src_port?: number;
  dst_port?: number;
}

interface LISPPacket {
  packet_id: string;
  timestamp: number;
  outer_header: PacketHeader;
  inner_header: PacketHeader;
  metadata: PacketMetadata;
}

interface PacketStats {
  total_packets: number;
  total_bytes: number;
  packets_by_model: Record<string, number>;
  recent_packets: number;
  avg_packet_size: number;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api/v1';
const AUTH_TOKEN = 'test'; // In production, use proper authentication

export const PacketViewer: React.FC = () => {
  const [packets, setPackets] = useState<LISPPacket[]>([]);
  const [stats, setStats] = useState<PacketStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPacket, setSelectedPacket] = useState<LISPPacket | null>(null);
  const [visualizationOpen, setVisualizationOpen] = useState(false);
  const [visualization, setVisualization] = useState<string>('');
  const [downloadCount, setDownloadCount] = useState(10);

  const fetchPackets = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/packets/recent?count=20`, {
        headers: {
          'Authorization': `Bearer ${AUTH_TOKEN}`
        }
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setPackets(data.packets || []);
    } catch (err) {
      setError('Failed to fetch packets');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/packets/stats`, {
        headers: {
          'Authorization': `Bearer ${AUTH_TOKEN}`
        }
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setStats(data.stats || null);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  useEffect(() => {
    fetchPackets();
    fetchStats();
    const interval = setInterval(() => {
      fetchPackets();
      fetchStats();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDownloadPCAP = async (count: number) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/v1/packets/download/pcap?count=${count}`,
        {
          headers: {
            'Authorization': 'Bearer test'
          }
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to download PCAP');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `lisp_packets_${new Date().toISOString().replace(/[:.]/g, '-')}.pcap`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Failed to download PCAP file');
      console.error(err);
    }
  };

  const handleDownloadSinglePCAP = async (packetId: string) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/v1/packets/${packetId}/download/pcap`,
        {
          headers: {
            'Authorization': 'Bearer test'
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to download PCAP');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `lisp_packet_${packetId}.pcap`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Failed to download PCAP file');
      console.error(err);
    }
  };

  const handleViewPacket = async (packet: LISPPacket) => {
    setSelectedPacket(packet);
    try {
      const response = await fetch(`${API_BASE_URL}/packets/${packet.packet_id}`, {
        headers: {
          'Authorization': `Bearer ${AUTH_TOKEN}`
        }
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setVisualization(data.visualization || '');
      setVisualizationOpen(true);
    } catch (err) {
      setError('Failed to fetch packet visualization');
      console.error(err);
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  const getWorkloadColor = (workload: string) => {
    const colors: Record<string, "primary" | "secondary" | "success" | "warning" | "error" | "info"> = {
      'code_generation': 'primary',
      'creative_writing': 'secondary',
      'math_computation': 'success',
      'summarization': 'info',
      'translation': 'warning',
      'general': 'default' as any
    };
    return colors[workload] || 'default';
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        LISP Packet Viewer
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Statistics Section */}
      {stats && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Packet Statistics
          </Typography>
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Total Packets
              </Typography>
              <Typography variant="h5">{stats.total_packets}</Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Total Bytes
              </Typography>
              <Typography variant="h5">
                {(stats.total_bytes / 1024).toFixed(2)} KB
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Avg Packet Size
              </Typography>
              <Typography variant="h5">
                {stats.avg_packet_size.toFixed(0)} bytes
              </Typography>
            </Box>
          </Box>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Packets by Model:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {Object.entries(stats.packets_by_model).map(([model, count]) => (
                <Chip
                  key={model}
                  label={`${model}: ${count}`}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        </Paper>
      )}

      {/* Download Section */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Download PCAP Files
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Download LISP packets as PCAP files for analysis in Wireshark or other network tools.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            label="Number of Packets"
            type="number"
            value={downloadCount}
            onChange={(e) => setDownloadCount(Math.max(1, Math.min(100, parseInt(e.target.value) || 10)))}
            size="small"
            sx={{ width: 150 }}
          />
          <Button
            variant="contained"
            startIcon={<CloudDownloadIcon />}
            onClick={() => handleDownloadPCAP(downloadCount)}
          >
            Download PCAP
          </Button>
          <Typography variant="caption" color="text.secondary">
            (Max 100 packets)
          </Typography>
        </Box>
      </Paper>

      {/* Packets Table */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Recent Packets
          </Typography>
          <IconButton onClick={fetchPackets} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Box>

        {loading && packets.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Packet ID</TableCell>
                  <TableCell>Model</TableCell>
                  <TableCell>Workload</TableCell>
                  <TableCell>EID Route</TableCell>
                  <TableCell>RLOC Route</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Timestamp</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {packets.map((packet) => (
                  <TableRow key={packet.packet_id} hover>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {packet.packet_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={packet.metadata.model_name}
                        size="small"
                        color="primary"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={packet.metadata.workload_type}
                        size="small"
                        color={getWorkloadColor(packet.metadata.workload_type)}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption" fontFamily="monospace">
                        {packet.inner_header.src_ip} → {packet.inner_header.dst_ip}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption" fontFamily="monospace">
                        {packet.outer_header.src_ip} → {packet.outer_header.dst_ip}
                      </Typography>
                    </TableCell>
                    <TableCell>{packet.metadata.payload_size} B</TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {formatTimestamp(packet.timestamp)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={() => handleViewPacket(packet)}
                        >
                          <ViewIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Download PCAP">
                        <IconButton
                          size="small"
                          onClick={() => handleDownloadSinglePCAP(packet.packet_id)}
                        >
                          <DownloadIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Visualization Dialog */}
      <Dialog
        open={visualizationOpen}
        onClose={() => setVisualizationOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Packet Visualization: {selectedPacket?.packet_id}
        </DialogTitle>
        <DialogContent>
          <Box
            component="pre"
            sx={{
              fontFamily: 'monospace',
              fontSize: '0.85rem',
              backgroundColor: '#000000',
              color: '#ffffff',
              p: 2,
              borderRadius: 1,
              overflow: 'auto'
            }}
          >
            {visualization}
          </Box>
        </DialogContent>
        <DialogActions>
          {selectedPacket && (
            <Button
              startIcon={<DownloadIcon />}
              onClick={() => handleDownloadSinglePCAP(selectedPacket.packet_id)}
            >
              Download PCAP
            </Button>
          )}
          <Button onClick={() => setVisualizationOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

