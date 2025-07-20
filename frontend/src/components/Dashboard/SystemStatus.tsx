import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Computer,
  CheckCircle,
  Error,
  Warning,
  Wifi,
  Storage,
  Memory,
} from '@mui/icons-material';

interface SystemStatusProps {
  isConnected: boolean;
}

const SystemStatus: React.FC<SystemStatusProps> = ({ isConnected }) => {
  // Mock system metrics for demo
  const systemMetrics = {
    uptime: '72h 15m',
    cpuUsage: 45,
    memoryUsage: 62,
    diskUsage: 23,
    networkLatency: 12,
    lastUpdate: new Date().toLocaleTimeString(),
  };

  const services = [
    {
      name: 'Safety Engine',
      status: 'operational',
      icon: <CheckCircle color="success" />,
    },
    {
      name: 'VLM Service',
      status: 'disabled',
      icon: <Warning color="warning" />,
    },
    {
      name: 'Database',
      status: 'connected',
      icon: <CheckCircle color="success" />,
    },
    {
      name: 'Sensor Array',
      status: 'operational',
      icon: <CheckCircle color="success" />,
    },
    {
      name: 'Camera Feed',
      status: 'operational',
      icon: <CheckCircle color="success" />,
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational':
      case 'connected':
        return 'success';
      case 'disabled':
      case 'warning':
        return 'warning';
      case 'error':
      case 'disconnected':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          <Computer sx={{ mr: 1, verticalAlign: 'middle' }} />
          System Status
        </Typography>

        {/* Connection Status */}
        <Box mb={3}>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
            <Typography variant="body2">Connection</Typography>
            <Chip
              icon={<Wifi />}
              label={isConnected ? 'CONNECTED' : 'DISCONNECTED'}
              color={isConnected ? 'success' : 'error'}
              size="small"
            />
          </Box>
        </Box>

        {/* System Metrics */}
        <Box mb={3}>
          <Typography variant="subtitle2" gutterBottom>
            Performance Metrics
          </Typography>
          
          <Box display="flex" flexDirection="column" gap={1}>
            <Box display="flex" justifyContent="space-between">
              <Typography variant="body2">Uptime</Typography>
              <Typography variant="body2" color="text.secondary">
                {systemMetrics.uptime}
              </Typography>
            </Box>
            
            <Box display="flex" justifyContent="space-between">
              <Typography variant="body2">CPU Usage</Typography>
              <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="body2" color="text.secondary">
                  {systemMetrics.cpuUsage}%
                </Typography>
                <Chip
                  size="small"
                  color={systemMetrics.cpuUsage > 80 ? 'error' : systemMetrics.cpuUsage > 60 ? 'warning' : 'success'}
                  label=""
                  sx={{ width: 8, height: 8, minWidth: 8 }}
                />
              </Box>
            </Box>
            
            <Box display="flex" justifyContent="space-between">
              <Typography variant="body2">Memory</Typography>
              <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="body2" color="text.secondary">
                  {systemMetrics.memoryUsage}%
                </Typography>
                <Chip
                  size="small"
                  color={systemMetrics.memoryUsage > 80 ? 'error' : systemMetrics.memoryUsage > 60 ? 'warning' : 'success'}
                  label=""
                  sx={{ width: 8, height: 8, minWidth: 8 }}
                />
              </Box>
            </Box>
          </Box>
        </Box>

        {/* Service Status */}
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Service Status
          </Typography>
          
          <List dense sx={{ p: 0 }}>
            {services.map((service, index) => (
              <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  {service.icon}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="body2">
                        {service.name}
                      </Typography>
                      <Chip
                        label={service.status.toUpperCase()}
                        color={getStatusColor(service.status) as any}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: '0.6rem', height: 20 }}
                      />
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Box>

        {/* Last Update */}
        <Box mt={2} pt={2} borderTop={1} borderColor="divider">
          <Typography variant="caption" color="text.secondary">
            Last update: {systemMetrics.lastUpdate}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default SystemStatus;