"""
Multi-modal sensor data fusion for comprehensive environmental monitoring
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class FusedSensorData:
    """Fused multi-modal sensor readings"""
    timestamp: datetime
    confidence: float
    anomaly_score: float
    risk_indicators: Dict[str, float]
    sensor_health: Dict[str, bool]
    environmental_summary: str

class SensorFusionEngine:
    """Advanced sensor fusion for nuclear facility monitoring"""
    
    def __init__(self):
        self.sensor_weights = {
            'radiation': 0.4,
            'temperature': 0.2,
            'gas_levels': 0.3,
            'vibration': 0.1
        }
        
    def fuse_sensor_data(self, sensor_readings: Dict) -> FusedSensorData:
        """Fuse multiple sensor modalities into unified assessment"""
        timestamp = datetime.now()
        
        # Extract individual sensor readings
        radiation = sensor_readings.get('radiation_level', 0.0)
        temperature = sensor_readings.get('temperature', 20.0)
        gas_levels = sensor_readings.get('gas_levels', {})
        vibration = sensor_readings.get('vibration', np.array([0.0]))
        pressure = sensor_readings.get('pressure', 101.3)
        
        # Calculate weighted risk indicators
        risk_indicators = {}
        
        # Radiation risk assessment
        if radiation > 2.0:
            risk_indicators['radiation'] = 1.0  # Critical
        elif radiation > 1.0:
            risk_indicators['radiation'] = 0.8  # High
        elif radiation > 0.5:
            risk_indicators['radiation'] = 0.4  # Medium
        else:
            risk_indicators['radiation'] = 0.1  # Low
            
        # Temperature risk assessment
        if temperature > 80:
            risk_indicators['temperature'] = 1.0
        elif temperature > 70:
            risk_indicators['temperature'] = 0.6
        elif temperature < 10:
            risk_indicators['temperature'] = 0.5
        else:
            risk_indicators['temperature'] = 0.1
            
        # Gas level risk assessment
        gas_risk = 0.1
        for gas, level in gas_levels.items():
            if gas == 'hydrogen' and level > 4000:
                gas_risk = max(gas_risk, 1.0)
            elif gas == 'methane' and level > 50000:
                gas_risk = max(gas_risk, 1.0)
            elif gas == 'carbon_monoxide' and level > 200:
                gas_risk = max(gas_risk, 1.0)
        risk_indicators['gas_levels'] = gas_risk
        
        # Vibration risk assessment
        if isinstance(vibration, np.ndarray) and len(vibration) > 0:
            vibration_rms = np.sqrt(np.mean(vibration**2))
            if vibration_rms > 25.0:
                risk_indicators['vibration'] = 1.0
            elif vibration_rms > 10.0:
                risk_indicators['vibration'] = 0.6
            else:
                risk_indicators['vibration'] = 0.1
        else:
            risk_indicators['vibration'] = 0.1
        
        # Calculate overall confidence based on sensor agreement
        risk_values = list(risk_indicators.values())
        risk_variance = np.var(risk_values) if len(risk_values) > 1 else 0.0
        confidence = float(max(0.5, 1.0 - risk_variance))  # Higher variance = lower confidence
        
        # Calculate anomaly score (deviation from expected normal values)
        expected_radiation = 0.1
        expected_temp = 45.0
        
        radiation_anomaly = abs(radiation - expected_radiation) / expected_radiation
        temp_anomaly = abs(temperature - expected_temp) / expected_temp
        anomaly_score = min(1.0, (radiation_anomaly + temp_anomaly) / 2.0)
        
        # Check sensor health (basic implementation)
        sensor_health = {
            'radiation_sensor': radiation >= 0 and radiation <= 10.0,
            'temperature_sensor': temperature >= -50 and temperature <= 150,
            'gas_sensors': all(level >= 0 for level in gas_levels.values()),
            'vibration_sensor': True,  # Assume healthy if data present
            'pressure_sensor': pressure > 0
        }
        
        # Generate environmental summary
        max_risk_sensor = max(risk_indicators.items(), key=lambda x: x[1])
        if max_risk_sensor[1] > 0.8:
            severity = "CRITICAL"
        elif max_risk_sensor[1] > 0.6:
            severity = "HIGH"
        elif max_risk_sensor[1] > 0.4:
            severity = "MODERATE"
        else:
            severity = "LOW"
            
        environmental_summary = f"{severity} risk detected. Primary concern: {max_risk_sensor[0]} (risk: {max_risk_sensor[1]:.2f})"
        
        return FusedSensorData(
            timestamp=timestamp,
            confidence=confidence,
            anomaly_score=anomaly_score,
            risk_indicators=risk_indicators,
            sensor_health=sensor_health,
            environmental_summary=environmental_summary
        )