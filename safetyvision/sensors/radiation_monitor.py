"""
Radiation monitoring interface for nuclear facility safety
"""

import asyncio
import logging
import numpy as np
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import threading
import json

logger = logging.getLogger(__name__)


class RadiationLevel(Enum):
    """Radiation safety levels"""
    BACKGROUND = 1      # < 0.1 mSv/h
    SAFE = 2           # 0.1 - 0.5 mSv/h
    ELEVATED = 3       # 0.5 - 1.0 mSv/h
    HIGH = 4           # 1.0 - 2.0 mSv/h
    DANGEROUS = 5      # 2.0 - 5.0 mSv/h
    EXTREME = 6        # > 5.0 mSv/h


class SensorStatus(Enum):
    """Radiation sensor status"""
    ONLINE = "online"
    OFFLINE = "offline"
    CALIBRATING = "calibrating"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class RadiationReading:
    """Individual radiation sensor reading"""
    sensor_id: str
    dose_rate: float              # mSv/h
    integrated_dose: float        # mSv (accumulated)
    timestamp: datetime
    location: Optional[tuple] = None  # (x, y, z)
    sensor_temp: Optional[float] = None  # Celsius
    battery_level: Optional[float] = None  # %
    status: SensorStatus = SensorStatus.ONLINE
    calibration_factor: float = 1.0
    quality_indicator: float = 1.0  # 0-1, confidence in reading


@dataclass
class RadiationMap:
    """Spatial radiation map"""
    grid_data: np.ndarray         # 2D array of dose rates
    resolution: float             # meters per pixel
    origin: tuple                 # (x, y) world coordinates of grid origin
    timestamp: datetime
    confidence_map: Optional[np.ndarray] = None  # Confidence for each grid cell


