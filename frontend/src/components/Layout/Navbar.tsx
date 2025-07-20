import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Chip,
  IconButton,
} from '@mui/material';
import {
  Security,
  Dashboard,
  History,
  Settings,
  Notifications,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useWebSocket } from '../../hooks/useWebSocket';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isConnected, emergencyAlert } = useWebSocket();

  const navItems = [
    { label: 'Dashboard', path: '/', icon: <Dashboard /> },
    { label: 'Historical', path: '/historical', icon: <History /> },
    { label: 'Settings', path: '/settings', icon: <Settings /> },
  ];

  return (
    <AppBar position="static" sx={{ bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
      <Toolbar>
        <Box display="flex" alignItems="center" sx={{ mr: 4 }}>
          <Security sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" component="div" sx={{ color: 'text.primary', fontWeight: 700 }}>
            SafetyVision
          </Typography>
        </Box>

        <Box sx={{ flexGrow: 1, display: 'flex', gap: 1 }}>
          {navItems.map((item) => (
            <Button
              key={item.path}
              startIcon={item.icon}
              onClick={() => navigate(item.path)}
              sx={{
                color: location.pathname === item.path ? 'primary.main' : 'text.primary',
                bgcolor: location.pathname === item.path ? 'primary.main' : 'transparent',
                '&:hover': {
                  bgcolor: location.pathname === item.path ? 'primary.dark' : 'action.hover',
                },
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>

        <Box display="flex" alignItems="center" gap={2}>
          {emergencyAlert && (
            <Chip
              label="EMERGENCY ACTIVE"
              color="error"
              variant="filled"
              sx={{
                animation: 'pulse 2s infinite',
                '@keyframes pulse': {
                  '0%': { opacity: 1 },
                  '50%': { opacity: 0.7 },
                  '100%': { opacity: 1 },
                },
              }}
            />
          )}
          
          <Chip
            label={isConnected ? 'CONNECTED' : 'DISCONNECTED'}
            color={isConnected ? 'success' : 'error'}
            variant="outlined"
            size="small"
          />

          <IconButton color="inherit">
            <Notifications />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;