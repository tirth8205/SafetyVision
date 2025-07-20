import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
} from '@mui/material';
import {
  History,
  Warning,
  Error,
  CheckCircle,
  Visibility,
} from '@mui/icons-material';
import { format } from 'date-fns';

const AlertHistory: React.FC = () => {
  // Mock alert history for demo
  const alerts = [
    {
      id: '1',
      timestamp: new Date(Date.now() - 30 * 60 * 1000), // 30 min ago
      level: 'HIGH',
      type: 'Radiation',
      message: 'Radiation levels exceeded threshold in Zone A',
      status: 'resolved',
      confidence: 0.92,
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
      level: 'MODERATE',
      type: 'Temperature',
      message: 'Cooling system temperature rising above normal',
      status: 'monitoring',
      confidence: 0.78,
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4 hours ago
      level: 'LOW',
      type: 'Vibration',
      message: 'Minor vibration detected in Pump A',
      status: 'resolved',
      confidence: 0.65,
    },
    {
      id: '4',
      timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000), // 6 hours ago
      level: 'CRITICAL',
      type: 'Emergency',
      message: 'Manual emergency stop activated by operator',
      status: 'resolved',
      confidence: 1.0,
    },
    {
      id: '5',
      timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000), // 8 hours ago
      level: 'MODERATE',
      type: 'Gas',
      message: 'Gas concentration levels elevated in storage area',
      status: 'resolved',
      confidence: 0.84,
    },
  ];

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'error';
      case 'HIGH': return 'error';
      case 'MODERATE': return 'warning';
      case 'LOW': return 'info';
      default: return 'default';
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'CRITICAL': return <Error color="error" />;
      case 'HIGH': return <Warning color="error" />;
      case 'MODERATE': return <Warning color="warning" />;
      case 'LOW': return <CheckCircle color="info" />;
      default: return <CheckCircle />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'resolved': return 'success';
      case 'monitoring': return 'warning';
      case 'active': return 'error';
      default: return 'default';
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          <History sx={{ mr: 1, verticalAlign: 'middle' }} />
          Recent Alerts & Events
        </Typography>

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Time</TableCell>
                <TableCell>Level</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Message</TableCell>
                <TableCell>Confidence</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {alerts.map((alert) => (
                <TableRow key={alert.id} hover>
                  <TableCell>
                    <Typography variant="body2">
                      {format(alert.timestamp, 'HH:mm')}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {format(alert.timestamp, 'MMM dd')}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      {getLevelIcon(alert.level)}
                      <Chip
                        label={alert.level}
                        color={getLevelColor(alert.level) as any}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {alert.type}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Typography variant="body2">
                      {alert.message}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Typography variant="body2">
                      {(alert.confidence * 100).toFixed(0)}%
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Chip
                      label={alert.status.toUpperCase()}
                      color={getStatusColor(alert.status) as any}
                      size="small"
                      variant="filled"
                    />
                  </TableCell>
                  
                  <TableCell>
                    <IconButton size="small" color="primary">
                      <Visibility fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Summary Stats */}
        <Box mt={2} display="flex" gap={2} flexWrap="wrap">
          <Chip
            label={`${alerts.filter(a => a.status === 'resolved').length} Resolved`}
            color="success"
            size="small"
            variant="outlined"
          />
          <Chip
            label={`${alerts.filter(a => a.status === 'monitoring').length} Monitoring`}
            color="warning"
            size="small"
            variant="outlined"
          />
          <Chip
            label={`${alerts.filter(a => a.level === 'CRITICAL' || a.level === 'HIGH').length} High Priority`}
            color="error"
            size="small"
            variant="outlined"
          />
        </Box>
      </CardContent>
    </Card>
  );
};

export default AlertHistory;