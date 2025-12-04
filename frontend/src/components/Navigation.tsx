import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  Tabs,
  Tab,
  Paper
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Send as QueryIcon,
  Analytics as MonitoringIcon,
  Psychology as ModelIcon,
  ViewInAr as PacketIcon
} from '@mui/icons-material';

const Navigation: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const getCurrentTab = () => {
    switch (location.pathname) {
      case '/':
        return 0;
      case '/query':
        return 1;
      case '/monitoring':
        return 2;
      case '/models':
        return 3;
      case '/packets':
        return 4;
      default:
        return 0;
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    const routes = ['/', '/query', '/monitoring', '/models', '/packets'];
    navigate(routes[newValue]);
  };
  
  return (
    <Paper elevation={1} sx={{ borderRadius: 0 }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={getCurrentTab()}
          onChange={handleTabChange}
          aria-label="navigation tabs"
          variant="fullWidth"
        >
          <Tab
            icon={<DashboardIcon />}
            label="Dashboard"
            iconPosition="start"
          />
          <Tab
            icon={<QueryIcon />}
            label="Query Interface"
            iconPosition="start"
          />
          <Tab
            icon={<MonitoringIcon />}
            label="Monitoring"
            iconPosition="start"
          />
          <Tab
            icon={<ModelIcon />}
            label="Models"
            iconPosition="start"
          />
          <Tab
            icon={<PacketIcon />}
            label="LISP Packets"
            iconPosition="start"
          />
        </Tabs>
      </Box>
    </Paper>
  );
};

export default Navigation;