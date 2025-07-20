"""
FastAPI Backend for SafetyVision Dashboard
Real-time safety monitoring API with WebSocket support
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
import logging
from datetime import datetime, timedelta
import uuid

from ..core.vlm_safety_engine import VLMSafetyEngine, SensorReading, RiskLevel
from .models import (
    SafetyReportResponse, 
    SensorDataRequest, 
    EmergencyAlert,
    SystemStatus,
    AnalysisRequest
)
from .database import DatabaseManager
from .websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SafetyVision API",
    description="Real-time nuclear facility safety monitoring API",
    version="2.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
safety_engine = VLMSafetyEngine()
db_manager = DatabaseManager()
connection_manager = ConnectionManager()

class SafetyMonitor:
    """Real-time safety monitoring service"""
    
    def __init__(self):
        self.is_running = False
        self.current_risk_level = RiskLevel.MINIMAL
        self.emergency_active = False
        
    async def start_monitoring(self):
        """Start real-time monitoring loop"""
        self.is_running = True
        while self.is_running:
            try:
                # Generate simulated sensor data
                sensor_data = self._generate_sensor_data()
                
                # Analyze safety conditions
                safety_report = await safety_engine.analyze_environment_async(
                    visual_data=None,  # Would be camera feed
                    sensor_data=sensor_data,
                    query="Continuous safety monitoring"
                )
                
                # Store in database
                await db_manager.store_safety_report(safety_report)
                
                # Broadcast to connected clients
                await connection_manager.broadcast({
                    "type": "safety_update",
                    "data": {
                        "timestamp": datetime.now().isoformat(),
                        "risk_level": safety_report.risk_level.name,
                        "sensor_data": sensor_data.__dict__,
                        "confidence": safety_report.confidence,
                        "status": safety_report.status,
                        "recommendations": safety_report.recommendations
                    }
                })
                
                # Check for emergency conditions
                if safety_report.emergency_required and not self.emergency_active:
                    await self._trigger_emergency(safety_report)
                
                await asyncio.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)
    
    def _generate_sensor_data(self) -> SensorReading:
        """Generate realistic sensor data"""
        import numpy as np
        base_radiation = 0.1
        radiation_noise = np.random.normal(0, 0.02)
        
        return SensorReading(
            radiation_level=max(0, base_radiation + radiation_noise),
            temperature=np.random.normal(25, 3),
            humidity=np.random.normal(60, 10),
            pressure=np.random.normal(1013, 5),
            gas_concentration=np.random.exponential(0.1),
            vibration_level=np.random.exponential(0.05)
        )
    
    async def _trigger_emergency(self, safety_report):
        """Trigger emergency protocols"""
        self.emergency_active = True
        emergency_alert = EmergencyAlert(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            risk_level=safety_report.risk_level,
            description=safety_report.explanation,
            recommendations=safety_report.recommendations,
            auto_triggered=True
        )
        
        await db_manager.store_emergency_alert(emergency_alert)
        await connection_manager.broadcast({
            "type": "emergency_alert",
            "data": emergency_alert.dict()
        })

# Initialize monitor
safety_monitor = SafetyMonitor()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await db_manager.initialize()
    # Start monitoring in background
    asyncio.create_task(safety_monitor.start_monitoring())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await connection_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message.get("type") == "emergency_stop":
                await handle_emergency_stop()
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

@app.get("/api/status")
async def get_system_status() -> SystemStatus:
    """Get current system status"""
    return SystemStatus(
        timestamp=datetime.now(),
        risk_level=safety_monitor.current_risk_level,
        emergency_active=safety_monitor.emergency_active,
        systems_operational=True,
        connected_clients=len(connection_manager.active_connections)
    )

@app.get("/api/safety-reports")
async def get_safety_reports(
    limit: int = 100,
    start_time: Optional[datetime] = None
) -> List[SafetyReportResponse]:
    """Get historical safety reports"""
    return await db_manager.get_safety_reports(limit=limit, start_time=start_time)

@app.post("/api/analyze")
async def analyze_environment(request: AnalysisRequest) -> SafetyReportResponse:
    """Trigger manual safety analysis"""
    try:
        sensor_data = SensorReading(**request.sensor_data) if request.sensor_data else None
        
        safety_report = await safety_engine.analyze_environment_async(
            visual_data=request.visual_data,
            sensor_data=sensor_data,
            query=request.query or "Manual safety analysis"
        )
        
        await db_manager.store_safety_report(safety_report)
        
        return SafetyReportResponse.from_safety_report(safety_report)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emergency/trigger")
async def trigger_manual_emergency():
    """Manually trigger emergency protocols"""
    emergency_alert = EmergencyAlert(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        risk_level=RiskLevel.CRITICAL,
        description="Manual emergency activation",
        recommendations=["Evacuate immediately", "Shut down all systems"],
        auto_triggered=False
    )
    
    safety_monitor.emergency_active = True
    await db_manager.store_emergency_alert(emergency_alert)
    await connection_manager.broadcast({
        "type": "emergency_alert",
        "data": emergency_alert.dict()
    })
    
    return {"status": "Emergency protocols activated"}

@app.post("/api/emergency/clear")
async def clear_emergency():
    """Clear emergency status"""
    safety_monitor.emergency_active = False
    await connection_manager.broadcast({
        "type": "emergency_cleared",
        "data": {"timestamp": datetime.now().isoformat()}
    })
    
    return {"status": "Emergency status cleared"}

async def handle_emergency_stop():
    """Handle emergency stop command from WebSocket"""
    safety_monitor.emergency_active = True
    await connection_manager.broadcast({
        "type": "emergency_stop",
        "data": {
            "timestamp": datetime.now().isoformat(),
            "message": "Emergency stop activated"
        }
    })

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "safety_engine": "operational",
            "database": "connected" if db_manager.is_connected() else "disconnected",
            "monitoring": "active" if safety_monitor.is_running else "inactive"
        }
    }

# Serve React build files in production
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)