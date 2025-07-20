import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';
import toast from 'react-hot-toast';

interface SafetyUpdate {
  timestamp: string;
  risk_level: string;
  sensor_data: any;
  confidence: number;
  status: string;
  recommendations: string[];
}

interface EmergencyAlert {
  id: string;
  timestamp: string;
  risk_level: string;
  description: string;
  recommendations: string[];
  auto_triggered: boolean;
}

interface WebSocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  latestSafetyUpdate: SafetyUpdate | null;
  emergencyAlert: EmergencyAlert | null;
  sendMessage: (message: any) => void;
  triggerEmergencyStop: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [latestSafetyUpdate, setLatestSafetyUpdate] = useState<SafetyUpdate | null>(null);
  const [emergencyAlert, setEmergencyAlert] = useState<EmergencyAlert | null>(null);

  useEffect(() => {
    // Connect to WebSocket server
    const newSocket = io('ws://localhost:8000/ws', {
      transports: ['websocket'],
    });

    newSocket.on('connect', () => {
      setIsConnected(true);
      toast.success('Connected to SafetyVision system');
      console.log('WebSocket connected');
    });

    newSocket.on('disconnect', () => {
      setIsConnected(false);
      toast.error('Disconnected from SafetyVision system');
      console.log('WebSocket disconnected');
    });

    newSocket.on('safety_update', (data: SafetyUpdate) => {
      setLatestSafetyUpdate(data);
      
      // Show toast for risk level changes
      const riskLevel = data.risk_level.toLowerCase();
      if (riskLevel === 'high' || riskLevel === 'critical') {
        toast.error(`⚠️ Risk level: ${data.risk_level}`, {
          duration: 6000,
        });
      } else if (riskLevel === 'moderate') {
        toast(`⚠️ Risk level: ${data.risk_level}`, {
          icon: '⚠️',
          duration: 4000,
        });
      }
    });

    newSocket.on('emergency_alert', (data: EmergencyAlert) => {
      setEmergencyAlert(data);
      toast.error(`🚨 EMERGENCY: ${data.description}`, {
        duration: 0, // Don't auto-dismiss
      });
      
      // Browser notification if permission granted
      if (Notification.permission === 'granted') {
        new Notification('SafetyVision Emergency Alert', {
          body: data.description,
          icon: '/favicon.ico',
          requireInteraction: true,
        });
      }
    });

    newSocket.on('emergency_cleared', () => {
      setEmergencyAlert(null);
      toast.success('✅ Emergency status cleared');
    });

    newSocket.on('emergency_stop', (data) => {
      toast.error('🛑 EMERGENCY STOP ACTIVATED', {
        duration: 0,
      });
    });

    // Request notification permission
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }

    setSocket(newSocket);

    // Cleanup on unmount
    return () => {
      newSocket.close();
    };
  }, []);

  const sendMessage = (message: any) => {
    if (socket && isConnected) {
      socket.emit('message', message);
    }
  };

  const triggerEmergencyStop = () => {
    if (socket && isConnected) {
      socket.emit('emergency_stop');
      toast.error('Emergency stop signal sent');
    }
  };

  const value: WebSocketContextType = {
    socket,
    isConnected,
    latestSafetyUpdate,
    emergencyAlert,
    sendMessage,
    triggerEmergencyStop,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};