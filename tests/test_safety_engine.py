"""
Test suite for VLM Safety Engine
"""

import pytest
import numpy as np
import asyncio
from datetime import datetime
from safetyvision.core.vlm_safety_engine import (
    VLMSafetyEngine, 
    SensorReading, 
    RiskLevel,
    create_demo_sensor_reading
)

class TestVLMSafetyEngine:
    """Test cases for VLM Safety Engine"""
    
    @pytest.fixture
    def safety_engine(self):
        """Create safety engine instance for testing"""
        return VLMSafetyEngine()
    
    @pytest.fixture
    def demo_image(self):
        """Create demo image for testing"""
        return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    @pytest.fixture
    def safe_sensor_data(self):
        """Create safe sensor readings"""
        return SensorReading(
            radiation_level=0.1,  # Safe level
            temperature=45.0,
            humidity=65.0,
            pressure=101.3,
            gas_levels={'hydrogen': 100, 'methane': 50},
            vibration=np.random.normal(0, 0.05, 100),
            timestamp=datetime.now()
        )
    
    @pytest.fixture
    def dangerous_sensor_data(self):
        """Create dangerous sensor readings"""
        return SensorReading(
            radiation_level=1.5,  # Dangerous level
            temperature=85.0,     # High temperature
            humidity=65.0,
            pressure=101.3,
            gas_levels={'hydrogen': 5000, 'methane': 200},  # High gas levels
            vibration=np.random.normal(0, 0.2, 100),
            timestamp=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_safe_environment_analysis(self, safety_engine, demo_image, safe_sensor_data):
        """Test analysis of safe environment"""
        report = await safety_engine.analyze_environment(
            visual_data=demo_image,
            sensor_data=safe_sensor_data,
            query="Is this environment safe?"
        )
        
        assert report.risk_level in [RiskLevel.MINIMAL, RiskLevel.LOW]
        assert not report.emergency_required
        assert report.confidence > 0.5
        assert "safe" in report.status.lower()
    
    @pytest.mark.asyncio
    async def test_dangerous_environment_analysis(self, safety_engine, demo_image, dangerous_sensor_data):
        """Test analysis of dangerous environment"""
        report = await safety_engine.analyze_environment(
            visual_data=demo_image,
            sensor_data=dangerous_sensor_data,
            query="Assess current safety conditions"
        )
        
        assert report.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert report.emergency_required
        assert report.confidence > 0.5
        assert len(report.recommendations) > 0
    
    def test_sensor_alert_generation(self, safety_engine, dangerous_sensor_data):
        """Test sensor alert generation"""
        alerts = safety_engine._analyze_sensor_data(dangerous_sensor_data)
        
        assert len(alerts) > 0
        assert any("radiation" in alert.lower() for alert in alerts)
        assert any("CRITICAL" in alert or "DANGER" in alert for alert in alerts)
    
    def test_risk_level_classification(self, safety_engine):
        """Test risk level classification logic"""
        # Test safe conditions
        safe_data = create_demo_sensor_reading()
        safe_data.radiation_level = 0.1
        alerts = safety_engine._analyze_sensor_data(safe_data)
        assert len([a for a in alerts if "CRITICAL" in a]) == 0
        
        # Test dangerous conditions
        dangerous_data = create_demo_sensor_reading()
        dangerous_data.radiation_level = 2.0
        alerts = safety_engine._analyze_sensor_data(dangerous_data)
        assert len([a for a in alerts if "CRITICAL" in a]) > 0
    
    def test_decision_explanation(self, safety_engine):
        """Test safety decision explanation"""
        from safetyvision.core.vlm_safety_engine import SafetyReport
        
        report = SafetyReport(
            timestamp=datetime.now(),
            risk_level=RiskLevel.HIGH,
            confidence=0.9,
            status="UNSAFE - High radiation detected",
            explanation="Elevated radiation levels exceed safety thresholds",
            recommendations=["Evacuate area", "Investigate source"],
            sensor_data={},
            visual_analysis="Equipment shows warning indicators",
            emergency_required=True
        )
        
        explanation = safety_engine.explain_decision(report, "Why is this dangerous?")
        assert len(explanation) > 100
        assert "radiation" in explanation.lower()