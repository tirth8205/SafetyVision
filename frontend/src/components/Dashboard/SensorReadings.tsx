import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  Thermostat,
  WaterDrop,
  Speed,
  RadioactiveSharp,
  Air,
  Vibration,
} from '@mui/icons-material';

interface SensorReadingsProps {
  sensorData: any;
}

interface SensorReading {
  icon: React.ReactNode;
  label: string;
  value: number;
  unit: string;
  threshold: { safe: number; warning: number; danger: number };
  format?: (value: number) => string;
}

const SensorReadings: React.FC<SensorReadingsProps> = ({ sensorData }) => {
  const defaultSensorData = {
    radiation_level: 0.1,
    temperature: 25,
    humidity: 60,
    pressure: 1013,
    gas_concentration: 0.05,
    vibration_level: 0.02,
  };

  const data = sensorData || defaultSensorData;

  const sensors: SensorReading[] = [
    {
      icon: <RadioactiveSharp />,
      label: 'Radiation',
      value: data.radiation_level || 0,
      unit: 'mSv/h',
      threshold: { safe: 0.1, warning: 0.5, danger: 1.0 },
      format: (v) => v.toFixed(3),
    },
    {
      icon: <Thermostat />,
      label: 'Temperature',
      value: data.temperature || 0,
      unit: '°C',
      threshold: { safe: 30, warning: 50, danger: 70 },
      format: (v) => v.toFixed(1),
    },
    {
      icon: <WaterDrop />,
      label: 'Humidity',
      value: data.humidity || 0,
      unit: '%',
      threshold: { safe: 70, warning: 85, danger: 95 },
      format: (v) => v.toFixed(0),
    },
    {
      icon: <Speed />,
      label: 'Pressure',
      value: data.pressure || 0,
      unit: 'hPa',
      threshold: { safe: 1020, warning: 1050, danger: 1080 },
      format: (v) => v.toFixed(0),
    },
    {
      icon: <Air />,
      label: 'Gas Levels',
      value: data.gas_concentration || 0,
      unit: 'ppm',
      threshold: { safe: 0.1, warning: 0.5, danger: 1.0 },
      format: (v) => v.toFixed(3),
    },
    {
      icon: <Vibration />,
      label: 'Vibration',
      value: data.vibration_level || 0,
      unit: 'mm/s',
      threshold: { safe: 0.1, warning: 0.5, danger: 1.0 },
      format: (v) => v.toFixed(3),
    },
  ];

  const getSensorStatus = (value: number, threshold: any) => {
    if (value <= threshold.safe) return { color: 'success', status: 'SAFE' };
    if (value <= threshold.warning) return { color: 'warning', status: 'WARNING' };
    return { color: 'error', status: 'DANGER' };
  };

  const getProgressValue = (value: number, threshold: any) => {
    const max = threshold.danger * 1.2; // Scale to show progression
    return Math.min((value / max) * 100, 100);
  };

  const getProgressColor = (value: number, threshold: any) => {
    if (value <= threshold.safe) return '#4caf50';
    if (value <= threshold.warning) return '#ff9800';
    return '#f44336';
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          Sensor Readings
        </Typography>

        <Grid container spacing={2}>
          {sensors.map((sensor, index) => {
            const status = getSensorStatus(sensor.value, sensor.threshold);
            const progressValue = getProgressValue(sensor.value, sensor.threshold);
            const progressColor = getProgressColor(sensor.value, sensor.threshold);

            return (
              <Grid item xs={12} sm={6} key={index}>
                <Box 
                  sx={{ 
                    p: 2, 
                    border: 1, 
                    borderColor: 'divider', 
                    borderRadius: 1,
                    backgroundColor: 'background.paper',
                  }}
                >
                  <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
                    <Box display="flex" alignItems="center" gap={1}>
                      {sensor.icon}
                      <Typography variant="body2" fontWeight="medium">
                        {sensor.label}
                      </Typography>
                    </Box>
                    <Chip
                      label={status.status}
                      color={status.color as any}
                      size="small"
                      variant="outlined"
                    />
                  </Box>

                  <Box display="flex" alignItems="baseline" justifyContent="space-between" mb={1}>
                    <Typography variant="h6" component="span">
                      {sensor.format ? sensor.format(sensor.value) : sensor.value}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {sensor.unit}
                    </Typography>
                  </Box>

                  <LinearProgress
                    variant="determinate"
                    value={progressValue}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: 'rgba(255,255,255,0.1)',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: progressColor,
                        borderRadius: 3,
                      },
                    }}
                  />

                  <Box display="flex" justifyContent="space-between" mt={0.5}>
                    <Typography variant="caption" color="text.secondary">
                      Safe: ≤{sensor.threshold.safe}{sensor.unit}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Danger: ≥{sensor.threshold.danger}{sensor.unit}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            );
          })}
        </Grid>

        {/* Quick Status Summary */}
        <Box mt={3} p={2} bgcolor="background.default" borderRadius={1}>
          <Typography variant="subtitle2" gutterBottom>
            Status Summary
          </Typography>
          <Box display="flex" gap={1} flexWrap="wrap">
            {sensors.map((sensor, index) => {
              const status = getSensorStatus(sensor.value, sensor.threshold);
              return (
                <Chip
                  key={index}
                  label={`${sensor.label}: ${status.status}`}
                  color={status.color as any}
                  size="small"
                  variant="filled"
                />
              );
            })}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default SensorReadings;