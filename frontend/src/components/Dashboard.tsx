import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Box,
  Chip,
  LinearProgress,
  Alert
} from '@mui/material';
import {
  Computer as ServerIcon,
  Psychology as ModelIcon,
  Speed as PerformanceIcon,
  Warning as AlertIcon
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { useAPI } from '../hooks/useAPI';

interface SystemStats {
  lisp_stats: any;
  dns_stats: any;
  llm_stats: any;
  system_stats: any;
}

interface HealthStatus {
  status: string;
  services: { [key: string]: string };
  uptime_seconds: number;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const api = useAPI();
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsData, healthData] = await Promise.all([
          api.getStats(),
          api.getHealth()
        ]);
        setStats(statsData);
        setHealth(healthData);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10 seconds
    
    return () => clearInterval(interval);
  }, [api]);
  
  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'degraded': return 'warning';
      case 'unhealthy': return 'error';
      default: return 'default';
    }
  };
  
  // Mock data for charts
  const modelDistribution = [
    { name: 'GPT-4', value: 45, color: '#8884d8' },
    { name: 'Claude-3', value: 35, color: '#82ca9d' },
    { name: 'GPT-3.5', value: 20, color: '#ffc658' }
  ];
  
  const performanceData = [
    { time: '10:00', responseTime: 2.1, throughput: 85 },
    { time: '10:05', responseTime: 1.8, throughput: 92 },
    { time: '10:10', responseTime: 2.3, throughput: 78 },
    { time: '10:15', responseTime: 1.9, throughput: 89 },
    { time: '10:20', responseTime: 2.0, throughput: 91 },
  ];
  
  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>Loading dashboard...</Typography>
      </Box>
    );
  }
  
  return (
    <Grid container spacing={3}>
      {/* System Health Overview */}
      <Grid size={12}>
        <Paper elevation={2} sx={{ p: 2 }}>
          <Typography variant="h5" gutterBottom>
            System Health Overview
          </Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <ServerIcon color="primary" />
                    <Typography variant="h6" sx={{ ml: 1 }}>System Status</Typography>
                  </Box>
                  <Chip
                    label={health?.status || 'unknown'}
                    color={getStatusColor(health?.status || 'unknown')}
                    size="small"
                  />
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Uptime: {health ? formatUptime(health.uptime_seconds) : 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <ModelIcon color="primary" />
                    <Typography variant="h6" sx={{ ml: 1 }}>Models</Typography>
                  </Box>
                  <Typography variant="h4" color="primary">
                    {stats?.llm_stats?.models ? Object.keys(stats.llm_stats.models).length : 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Available Models
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <PerformanceIcon color="primary" />
                    <Typography variant="h6" sx={{ ml: 1 }}>Queries</Typography>
                  </Box>
                  <Typography variant="h4" color="primary">
                    {stats?.llm_stats?.total_queries || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Processed
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <AlertIcon color="warning" />
                    <Typography variant="h6" sx={{ ml: 1 }}>Alerts</Typography>
                  </Box>
                  <Typography variant="h4" color="warning.main">
                    0
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Alerts
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      </Grid>
      
      {/* Service Status */}
      <Grid size={{ xs: 12, md: 6 }}>
        <Paper elevation={2} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Service Status
          </Typography>
          <Box sx={{ mt: 2 }}>
            {health?.services && Object.entries(health.services).map(([service, status]) => (
              <Box key={service} display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="body1">{service.replace('_', ' ').toUpperCase()}</Typography>
                <Chip
                  label={status}
                  color={getStatusColor(status)}
                  size="small"
                />
              </Box>
            ))}
          </Box>
        </Paper>
      </Grid>

      {/* Model Usage Distribution */}
      <Grid size={{ xs: 12, md: 6 }}>
        <Paper elevation={2} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Model Usage Distribution
          </Typography>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={modelDistribution}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={80}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}%`}
              >
                {modelDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      {/* Performance Metrics */}
      <Grid size={12}>
        <Paper elevation={2} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Performance Metrics
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis yAxisId="left" orientation="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line 
                yAxisId="left" 
                type="monotone" 
                dataKey="responseTime" 
                stroke="#8884d8" 
                name="Response Time (s)"
              />
              <Line 
                yAxisId="right" 
                type="monotone" 
                dataKey="throughput" 
                stroke="#82ca9d" 
                name="Throughput (%)"
              />
            </LineChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>
      
      {/* System Resources */}
      <Grid size={12}>
        <Paper elevation={2} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            System Resources
          </Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="body2" gutterBottom>CPU Usage</Typography>
              <LinearProgress
                variant="determinate"
                value={stats?.system_stats?.cpu_usage_percent || 0}
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="body2" sx={{ mt: 1 }}>
                {stats?.system_stats?.cpu_usage_percent || 0}%
              </Typography>
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="body2" gutterBottom>Memory Usage</Typography>
              <LinearProgress
                variant="determinate"
                value={stats?.system_stats?.memory_usage_percent || 0}
                color="warning"
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="body2" sx={{ mt: 1 }}>
                {stats?.system_stats?.memory_usage_percent || 0}%
              </Typography>
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="body2" gutterBottom>Disk Usage</Typography>
              <LinearProgress
                variant="determinate"
                value={stats?.system_stats?.disk_usage_percent || 0}
                color="error"
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="body2" sx={{ mt: 1 }}>
                {stats?.system_stats?.disk_usage_percent || 0}%
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
};

export default Dashboard;