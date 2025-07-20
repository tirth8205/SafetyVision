import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Grid,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Shield,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from 'recharts';

interface SafetyMetricsProps {
  safetyUpdate: any;
}

const SafetyMetrics: React.FC<SafetyMetricsProps> = ({ safetyUpdate }) => {
  // Generate mock historical data for demo
  const generateHistoricalData = () => {
    const data = [];
    const now = new Date();
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      data.push({
        time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        confidence: Math.random() * 30 + 70, // 70-100%
        riskScore: Math.random() * 20 + 10, // 10-30
      });
    }
    return data;
  };

  const historicalData = generateHistoricalData();
  const confidence = safetyUpdate?.confidence || 0.85;
  const riskScore = Math.random() * 100; // Mock risk score

  const getRiskLevel = (score: number) => {
    if (score < 20) return { level: 'MINIMAL', color: 'success' };
    if (score < 40) return { level: 'LOW', color: 'info' };
    if (score < 60) return { level: 'MODERATE', color: 'warning' };
    if (score < 80) return { level: 'HIGH', color: 'error' };
    return { level: 'CRITICAL', color: 'error' };
  };

  const risk = getRiskLevel(riskScore);
  const trend = Math.random() > 0.5 ? 'up' : Math.random() > 0.5 ? 'down' : 'flat';

  const getTrendIcon = () => {
    switch (trend) {
      case 'up': return <TrendingUp color="error" />;
      case 'down': return <TrendingDown color="success" />;
      default: return <TrendingFlat color="info" />;
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography variant="h6" component="h2">
            <Shield sx={{ mr: 1, verticalAlign: 'middle' }} />
            Safety Metrics
          </Typography>
          {getTrendIcon()}
        </Box>

        <Grid container spacing={3}>
          {/* Confidence Score */}
          <Grid item xs={12} sm={6}>
            <Box>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="body1">Analysis Confidence</Typography>
                <Typography variant="h6" color="primary">
                  {(confidence * 100).toFixed(1)}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={confidence * 100}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: confidence > 0.8 ? '#4caf50' : confidence > 0.6 ? '#ff9800' : '#f44336',
                  },
                }}
              />
            </Box>
          </Grid>

          {/* Risk Score */}
          <Grid item xs={12} sm={6}>
            <Box>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="body1">Risk Assessment</Typography>
                <Chip
                  label={risk.level}
                  color={risk.color as any}
                  size="small"
                />
              </Box>
              <LinearProgress
                variant="determinate"
                value={riskScore}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: riskScore < 30 ? '#4caf50' : riskScore < 60 ? '#ff9800' : '#f44336',
                  },
                }}
              />
            </Box>
          </Grid>
        </Grid>

        {/* Recommendations */}
        {safetyUpdate?.recommendations && (
          <Box mt={3}>
            <Typography variant="subtitle2" gutterBottom>
              Current Recommendations:
            </Typography>
            {safetyUpdate.recommendations.slice(0, 3).map((rec: string, index: number) => (
              <Typography key={index} variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                • {rec}
              </Typography>
            ))}
          </Box>
        )}

        {/* Mini Chart */}
        <Box mt={3} height={120}>
          <Typography variant="subtitle2" gutterBottom>
            24-Hour Confidence Trend
          </Typography>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis 
                dataKey="time" 
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 10, fill: '#666' }}
              />
              <YAxis hide />
              <Line
                type="monotone"
                dataKey="confidence"
                stroke="#00e676"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: '#00e676' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  );
};

export default SafetyMetrics;