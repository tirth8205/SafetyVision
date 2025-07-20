import React, { useState, useRef } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Alert,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  CameraAlt,
  Visibility,
  VisibilityOff,
  Refresh,
  SmartToy,
} from '@mui/icons-material';

const CameraFeed: React.FC = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<string | null>(null);
  const [showFeed, setShowFeed] = useState(true);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Generate a simulated camera feed
  const generateSimulatedFeed = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Simulate facility layout
    ctx.strokeStyle = '#00e676';
    ctx.lineWidth = 2;

    // Draw facility outline
    ctx.strokeRect(50, 50, canvas.width - 100, canvas.height - 100);

    // Draw equipment
    ctx.fillStyle = '#333';
    ctx.fillRect(100, 100, 80, 60);
    ctx.fillRect(220, 100, 80, 60);
    ctx.fillRect(340, 100, 80, 60);

    // Add labels
    ctx.fillStyle = '#00e676';
    ctx.font = '12px monospace';
    ctx.fillText('REACTOR-1', 105, 135);
    ctx.fillText('PUMP-A', 235, 135);
    ctx.fillText('VALVE-B', 350, 135);

    // Add sensor indicators
    ctx.fillStyle = '#ff9800';
    ctx.beginPath();
    ctx.arc(140, 80, 4, 0, 2 * Math.PI);
    ctx.fill();

    ctx.fillStyle = '#4caf50';
    ctx.beginPath();
    ctx.arc(260, 80, 4, 0, 2 * Math.PI);
    ctx.fill();

    ctx.beginPath();
    ctx.arc(380, 80, 4, 0, 2 * Math.PI);
    ctx.fill();

    // Add timestamp
    ctx.fillStyle = '#666';
    ctx.font = '10px monospace';
    ctx.fillText(new Date().toLocaleTimeString(), 10, canvas.height - 10);

    // Add radiation overlay (simulated)
    const gradient = ctx.createRadialGradient(
      canvas.width / 2, canvas.height / 2, 0,
      canvas.width / 2, canvas.height / 2, 200
    );
    gradient.addColorStop(0, 'rgba(255, 255, 0, 0.1)');
    gradient.addColorStop(1, 'rgba(255, 255, 0, 0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  };

  React.useEffect(() => {
    if (showFeed) {
      const interval = setInterval(generateSimulatedFeed, 1000);
      generateSimulatedFeed(); // Initial render
      return () => clearInterval(interval);
    }
  }, [showFeed]);

  const handleVLMAnalysis = async () => {
    setIsAnalyzing(true);
    
    // Simulate VLM analysis
    setTimeout(() => {
      setAnalysisResult(
        'Visual analysis temporarily disabled (PyTorch security update required). ' +
        'Simulated analysis: Facility equipment appears operational. ' +
        'No visible structural damage detected. ' +
        'Personnel protective equipment required in Zone A.'
      );
      setIsAnalyzing(false);
    }, 3000);
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography variant="h6" component="h2">
            <CameraAlt sx={{ mr: 1, verticalAlign: 'middle' }} />
            Facility Camera Feed
          </Typography>
          
          <Box display="flex" gap={1}>
            <Button
              startIcon={showFeed ? <VisibilityOff /> : <Visibility />}
              onClick={() => setShowFeed(!showFeed)}
              size="small"
            >
              {showFeed ? 'Hide' : 'Show'}
            </Button>
            <Button startIcon={<Refresh />} size="small">
              Refresh
            </Button>
          </Box>
        </Box>

        {showFeed && (
          <Box
            sx={{
              position: 'relative',
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              overflow: 'hidden',
              mb: 2,
            }}
          >
            <canvas
              ref={canvasRef}
              width={600}
              height={300}
              style={{
                width: '100%',
                height: 'auto',
                display: 'block',
                backgroundColor: '#1a1a1a',
              }}
            />
            
            {/* Overlay indicators */}
            <Box
              sx={{
                position: 'absolute',
                top: 8,
                left: 8,
                display: 'flex',
                gap: 1,
              }}
            >
              <Chip label="LIVE" color="error" size="small" />
              <Chip label="ZONE-A" color="warning" size="small" />
            </Box>

            <Box
              sx={{
                position: 'absolute',
                top: 8,
                right: 8,
                display: 'flex',
                gap: 1,
              }}
            >
              <Chip label="HD" size="small" />
              <Chip label="THERMAL" color="info" size="small" />
            </Box>
          </Box>
        )}

        {/* VLM Analysis Section */}
        <Box>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
            <Typography variant="subtitle1">
              VLM Analysis
            </Typography>
            <Button
              startIcon={<SmartToy />}
              onClick={handleVLMAnalysis}
              disabled={isAnalyzing || !showFeed}
              variant="outlined"
              size="small"
            >
              Analyze Scene
            </Button>
          </Box>

          {isAnalyzing && (
            <Box mb={2}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                VLM analyzing environment...
              </Typography>
              <LinearProgress />
            </Box>
          )}

          {analysisResult && (
            <Alert severity="info" sx={{ mt: 1 }}>
              <Typography variant="body2">
                {analysisResult}
              </Typography>
            </Alert>
          )}

          {!analysisResult && !isAnalyzing && (
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              Click "Analyze Scene" to run VLM safety analysis on the current camera feed.
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default CameraFeed;