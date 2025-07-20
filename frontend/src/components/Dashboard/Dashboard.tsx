import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Alert,
  AlertTitle,
  Chip,
  Card,
  CardContent,
  IconButton,
  Button,
} from '@mui/material';
import {
  Warning,
  Emergency,
  CheckCircle,
  Refresh,
  Stop,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

import { useWebSocket } from '../../hooks/useWebSocket';
import SafetyMetrics from './SafetyMetrics';
import SensorReadings from './SensorReadings';
import CameraFeed from './CameraFeed';
import AlertHistory from './AlertHistory';
import SystemStatus from './SystemStatus';

const Dashboard: React.FC = () => {
  const { 
    isConnected, 
    latestSafetyUpdate, 
    emergencyAlert, 
    triggerEmergencyStop 
  } = useWebSocket();
  
  const [lastUpdateTime, setLastUpdateTime] = useState<Date>(new Date());

  useEffect(() => {
    if (latestSafetyUpdate) {
      setLastUpdateTime(new Date());
    }
  }, [latestSafetyUpdate]);

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel?.toLowerCase()) {
      case 'minimal': return 'success';
      case 'low': return 'info';
      case 'moderate': return 'warning';
      case 'high': return 'error';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getRiskLevelIcon = (riskLevel: string) => {
    switch (riskLevel?.toLowerCase()) {
      case 'minimal': return <CheckCircle />;
      case 'low': return <CheckCircle color="info" />;
      case 'moderate': return <Warning color="warning" />;
      case 'high': return <Warning color="error" />;
      case 'critical': return <Emergency color="error" />;
      default: return <CheckCircle />;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Emergency Alert Banner */}
      <AnimatePresence>
        {emergencyAlert && (
          <motion.div
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            style={{ marginBottom: 16 }}
          >
            <Alert 
              severity="error" 
              sx={{ 
                mb: 2,
                '& .MuiAlert-message': { fontSize: '1.1rem' },
                border: '2px solid #f44336',
                boxShadow: '0 0 20px rgba(244, 67, 54, 0.3)',
              }}
            >
              <AlertTitle>🚨 EMERGENCY ALERT</AlertTitle>
              <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                {emergencyAlert.description}
              </Typography>
              <Box sx={{ mt: 1 }}>
                {emergencyAlert.recommendations.map((rec, index) => (
                  <Typography key={index} variant="body2">
                    • {rec}
                  </Typography>
                ))}
              </Box>
            </Alert>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header with System Status */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box display="flex" alignItems="center" gap={2}>
                  <Typography variant="h4" component="h1">
                    Safety Status
                  </Typography>
                  <Chip
                    icon={getRiskLevelIcon(latestSafetyUpdate?.risk_level || 'minimal')}
                    label={latestSafetyUpdate?.risk_level || 'MINIMAL'}
                    color={getRiskLevelColor(latestSafetyUpdate?.risk_level || 'minimal') as any}
                    size="large"
                    sx={{ fontSize: '1rem', px: 2 }}
                  />
                </Box>
                <Box display="flex" alignItems="center" gap={1}>
                  <Chip
                    label={isConnected ? 'CONNECTED' : 'DISCONNECTED'}
                    color={isConnected ? 'success' : 'error'}
                    variant="outlined"
                  />
                  <IconButton color="primary">
                    <Refresh />
                  </IconButton>
                </Box>
              </Box>
              
              {latestSafetyUpdate && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body1" color="text.secondary">
                    Status: {latestSafetyUpdate.status}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Confidence: {(latestSafetyUpdate.confidence * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Last Update: {lastUpdateTime.toLocaleTimeString()}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" flexDirection="column" height="100%" justifyContent="center">
                <Button
                  variant="contained"
                  color="error"
                  size="large"
                  startIcon={<Stop />}
                  onClick={triggerEmergencyStop}
                  sx={{ 
                    py: 2,
                    fontSize: '1.1rem',
                    fontWeight: 'bold',
                    boxShadow: '0 4px 20px rgba(244, 67, 54, 0.3)',
                  }}
                >
                  EMERGENCY STOP
                </Button>
                <Typography variant="caption" align="center" sx={{ mt: 1 }}>
                  Immediately halt all operations
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Dashboard Grid */}
      <Grid container spacing={3}>
        {/* Safety Metrics */}
        <Grid item xs={12} lg={6}>
          <SafetyMetrics safetyUpdate={latestSafetyUpdate} />
        </Grid>

        {/* Sensor Readings */}
        <Grid item xs={12} lg={6}>
          <SensorReadings sensorData={latestSafetyUpdate?.sensor_data} />
        </Grid>

        {/* Camera Feed */}
        <Grid item xs={12} lg={8}>
          <CameraFeed />
        </Grid>

        {/* System Status */}
        <Grid item xs={12} lg={4}>
          <SystemStatus isConnected={isConnected} />
        </Grid>

        {/* Alert History */}
        <Grid item xs={12}>
          <AlertHistory />
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;