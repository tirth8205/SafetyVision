"""
Thermal camera interface for temperature monitoring and analysis
"""

import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class ThermalAnomaly(Enum):
    """Types of thermal anomalies"""
    OVERHEATING = "overheating"
    COLD_SPOT = "cold_spot"
    HEAT_LEAK = "heat_leak"
    EQUIPMENT_FAILURE = "equipment_failure"
    FIRE_RISK = "fire_risk"
    INSULATION_ISSUE = "insulation_issue"


class ThermalSeverity(Enum):
    """Thermal anomaly severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ThermalReading:
    """Individual thermal measurement"""
    location: Tuple[int, int]     # Pixel coordinates
    temperature: float            # Celsius
    timestamp: datetime
    world_coords: Optional[Tuple[float, float]] = None  # World coordinates if available


@dataclass
class ThermalAnomaly:
    """Detected thermal anomaly"""
    anomaly_type: ThermalAnomaly
    severity: ThermalSeverity
    bounding_box: Tuple[int, int, int, int]  # (x, y, width, height)
    avg_temperature: float
    max_temperature: float
    min_temperature: float
    confidence: float
    description: str
    timestamp: datetime
    area_pixels: int


class ThermalCamera:
    """
    Thermal camera interface for nuclear facility monitoring
    
    Provides temperature measurement, thermal imaging, and anomaly detection
    for equipment monitoring and safety assessment.
    """
    
    def __init__(self, camera_id: int = 0, calibration_file: Optional[str] = None):
        self.camera_id = camera_id
        self.calibration_file = calibration_file
        self.is_connected = False
        self.current_frame = None
        self.temperature_map = None
        
        # Temperature thresholds (Celsius)
        self.thresholds = {
            'normal_min': 15.0,
            'normal_max': 35.0,
            'warning_hot': 60.0,
            'critical_hot': 80.0,
            'warning_cold': 5.0,
            'critical_cold': -10.0,
            'fire_risk': 100.0
        }
        
        # Detection parameters
        self.anomaly_min_area = 100  # Minimum pixels for anomaly detection
        self.confidence_threshold = 0.6
        self.temporal_smoothing = 0.3  # For temporal noise reduction
        
        # Calibration parameters
        self.temp_scale = 1.0
        self.temp_offset = 0.0
        self.emissivity = 0.95  # Default emissivity for most materials
        
        # History for temporal analysis
        self.frame_history = []
        self.anomaly_history = []
        self.max_history_frames = 30
        
        # Callbacks for alerts
        self.alert_callbacks = []
        
        logger.info(f"Thermal camera initialized (ID: {camera_id})")
    
    async def connect(self) -> bool:
        """Connect to thermal camera"""
        try:
            # In production, would interface with actual thermal camera hardware
            # For demo, simulate connection
            
            logger.info(f"Connecting to thermal camera {self.camera_id}")
            
            # Load calibration if available
            if self.calibration_file:
                await self._load_calibration()
            
            self.is_connected = True
            logger.info("Thermal camera connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to thermal camera: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from thermal camera"""
        self.is_connected = False
        logger.info("Thermal camera disconnected")
    
    async def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture thermal frame and convert to temperature map
        
        Returns:
            Temperature map as numpy array (temperatures in Celsius)
        """
        if not self.is_connected:
            logger.warning("Thermal camera not connected")
            return None
        
        try:
            # In production, would capture from actual thermal camera
            # For demo, generate realistic thermal data
            
            height, width = 240, 320  # Typical thermal camera resolution
            
            # Generate base temperature map
            base_temp = 25.0  # Room temperature
            temp_map = np.full((height, width), base_temp, dtype=np.float32)
            
            # Add some realistic thermal patterns
            
            # Hot spots (equipment)
            hot_spots = [
                ((80, 60), 45.0, 20),   # Equipment panel
                ((200, 150), 55.0, 15), # Motor
                ((120, 180), 40.0, 25)  # Electronics
            ]
            
            for (cx, cy), temp, radius in hot_spots:
                y, x = np.ogrid[:height, :width]
                mask = (x - cx)**2 + (y - cy)**2 <= radius**2
                temp_map[mask] = temp + np.random.normal(0, 2.0, np.sum(mask))
            
            # Cold spots (ventilation)
            cold_spots = [
                ((50, 200), 18.0, 15),
                ((250, 80), 20.0, 12)
            ]
            
            for (cx, cy), temp, radius in cold_spots:
                y, x = np.ogrid[:height, :width]
                mask = (x - cx)**2 + (y - cy)**2 <= radius**2
                temp_map[mask] = temp + np.random.normal(0, 1.0, np.sum(mask))
            
            # Add noise
            temp_map += np.random.normal(0, 0.5, temp_map.shape)
            
            # Apply calibration
            temp_map = temp_map * self.temp_scale + self.temp_offset
            
            # Store current frame
            self.current_frame = temp_map
            self.temperature_map = temp_map
            
            # Add to history
            self.frame_history.append({
                'temperature_map': temp_map.copy(),
                'timestamp': datetime.now()
            })
            
            # Limit history size
            if len(self.frame_history) > self.max_history_frames:
                self.frame_history.pop(0)
            
            return temp_map
            
        except Exception as e:
            logger.error(f"Error capturing thermal frame: {e}")
            return None
    
    async def analyze_thermal_anomalies(self, 
                                      temperature_map: Optional[np.ndarray] = None) -> List[ThermalAnomaly]:
        """
        Analyze thermal frame for anomalies
        
        Args:
            temperature_map: Optional temperature map to analyze (uses current if None)
            
        Returns:
            List of detected thermal anomalies
        """
        if temperature_map is None:
            temperature_map = self.temperature_map
        
        if temperature_map is None:
            return []
        
        anomalies = []
        
        # Detect overheating
        anomalies.extend(await self._detect_overheating(temperature_map))
        
        # Detect cold spots
        anomalies.extend(await self._detect_cold_spots(temperature_map))
        
        # Detect temperature gradients (heat leaks)
        anomalies.extend(await self._detect_heat_leaks(temperature_map))
        
        # Detect equipment issues
        anomalies.extend(await self._detect_equipment_anomalies(temperature_map))
        
        # Store anomaly history
        self.anomaly_history.extend(anomalies)
        
        # Trigger alerts for critical anomalies
        for anomaly in anomalies:
            if anomaly.severity in [ThermalSeverity.HIGH, ThermalSeverity.CRITICAL]:
                await self._trigger_thermal_alert(anomaly)
        
        return anomalies
    
    async def _detect_overheating(self, temperature_map: np.ndarray) -> List[ThermalAnomaly]:
        """Detect overheating anomalies"""
        anomalies = []
        
        try:
            # Create masks for different temperature thresholds
            critical_mask = temperature_map > self.thresholds['critical_hot']
            warning_mask = (temperature_map > self.thresholds['warning_hot']) & ~critical_mask
            fire_risk_mask = temperature_map > self.thresholds['fire_risk']
            
            # Process critical overheating
            if np.any(critical_mask):
                anomalies.extend(self._process_temperature_regions(
                    critical_mask, temperature_map, ThermalAnomaly.OVERHEATING, 
                    ThermalSeverity.CRITICAL, "Critical overheating detected"
                ))
            
            # Process fire risk
            if np.any(fire_risk_mask):
                anomalies.extend(self._process_temperature_regions(
                    fire_risk_mask, temperature_map, ThermalAnomaly.FIRE_RISK,
                    ThermalSeverity.CRITICAL, "Fire risk - extreme temperature detected"
                ))
            
            # Process warning level overheating
            if np.any(warning_mask):
                anomalies.extend(self._process_temperature_regions(
                    warning_mask, temperature_map, ThermalAnomaly.OVERHEATING,
                    ThermalSeverity.HIGH, "Warning level overheating detected"
                ))
                
        except Exception as e:
            logger.error(f"Error in overheating detection: {e}")
        
        return anomalies
    
    async def _detect_cold_spots(self, temperature_map: np.ndarray) -> List[ThermalAnomaly]:
        """Detect unusual cold spots"""
        anomalies = []
        
        try:
            critical_cold_mask = temperature_map < self.thresholds['critical_cold']
            warning_cold_mask = (temperature_map < self.thresholds['warning_cold']) & ~critical_cold_mask
            
            if np.any(critical_cold_mask):
                anomalies.extend(self._process_temperature_regions(
                    critical_cold_mask, temperature_map, ThermalAnomaly.COLD_SPOT,
                    ThermalSeverity.HIGH, "Critical cold spot detected"
                ))
            
            if np.any(warning_cold_mask):
                anomalies.extend(self._process_temperature_regions(
                    warning_cold_mask, temperature_map, ThermalAnomaly.COLD_SPOT,
                    ThermalSeverity.MEDIUM, "Cold spot detected"
                ))
                
        except Exception as e:
            logger.error(f"Error in cold spot detection: {e}")
        
        return anomalies
    
    async def _detect_heat_leaks(self, temperature_map: np.ndarray) -> List[ThermalAnomaly]:
        """Detect heat leaks using gradient analysis"""
        anomalies = []
        
        try:
            # Calculate temperature gradients
            grad_x = cv2.Sobel(temperature_map, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(temperature_map, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # Detect high gradient areas (potential heat leaks)
            high_gradient_threshold = np.percentile(gradient_magnitude, 95)
            heat_leak_mask = gradient_magnitude > high_gradient_threshold
            
            # Filter by minimum area and temperature
            heat_leak_mask = heat_leak_mask & (temperature_map > self.thresholds['normal_max'])
            
            if np.any(heat_leak_mask):
                anomalies.extend(self._process_temperature_regions(
                    heat_leak_mask, temperature_map, ThermalAnomaly.HEAT_LEAK,
                    ThermalSeverity.MEDIUM, "Potential heat leak detected"
                ))
                
        except Exception as e:
            logger.error(f"Error in heat leak detection: {e}")
        
        return anomalies
    
    async def _detect_equipment_anomalies(self, temperature_map: np.ndarray) -> List[ThermalAnomaly]:
        """Detect equipment-related thermal anomalies"""
        anomalies = []
        
        try:
            # Detect equipment with unusual temperature patterns
            # This would typically use knowledge of expected equipment temperatures
            
            # For demo, detect regions that are significantly hotter than surroundings
            blurred = cv2.GaussianBlur(temperature_map, (15, 15), 0)
            temp_diff = temperature_map - blurred
            
            # Equipment failure often shows up as hot spots relative to surroundings
            equipment_issue_mask = temp_diff > 10.0  # 10°C hotter than surroundings
            
            if np.any(equipment_issue_mask):
                anomalies.extend(self._process_temperature_regions(
                    equipment_issue_mask, temperature_map, ThermalAnomaly.EQUIPMENT_FAILURE,
                    ThermalSeverity.HIGH, "Equipment thermal anomaly detected"
                ))
                
        except Exception as e:
            logger.error(f"Error in equipment anomaly detection: {e}")
        
        return anomalies
    
    def _process_temperature_regions(self, 
                                   mask: np.ndarray, 
                                   temperature_map: np.ndarray,
                                   anomaly_type: ThermalAnomaly,
                                   severity: ThermalSeverity,
                                   description: str) -> List[ThermalAnomaly]:
        """Process temperature regions from mask"""
        anomalies = []
        
        try:
            # Find connected components
            contours, _ = cv2.findContours(
                mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < self.anomaly_min_area:
                    continue
                
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Create region mask
                region_mask = np.zeros_like(mask, dtype=bool)
                cv2.fillPoly(region_mask, [contour], True)
                
                # Calculate temperature statistics for this region
                region_temps = temperature_map[region_mask]
                avg_temp = float(np.mean(region_temps))
                max_temp = float(np.max(region_temps))
                min_temp = float(np.min(region_temps))
                
                # Calculate confidence based on temperature deviation and area
                temp_deviation = abs(avg_temp - np.mean(temperature_map))
                confidence = min(0.9, (temp_deviation / 20.0) + (area / 10000.0))
                
                anomaly = ThermalAnomaly(
                    anomaly_type=anomaly_type,
                    severity=severity,
                    bounding_box=(x, y, w, h),
                    avg_temperature=avg_temp,
                    max_temperature=max_temp,
                    min_temperature=min_temp,
                    confidence=confidence,
                    description=description,
                    timestamp=datetime.now(),
                    area_pixels=int(area)
                )
                
                anomalies.append(anomaly)
                
        except Exception as e:
            logger.error(f"Error processing temperature regions: {e}")
        
        return anomalies
    
    async def _trigger_thermal_alert(self, anomaly: ThermalAnomaly):
        """Trigger alert for thermal anomaly"""
        alert_data = {
            'type': 'thermal_anomaly',
            'anomaly_type': anomaly.anomaly_type.value,
            'severity': anomaly.severity.name,
            'temperature': {
                'avg': anomaly.avg_temperature,
                'max': anomaly.max_temperature,
                'min': anomaly.min_temperature
            },
            'location': anomaly.bounding_box,
            'confidence': anomaly.confidence,
            'description': anomaly.description,
            'timestamp': anomaly.timestamp
        }
        
        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert_data)
                else:
                    callback(alert_data)
            except Exception as e:
                logger.error(f"Error in thermal alert callback: {e}")
        
        logger.warning(f"Thermal alert: {anomaly.description} - {anomaly.avg_temperature:.1f}°C")
    
    async def _load_calibration(self):
        """Load thermal camera calibration data"""
        try:
            # In production, would load actual calibration file
            # For demo, use default values
            self.temp_scale = 1.0
            self.temp_offset = 0.0
            logger.info("Thermal camera calibration loaded")
        except Exception as e:
            logger.error(f"Error loading calibration: {e}")
    
    def get_temperature_at_point(self, x: int, y: int) -> Optional[float]:
        """Get temperature at specific pixel coordinates"""
        if self.temperature_map is None:
            return None
        
        height, width = self.temperature_map.shape
        if 0 <= x < width and 0 <= y < height:
            return float(self.temperature_map[y, x])
        
        return None
    
    def get_temperature_statistics(self, 
                                 region: Optional[Tuple[int, int, int, int]] = None) -> Dict[str, float]:
        """Get temperature statistics for region or entire frame"""
        if self.temperature_map is None:
            return {}
        
        if region:
            x, y, w, h = region
            temp_region = self.temperature_map[y:y+h, x:x+w]
        else:
            temp_region = self.temperature_map
        
        return {
            'min': float(np.min(temp_region)),
            'max': float(np.max(temp_region)),
            'mean': float(np.mean(temp_region)),
            'median': float(np.median(temp_region)),
            'std': float(np.std(temp_region))
        }
    
    def create_thermal_visualization(self, 
                                   colormap: int = cv2.COLORMAP_JET,
                                   temp_range: Optional[Tuple[float, float]] = None) -> Optional[np.ndarray]:
        """Create thermal visualization image"""
        if self.temperature_map is None:
            return None
        
        try:
            # Normalize temperature map
            if temp_range:
                min_temp, max_temp = temp_range
                normalized = np.clip((self.temperature_map - min_temp) / (max_temp - min_temp), 0, 1)
            else:
                min_temp = np.min(self.temperature_map)
                max_temp = np.max(self.temperature_map)
                normalized = (self.temperature_map - min_temp) / (max_temp - min_temp)
            
            # Convert to 8-bit
            normalized_8bit = (normalized * 255).astype(np.uint8)
            
            # Apply colormap
            colored = cv2.applyColorMap(normalized_8bit, colormap)
            
            return colored
            
        except Exception as e:
            logger.error(f"Error creating thermal visualization: {e}")
            return None
    
    def register_alert_callback(self, callback: Callable):
        """Register callback for thermal alerts"""
        self.alert_callbacks.append(callback)
    
    def get_anomaly_history(self, minutes: int = 60) -> List[ThermalAnomaly]:
        """Get thermal anomaly history for specified time period"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            anomaly for anomaly in self.anomaly_history
            if anomaly.timestamp > cutoff_time
        ]
    
    def export_thermal_data(self, filename: str):
        """Export current thermal data to file"""
        if self.temperature_map is None:
            logger.warning("No thermal data to export")
            return
        
        try:
            # Export as numpy array
            np.save(filename, self.temperature_map)
            logger.info(f"Thermal data exported to {filename}")
        except Exception as e:
            logger.error(f"Error exporting thermal data: {e}")