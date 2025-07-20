#!/bin/bash

# SafetyVision Simple Dashboard Startup Script

echo "🔬 Starting SafetyVision Simple Dashboard..."

# Check if we're in the right directory
if [ ! -f "safetyvision/api/main.py" ]; then
    echo "❌ Error: Please run this script from the SafetyVision root directory"
    exit 1
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
pip install -r requirements-api.txt

# Start FastAPI backend
echo "🚀 Starting FastAPI backend..."
cd safetyvision
python -m api.main &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start simple HTTP server for frontend
echo "🌐 Starting simple dashboard..."
cd ../frontend-simple
python3 -m http.server 3000 &
FRONTEND_PID=$!

echo "✅ Dashboard started successfully!"
echo ""
echo "🎯 Available services:"
echo "  • Dashboard: http://localhost:3000"
echo "  • API: http://localhost:8000"
echo "  • WebSocket: ws://localhost:8000/ws"
echo ""
echo "🚀 Features:"
echo "  • Real-time sensor monitoring"
echo "  • WebSocket live updates"
echo "  • Emergency alert system"
echo "  • VLM analysis simulation"
echo "  • Dark theme optimized for monitoring"
echo ""
echo "🛑 To stop:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  or press Ctrl+C"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Setup signal handlers
trap cleanup SIGINT SIGTERM

# Keep script running
wait