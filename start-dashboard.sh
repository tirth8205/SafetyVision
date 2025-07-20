#!/bin/bash

# SafetyVision Modern Dashboard Startup Script

echo "🔬 Starting SafetyVision Modern Dashboard..."

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

echo "✅ FastAPI backend started (PID: $BACKEND_PID)"
echo "📡 API available at: http://localhost:8000"
echo "📊 WebSocket endpoint: ws://localhost:8000/ws"
echo ""
echo "🎯 Modern dashboard features:"
echo "  • Real-time WebSocket updates"
echo "  • Material-UI dark theme"
echo "  • Advanced safety visualizations"
echo "  • Historical data analysis"
echo "  • Emergency alert system"
echo ""
echo "📝 To start the React frontend:"
echo "  cd frontend"
echo "  npm install"
echo "  npm start"
echo ""
echo "🛑 To stop the backend: kill $BACKEND_PID"

# Keep script running to maintain backend
wait $BACKEND_PID