"""
Pydantic models for API data validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ..core.vlm_safety_engine import RiskLevel, SafetyReport


class SensorDataRequest(BaseModel):
    """Sensor data input model"""
    radiation_level: float = Field(..., ge=0, description="Radiation level in mSv/h")
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Humidity percentage")
    pressure: float = Field(..., ge=0, description="Atmospheric pressure in hPa")
    gas_concentration: float = Field(..., ge=0, description="Gas concentration")
    vibration_level: float = Field(..., ge=0, description="Vibration level")


class AnalysisRequest(BaseModel):
    """Request model for safety analysis"""
    sensor_data: Optional[Dict[str, float]] = None
    visual_data: Optional[str] = None  # Base64 encoded image
    query: Optional[str] = None


class SafetyReportResponse(BaseModel):
    """Safety report response model"""
    id: str
    timestamp: datetime
    risk_level: str
    confidence: float
    status: str
    explanation: str
    recommendations: List[str]
    sensor_data: Dict[str, Any]
    visual_analysis: str
    emergency_required: bool
    
    @classmethod
    def from_safety_report(cls, report: SafetyReport, report_id: str = None):
        """Convert SafetyReport to response model"""
        import uuid
        return cls(
            id=report_id or str(uuid.uuid4()),
            timestamp=report.timestamp,
            risk_level=report.risk_level.name,
            confidence=report.confidence,
            status=report.status,
            explanation=report.explanation,
            recommendations=report.recommendations,
            sensor_data=report.sensor_data,
            visual_analysis=report.visual_analysis,
            emergency_required=report.emergency_required
        )


class EmergencyAlert(BaseModel):
    """Emergency alert model"""
    id: str
    timestamp: datetime
    risk_level: RiskLevel
    description: str
    recommendations: List[str]
    auto_triggered: bool = True
    acknowledged: bool = False
    resolved: bool = False


class SystemStatus(BaseModel):
    """System status model"""
    timestamp: datetime
    risk_level: RiskLevel
    emergency_active: bool
    systems_operational: bool
    connected_clients: int
    uptime: Optional[str] = None


class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class HistoricalDataRequest(BaseModel):
    """Request for historical data"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    risk_level_filter: Optional[List[str]] = None


class DashboardConfig(BaseModel):
    """Dashboard configuration model"""
    refresh_interval: int = Field(default=2000, description="Refresh interval in ms")
    alert_thresholds: Dict[str, float]
    display_preferences: Dict[str, Any]
    notification_settings: Dict[str, bool]