class RadiationMonitor:
    """
    Comprehensive radiation monitoring system for nuclear facilities
    
    Manages multiple radiation sensors, provides real-time monitoring,
    spatial mapping, and safety threshold management.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.sensors = {}  # sensor_id -> sensor_info
        self.readings_history = []  # Historical readings
        self.current_readings = {}  # sensor_id -> latest RadiationReading
        self.callbacks = []  # Alert callbacks
        
        # Safety thresholds (mSv/h)
        self.thresholds = {
            'background': 0.1,
            'safe_limit': 0.5,
            'warning': 1.0,
            'danger': 2.0,
            'extreme': 5.0,
            'evacuation': 10.0
        }
        
        # Monitoring parameters
        self.monitoring_active = False
        self.sample_interval = 1.0  # seconds
        self.history_retention = timedelta(hours=24)
        
        # Spatial mapping
        self.radiation_map = None
        self.map_resolution = 0.5  # meters per pixel
        self.map_size = (100, 100)  # grid size
        
        # Data logging
        self.log_file = "radiation_log.json"
        self.enable_logging = True
        
        logger.info("Radiation monitor initialized")
    
    def add_sensor(self, 
                   sensor_id: str,
                   location: tuple,
                   sensor_type: str = "geiger",
                   calibration_factor: float = 1.0):
        """Add a radiation sensor to the monitoring system"""
        sensor_info = {
            'id': sensor_id,
            'type': sensor_type,
            'location': location,
            'calibration_factor': calibration_factor,
            'status': SensorStatus.OFFLINE,
            'last_seen': None,
            'total_readings': 0,
            'error_count': 0
        }
        
        self.sensors[sensor_id] = sensor_info
        logger.info(f"Added radiation sensor {sensor_id} at location {location}")
    
    def register_callback(self, callback: Callable[[RadiationReading], None]):
        """Register callback for radiation threshold alerts"""
        self.callbacks.append(callback)
    
    async def start_monitoring(self):
        """Start continuous radiation monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        logger.info("Starting radiation monitoring")
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._sensor_polling_loop()),
            asyncio.create_task(self._map_update_loop()),
            asyncio.create_task(self._data_cleanup_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        finally:
            self.monitoring_active = False
    
    async def stop_monitoring(self):
        """Stop radiation monitoring"""
        self.monitoring_active = False
        logger.info("Radiation monitoring stopped")
    
    async def _sensor_polling_loop(self):
        """Main sensor polling loop"""
        while self.monitoring_active:
            try:
                # Poll all sensors
                for sensor_id in self.sensors.keys():
                    reading = await self._read_sensor(sensor_id)
                    if reading:
                        await self._process_reading(reading)
                
                await asyncio.sleep(self.sample_interval)
                
            except Exception as e:
                logger.error(f"Error in sensor polling: {e}")
                await asyncio.sleep(self.sample_interval)
    
    async def _read_sensor(self, sensor_id: str) -> Optional[RadiationReading]:
        """Read data from a specific radiation sensor"""
        sensor_info = self.sensors.get(sensor_id)
        if not sensor_info:
            return None
        
        try:
            # In production, this would interface with actual hardware
            # For demo, simulate realistic radiation readings
            
            base_reading = 0.08  # Background radiation
            location = sensor_info['location']
            
            # Add some spatial variation based on location
            spatial_factor = 1.0 + 0.3 * np.sin(location[0] * 0.1) * np.cos(location[1] * 0.1)
            
            # Add temporal noise
            noise = np.random.normal(0, 0.02)
            
            # Simulate occasional elevated readings
            if np.random.random() < 0.01:  # 1% chance of elevated reading
                elevated_factor = np.random.uniform(2.0, 5.0)
            else:
                elevated_factor = 1.0
            
            dose_rate = base_reading * spatial_factor * elevated_factor + noise
            dose_rate = max(0.0, dose_rate)  # Ensure non-negative
            
            # Apply calibration
            dose_rate *= sensor_info['calibration_factor']
            
            # Calculate integrated dose (simplified)
            prev_reading = self.current_readings.get(sensor_id)
            if prev_reading:
                time_diff = (datetime.now() - prev_reading.timestamp).total_seconds() / 3600.0  # hours
                integrated_dose = prev_reading.integrated_dose + dose_rate * time_diff
            else:
                integrated_dose = 0.0
            
            # Simulate sensor parameters
            sensor_temp = np.random.normal(25.0, 2.0)  # Room temperature
            battery_level = max(0, 100 - sensor_info['total_readings'] * 0.01)  # Slow battery drain
            quality = 1.0 if dose_rate < 10.0 else 0.8  # Quality degrades at high levels
            
            reading = RadiationReading(
                sensor_id=sensor_id,
                dose_rate=dose_rate,
                integrated_dose=integrated_dose,
                timestamp=datetime.now(),
                location=location,
                sensor_temp=sensor_temp,
                battery_level=battery_level,
                status=SensorStatus.ONLINE,
                calibration_factor=sensor_info['calibration_factor'],
                quality_indicator=quality
            )
            
            # Update sensor info
            sensor_info['status'] = SensorStatus.ONLINE
            sensor_info['last_seen'] = datetime.now()
            sensor_info['total_readings'] += 1
            
            return reading
            
        except Exception as e:
            logger.error(f"Error reading sensor {sensor_id}: {e}")
            sensor_info['status'] = SensorStatus.ERROR
            sensor_info['error_count'] += 1
            return None
    
    async def _process_reading(self, reading: RadiationReading):
        """Process a new radiation reading"""
        # Store reading
        self.current_readings[reading.sensor_id] = reading
        self.readings_history.append(reading)
        
        # Check thresholds and trigger alerts
        await self._check_safety_thresholds(reading)
        
        # Log data if enabled
        if self.enable_logging:
            await self._log_reading(reading)
        
        # Update radiation map
        await self._update_spatial_map(reading)
    
    async def _check_safety_thresholds(self, reading: RadiationReading):
        """Check reading against safety thresholds and trigger alerts"""
        dose_rate = reading.dose_rate
        level = self._classify_radiation_level(dose_rate)
        
        # Trigger alerts for concerning levels
        if level.value >= RadiationLevel.ELEVATED.value:
            alert_level = "WARNING" if level == RadiationLevel.ELEVATED else \
                         "ERROR" if level == RadiationLevel.HIGH else \
                         "CRITICAL"
            
            alert_data = {
                'level': alert_level,
                'sensor_id': reading.sensor_id,
                'dose_rate': dose_rate,
                'location': reading.location,
                'timestamp': reading.timestamp,
                'radiation_level': level.name
            }
            
            # Trigger callbacks
            for callback in self.callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(alert_data)
                    else:
                        callback(alert_data)
                except Exception as e:
                    logger.error(f"Error in radiation alert callback: {e}")
            
            logger.warning(f"Radiation {alert_level}: {dose_rate:.3f} mSv/h at {reading.location}")
    
    def _classify_radiation_level(self, dose_rate: float) -> RadiationLevel:
        """Classify radiation level based on dose rate"""
        if dose_rate < self.thresholds['background']:
            return RadiationLevel.BACKGROUND
        elif dose_rate < self.thresholds['safe_limit']:
            return RadiationLevel.SAFE
        elif dose_rate < self.thresholds['warning']:
            return RadiationLevel.ELEVATED
        elif dose_rate < self.thresholds['danger']:
            return RadiationLevel.HIGH
        elif dose_rate < self.thresholds['extreme']:
            return RadiationLevel.DANGEROUS
        else:
            return RadiationLevel.EXTREME
    
    async def _log_reading(self, reading: RadiationReading):
        """Log radiation reading to file"""
        try:
            log_entry = {
                'sensor_id': reading.sensor_id,
                'dose_rate': reading.dose_rate,
                'integrated_dose': reading.integrated_dose,
                'timestamp': reading.timestamp.isoformat(),
                'location': reading.location,
                'sensor_temp': reading.sensor_temp,
                'battery_level': reading.battery_level,
                'status': reading.status.value,
                'quality': reading.quality_indicator
            }
            
            # In production, would write to proper logging system
            # For demo, just log to console
            logger.debug(f"Radiation reading: {json.dumps(log_entry)}")
            
        except Exception as e:
            logger.error(f"Error logging radiation reading: {e}")
    
    async def _update_spatial_map(self, reading: RadiationReading):
        """Update spatial radiation map with new reading"""
        if not reading.location:
            return
        
        try:
            # Initialize map if needed
            if self.radiation_map is None:
                self.radiation_map = RadiationMap(
                    grid_data=np.full(self.map_size, self.thresholds['background']),
                    resolution=self.map_resolution,
                    origin=(0.0, 0.0),
                    timestamp=datetime.now(),
                    confidence_map=np.zeros(self.map_size)
                )
            
            # Convert world coordinates to grid indices
            x, y = reading.location[:2]  # Only use x, y
            grid_x = int((x - self.radiation_map.origin[0]) / self.map_resolution)
            grid_y = int((y - self.radiation_map.origin[1]) / self.map_resolution)
            
            # Check bounds
            if (0 <= grid_x < self.map_size[0] and 0 <= grid_y < self.map_size[1]):
                # Update grid with exponential smoothing
                alpha = 0.3  # Smoothing factor
                current_value = self.radiation_map.grid_data[grid_y, grid_x]
                new_value = alpha * reading.dose_rate + (1 - alpha) * current_value
                
                self.radiation_map.grid_data[grid_y, grid_x] = new_value
                self.radiation_map.confidence_map[grid_y, grid_x] = min(
                    1.0, self.radiation_map.confidence_map[grid_y, grid_x] + 0.1
                )
                self.radiation_map.timestamp = reading.timestamp
            
        except Exception as e:
            logger.error(f"Error updating radiation map: {e}")
    
    async def _map_update_loop(self):
        """Periodic radiation map processing"""
        while self.monitoring_active:
            try:
                await self._process_radiation_map()
                await asyncio.sleep(10.0)  # Update every 10 seconds
            except Exception as e:
                logger.error(f"Error in map update loop: {e}")
                await asyncio.sleep(10.0)
    
    async def _process_radiation_map(self):
        """Process and smooth radiation map"""
        if self.radiation_map is None:
            return
        
        try:
            # Apply Gaussian smoothing to interpolate between sensor points
            from scipy import ndimage
            
            # Only smooth areas with some confidence
            mask = self.radiation_map.confidence_map > 0.1
            if np.any(mask):
                smoothed = ndimage.gaussian_filter(
                    self.radiation_map.grid_data, 
                    sigma=2.0
                )
                
                # Apply smoothing only where we have confidence
                self.radiation_map.grid_data = np.where(
                    mask, 
                    0.7 * self.radiation_map.grid_data + 0.3 * smoothed,
                    self.radiation_map.grid_data
                )
        
        except ImportError:
            # Fallback if scipy not available
            pass
        except Exception as e:
            logger.error(f"Error processing radiation map: {e}")
    
    async def _data_cleanup_loop(self):
        """Clean up old data periodically"""
        while self.monitoring_active:
            try:
                await self._cleanup_old_data()
                await asyncio.sleep(3600.0)  # Clean up every hour
            except Exception as e:
                logger.error(f"Error in data cleanup: {e}")
                await asyncio.sleep(3600.0)
    
    async def _cleanup_old_data(self):
        """Remove old readings to prevent memory issues"""
        cutoff_time = datetime.now() - self.history_retention
        
        original_count = len(self.readings_history)
        self.readings_history = [
            reading for reading in self.readings_history
            if reading.timestamp > cutoff_time
        ]
        
        removed_count = original_count - len(self.readings_history)
        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} old radiation readings")
    
    def get_current_levels(self) -> Dict[str, RadiationReading]:
        """Get current radiation levels from all sensors"""
        return self.current_readings.copy()
    
    def get_area_reading(self, location: tuple, radius: float = 5.0) -> Optional[float]:
        """Get average radiation reading for an area"""
        if not self.current_readings:
            return None
        
        nearby_readings = []
        for reading in self.current_readings.values():
            if reading.location:
                distance = np.sqrt(
                    (location[0] - reading.location[0])**2 + 
                    (location[1] - reading.location[1])**2
                )
                if distance <= radius:
                    nearby_readings.append(reading.dose_rate)
        
        return np.mean(nearby_readings) if nearby_readings else None
    
    def get_sensor_status(self) -> Dict[str, Dict]:
        """Get status of all sensors"""
        status = {}
        for sensor_id, sensor_info in self.sensors.items():
            current_reading = self.current_readings.get(sensor_id)
            
            status[sensor_id] = {
                'status': sensor_info['status'].value,
                'location': sensor_info['location'],
                'last_seen': sensor_info['last_seen'],
                'total_readings': sensor_info['total_readings'],
                'error_count': sensor_info['error_count'],
                'current_dose_rate': current_reading.dose_rate if current_reading else None,
                'battery_level': current_reading.battery_level if current_reading else None
            }
        
        return status
    
    def get_radiation_map(self) -> Optional[RadiationMap]:
        """Get current radiation map"""
        return self.radiation_map
    
    def export_data(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Export radiation data for specified time range"""
        exported_data = []
        
        for reading in self.readings_history:
            if start_time <= reading.timestamp <= end_time:
                exported_data.append({
                    'sensor_id': reading.sensor_id,
                    'dose_rate': reading.dose_rate,
                    'integrated_dose': reading.integrated_dose,
                    'timestamp': reading.timestamp.isoformat(),
                    'location': reading.location,
                    'sensor_temp': reading.sensor_temp,
                    'battery_level': reading.battery_level,
                    'quality': reading.quality_indicator
                })
        
        return exported_data