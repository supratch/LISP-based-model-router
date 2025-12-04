import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  Alert,
  Tabs,
  Tab
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as HealthyIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  BarChart,
  Bar,
  Area,
  AreaChart
} from 'recharts';
import { useAPI } from '../hooks/useAPI';

interface Alert {
  id: string;
  severity: string;
  title: string;
  description: string;
  timestamp: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`monitoring-tabpanel-${index}`}
      aria-labelledby={`monitoring-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const MonitoringDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const api = useAPI();
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsData] = await Promise.all([
          api.getStats()
        ]);
        setStats(statsData);
        
        // Mock alerts for demo
        setAlerts([
          {
            id: '1',
            severity: 'warning',
            title: 'High Response Time',
            description: 'Average response time exceeded 3 seconds',
            timestamp: new Date().toISOString()
          }
        ]);
      } catch (error) {
        console.error('Failed to fetch monitoring data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 15000); // Refresh every 15 seconds
    
    return () => clearInterval(interval);
  }, [api]);
  
  // Mock performance data
  const performanceData = [
    { time: '10:00', cpu: 45, memory: 62, queries: 120, errors: 2 },
    { time: '10:05', cpu: 52, memory: 65, queries: 145, errors: 1 },
    { time: '10:10', cpu: 48, memory: 68, queries: 135, errors: 0 },
    { time: '10:15', cpu: 41, memory: 64, queries: 150, errors: 3 },
    { time: '10:20', cpu: 55, memory: 70, queries: 128, errors: 1 },
    { time: '10:25', cpu: 43, memory: 66, queries: 162, errors: 0 }
  ];
  
  const responseTimeData = [
    { time: '10:00', gpt4: 2.1, claude3: 1.8, average: 1.95 },
    { time: '10:05', gpt4: 1.9, claude3: 1.7, average: 1.8 },
    { time: '10:10', gpt4: 2.3, claude3: 2.0, average: 2.15 },
    { time: '10:15', gpt4: 2.0, claude3: 1.6, average: 1.8 },
    { time: '10:20', gpt4: 1.8, claude3: 1.9, average: 1.85 },
    { time: '10:25', gpt4: 2.2, claude3: 1.5, average: 1.85 }
  ];
  
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'info';
      default: return 'default';
    }
  };
  
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <ErrorIcon />;
      case 'warning': return <WarningIcon />;
      case 'info': return <HealthyIcon />;
      default: return <HealthyIcon />;
    }
  };
  
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>Loading monitoring data...</Typography>
      </Box>
    );
  }
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Monitoring
      </Typography>
      
      {/* Active Alerts */}
      {alerts.length > 0 && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {alerts.map((alert) => (
            <Grid size={12} key={alert.id}>
              <Alert
                severity={getSeverityColor(alert.severity) as any}
                icon={getSeverityIcon(alert.severity)}
              >
                <Box>
                  <Typography variant="subtitle1">{alert.title}</Typography>
                  <Typography variant="body2">{alert.description}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(alert.timestamp).toLocaleString()}
                  </Typography>
                </Box>
              </Alert>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Monitoring Tabs */}
      <Paper elevation={2}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="monitoring tabs">
            <Tab label="System Performance" />
            <Tab label="Model Metrics" />
            <Tab label="Network & Routing" />
            <Tab label="Alert History" />
          </Tabs>
        </Box>

        {/* System Performance Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            {/* Resource Usage */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Resource Usage
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={performanceData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Area type="monotone" dataKey="cpu" stackId="1" stroke="#8884d8" fill="#8884d8" name="CPU %" />
                      <Area type="monotone" dataKey="memory" stackId="2" stroke="#82ca9d" fill="#82ca9d" name="Memory %" />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            {/* Query Volume and Errors */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Query Volume & Errors
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={performanceData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis yAxisId="left" orientation="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <Tooltip />
                      <Legend />
                      <Bar yAxisId="left" dataKey="queries" fill="#8884d8" name="Queries" />
                      <Bar yAxisId="right" dataKey="errors" fill="#ff7300" name="Errors" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            
            {/* Current Resource Status */}
            <Grid size={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Current System Status
                  </Typography>
                  <Grid container spacing={3}>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <Typography variant="body2" gutterBottom>CPU Usage</Typography>
                      <LinearProgress
                        variant="determinate"
                        value={stats?.system_stats?.cpu_usage_percent || 45}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        {stats?.system_stats?.cpu_usage_percent || 45}%
                      </Typography>
                    </Grid>

                    <Grid size={{ xs: 12, md: 4 }}>
                      <Typography variant="body2" gutterBottom>Memory Usage</Typography>
                      <LinearProgress
                        variant="determinate"
                        value={stats?.system_stats?.memory_usage_percent || 65}
                        color="warning"
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        {stats?.system_stats?.memory_usage_percent || 65}%
                      </Typography>
                    </Grid>

                    <Grid size={{ xs: 12, md: 4 }}>
                      <Typography variant="body2" gutterBottom>Network Load</Typography>
                      <LinearProgress
                        variant="determinate"
                        value={35}
                        color="success"
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="body2" sx={{ mt: 1 }}>35%</Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Model Metrics Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            {/* Response Time Comparison */}
            <Grid size={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Model Response Times
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={responseTimeData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="gpt4" stroke="#8884d8" name="GPT-4" />
                      <Line type="monotone" dataKey="claude3" stroke="#82ca9d" name="Claude-3" />
                      <Line type="monotone" dataKey="average" stroke="#ff7300" strokeDasharray="5 5" name="Average" />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            {/* Model Status Table */}
            <Grid size={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Model Status Overview
                  </Typography>
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Model</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Load</TableCell>
                          <TableCell>Requests/min</TableCell>
                          <TableCell>Avg Response</TableCell>
                          <TableCell>Success Rate</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          <TableCell>GPT-4</TableCell>
                          <TableCell>
                            <Chip label="Healthy" color="success" size="small" />
                          </TableCell>
                          <TableCell>42%</TableCell>
                          <TableCell>25</TableCell>
                          <TableCell>2.1s</TableCell>
                          <TableCell>99.2%</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Claude-3</TableCell>
                          <TableCell>
                            <Chip label="Healthy" color="success" size="small" />
                          </TableCell>
                          <TableCell>38%</TableCell>
                          <TableCell>32</TableCell>
                          <TableCell>1.8s</TableCell>
                          <TableCell>99.7%</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>GPT-3.5 Turbo</TableCell>
                          <TableCell>
                            <Chip label="Degraded" color="warning" size="small" />
                          </TableCell>
                          <TableCell>78%</TableCell>
                          <TableCell>45</TableCell>
                          <TableCell>1.2s</TableCell>
                          <TableCell>97.8%</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
        
        {/* Network & Routing Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    LISP Routing Statistics
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" gutterBottom>Map Cache Entries: {stats?.lisp_stats?.total_entries || 3}</Typography>
                    <Typography variant="body2" gutterBottom>Active RLOCs: {stats?.lisp_stats?.reachable_rlocs || 5}</Typography>
                    <Typography variant="body2" gutterBottom>Cache Hit Ratio: {((stats?.lisp_stats?.cache_hit_ratio || 0.95) * 100).toFixed(1)}%</Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    DNS Routing Statistics
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" gutterBottom>Total Services: {stats?.dns_stats?.total_services || 3}</Typography>
                    <Typography variant="body2" gutterBottom>Healthy Records: {stats?.dns_stats?.total_records || 6}</Typography>
                    <Typography variant="body2" gutterBottom>Avg Query Time: 2.3ms</Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
        
        {/* Alert History Tab */}
        <TabPanel value={tabValue} index={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Alerts (Last 24 Hours)
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Timestamp</TableCell>
                      <TableCell>Severity</TableCell>
                      <TableCell>Title</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell>{new Date().toLocaleString()}</TableCell>
                      <TableCell>
                        <Chip label="Warning" color="warning" size="small" />
                      </TableCell>
                      <TableCell>High Response Time</TableCell>
                      <TableCell>Average response time exceeded 3 seconds</TableCell>
                      <TableCell>
                        <Chip label="Active" color="error" size="small" />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>{new Date(Date.now() - 3600000).toLocaleString()}</TableCell>
                      <TableCell>
                        <Chip label="Info" color="info" size="small" />
                      </TableCell>
                      <TableCell>Model Failover</TableCell>
                      <TableCell>GPT-3.5 Turbo automatically failed over to backup</TableCell>
                      <TableCell>
                        <Chip label="Resolved" color="success" size="small" />
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default MonitoringDashboard;