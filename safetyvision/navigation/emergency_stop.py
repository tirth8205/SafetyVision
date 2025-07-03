"""
Emergency stop system for critical safety situations
"""

import asyncio
import logging
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EmergencyLevel(Enum):
    """Emergency severity levels"""
    LOW = 1          # Controlled stop
    MEDIUM = 2       # Immediate stop
    HIGH = 3         # Emergency stop with alerts
    CRITICAL = 4     # Full system shutdown


@dataclass
class EmergencyEvent:
    """Emergency event data structure"""
    level: EmergencyLevel
    trigger: str
    description: str
    timestamp: datetime
    sensor_data: Dict
    location: Optional[tuple] = None
    requires_evacuation: bool = False


class EmergencyStopSystem:
    """
    Emergency stop system for nuclear facility robots
    
    Provides multiple levels of emergency response from controlled stops
    to full system shutdowns with evacuation protocols.
    """
    
    def __init__(self):
        self.is_emergency_active = False
        self.current_emergency = None
        self.stop_callbacks = []
        self.alert_callbacks = []
        self.emergency_history = []
        
        # Emergency thresholds
        self.thresholds = {
            'radiation_critical': 2.0,      # mSv/h
            'radiation_high': 1.0,          # mSv/h
            'temperature_critical': 80,     # Celsius
            'gas_critical': {
                'hydrogen': 4000,           # ppm
                'carbon_monoxide': 200,     # ppm
            },
            'vibration_critical': 25.0,     # mm/s
            'proximity_emergency': 0.5      # meters
        }
        
        logger.info("Emergency stop system initialized")
    
    def register_stop_callback(self, callback: Callable):
        """Register callback for emergency stop actions"""
        self.stop_callbacks.append(callback)
    
    def register_alert_callback(self, callback: Callable):
        """Register callback for emergency alerts"""
        self.alert_callbacks.append(callback)
    
    async def check_emergency_conditions(self, sensor_data: Dict) -> Optional[EmergencyEvent]:
        """
        Check sensor data for emergency conditions
        
        Args:
            sensor_data: Current sensor readings
            
        Returns:
            EmergencyEvent if emergency detected, None otherwise
        """
        # Check radiation levels
        radiation = sensor_data.get('radiation_level', 0.0)
        if radiation >= self.thresholds['radiation_critical']:
            return EmergencyEvent(
                level=EmergencyLevel.CRITICAL,
                trigger='radiation_critical',
                description=f"Critical radiation level detected: {radiation} mSv/h",
                timestamp=datetime.now(),
                sensor_data=sensor_data,
                requires_evacuation=True
            )
        elif radiation >= self.thresholds['radiation_high']:
            return EmergencyEvent(
                level=EmergencyLevel.HIGH,
                trigger='radiation_high',
                description=f"High radiation level detected: {radiation} mSv/h",
                timestamp=datetime.now(),
                sensor_data=sensor_data,
                requires_evacuation=False
            )
        
        # Check temperature
        temperature = sensor_data.get('temperature', 20.0)
        if temperature >= self.thresholds['temperature_critical']:
            return EmergencyEvent(
                level=EmergencyLevel.HIGH,
                trigger='temperature_critical',
                description=f"Critical temperature detected: {temperature} degrees C",
                timestamp=datetime.now(),
                sensor_data=sensor_data
            )
        
        # Check gas levels
        gas_levels = sensor_data.get('gas_levels', {})
        for gas, level in gas_levels.items():
            if gas in self.thresholds['gas_critical']:
                if level >= self.thresholds['gas_critical'][gas]:
                    return EmergencyEvent(
                        level=EmergencyLevel.CRITICAL,
                        trigger=f'{gas}_critical',
                        description=f"Critical {gas} level detected: {level} ppm",
                        timestamp=datetime.now(),
                        sensor_data=sensor_data,
                        requires_evacuation=True
                    )
        
        # Check proximity (if available)
        proximity = sensor_data.get('proximity_distance', float('inf'))
        if proximity <= self.thresholds['proximity_emergency']:
            return EmergencyEvent(
                level=EmergencyLevel.MEDIUM,
                trigger='proximity_emergency',
                description=f"Emergency proximity detected: {proximity}m",
                timestamp=datetime.now(),
                sensor_data=sensor_data
            )
        
        return None
    
    async def trigger_emergency_stop(self, emergency_event: EmergencyEvent):
        """
        Trigger emergency stop procedures
        
        Args:
            emergency_event: The emergency event triggering the stop
        """
        if self.is_emergency_active and self.current_emergency:
            # Check if new emergency is more severe
            if emergency_event.level.value <= self.current_emergency.level.value:
                logger.warning(f"Emergency already active with level {self.current_emergency.level.name}")
                return
        
        self.is_emergency_active = True
        self.current_emergency = emergency_event
        self.emergency_history.append(emergency_event)
        
        logger.critical(f"EMERGENCY STOP TRIGGERED: {emergency_event.description}")
        
        # Execute emergency procedures based on level
        if emergency_event.level == EmergencyLevel.CRITICAL:
            await self._execute_critical_stop(emergency_event)
        elif emergency_event.level == EmergencyLevel.HIGH:
            await self._execute_high_priority_stop(emergency_event)
        elif emergency_event.level == EmergencyLevel.MEDIUM:
            await self._execute_medium_priority_stop(emergency_event)
        else:
            await self._execute_controlled_stop(emergency_event)
    
    async def _execute_critical_stop(self, event: EmergencyEvent):
        """Execute critical emergency stop - full system shutdown"""
        logger.critical("EXECUTING CRITICAL EMERGENCY STOP")
        
        # 1. Immediate robot stop
        await self._execute_immediate_stop()
        
        # 2. Trigger evacuation alarms
        await self._trigger_evacuation_alarm()
        
        # 3. Notify emergency services
        await self._notify_emergency_services(event)
        
        # 4. Activate containment protocols
        await self._activate_containment()
        
        # 5. Send alerts to all personnel
        await self._send_critical_alerts(event)
    
    async def _execute_high_priority_stop(self, event: EmergencyEvent):
        """Execute high priority emergency stop"""
        logger.error("EXECUTING HIGH PRIORITY EMERGENCY STOP")
        
        await self._execute_immediate_stop()
        await self._send_emergency_alerts(event)
        await self._initiate_safety_protocols()
    
    async def _execute_medium_priority_stop(self, event: EmergencyEvent):
        """Execute medium priority emergency stop"""
        logger.warning("EXECUTING MEDIUM PRIORITY EMERGENCY STOP")
        
        await self._execute_controlled_stop_sequence()
        await self._send_warning_alerts(event)
    
    async def _execute_controlled_stop(self, event: EmergencyEvent):
        """Execute controlled emergency stop"""
        logger.info("EXECUTING CONTROLLED EMERGENCY STOP")
        
        await self._execute_gradual_stop()
        await self._send_info_alerts(event)
    
    async def _execute_immediate_stop(self):
        """Execute immediate robot stop"""
        for callback in self.stop_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback('immediate')
                else:
                    callback('immediate')
            except Exception as e:
                logger.error(f"Error in stop callback: {e}")
    
    async def _execute_controlled_stop_sequence(self):
        """Execute controlled stop sequence"""
        for callback in self.stop_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback('controlled')
                else:
                    callback('controlled')
            except Exception as e:
                logger.error(f"Error in stop callback: {e}")
    
    async def _execute_gradual_stop(self):
        """Execute gradual stop"""
        for callback in self.stop_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback('gradual')
                else:
                    callback('gradual')
            except Exception as e:
                logger.error(f"Error in stop callback: {e}")
    
    async def _trigger_evacuation_alarm(self):
        """Trigger facility-wide evacuation alarm"""
        logger.critical("EVACUATION ALARM TRIGGERED")
        # In production: interface with facility alarm systems
    
    async def _notify_emergency_services(self, event: EmergencyEvent):
        """Notify emergency services"""
        logger.critical(f"NOTIFYING EMERGENCY SERVICES: {event.description}")
        # In production: automated emergency service notification
    
    async def _activate_containment(self):
        """Activate containment protocols"""
        logger.critical("ACTIVATING CONTAINMENT PROTOCOLS")
        # In production: interface with facility containment systems
    
    async def _initiate_safety_protocols(self):
        """Initiate enhanced safety protocols"""
        logger.warning("INITIATING ENHANCED SAFETY PROTOCOLS")
        # In production: interface with facility safety systems
    
    async def _send_critical_alerts(self, event: EmergencyEvent):
        """Send critical alerts to all personnel"""
        await self._send_alerts(event, "CRITICAL")
    
    async def _send_emergency_alerts(self, event: EmergencyEvent):
        """Send emergency alerts"""
        await self._send_alerts(event, "EMERGENCY")
    
    async def _send_warning_alerts(self, event: EmergencyEvent):
        """Send warning alerts"""
        await self._send_alerts(event, "WARNING")
    
    async def _send_info_alerts(self, event: EmergencyEvent):
        """Send informational alerts"""
        await self._send_alerts(event, "INFO")
    
    async def _send_alerts(self, event: EmergencyEvent, severity: str):
        """Send alerts through registered callbacks"""
        alert_message = {
            'severity': severity,
            'event': event,
            'timestamp': datetime.now(),
            'message': f"{severity}: {event.description}"
        }
        
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert_message)
                else:
                    callback(alert_message)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    async def reset_emergency(self, operator_id: str, reason: str):
        """
        Reset emergency state (requires operator authorization)
        
        Args:
            operator_id: ID of operator resetting emergency
            reason: Reason for reset
        """
        if not self.is_emergency_active:
            logger.warning("No emergency active to reset")
            return
        
        logger.info(f"Emergency reset by operator {operator_id}: {reason}")
        
        self.is_emergency_active = False
        previous_emergency = self.current_emergency
        self.current_emergency = None
        
        # Log reset event
        reset_event = {
            'timestamp': datetime.now(),
            'operator_id': operator_id,
            'reason': reason,
            'previous_emergency': previous_emergency
        }
        
        # Notify all systems of reset
        await self._send_alerts(
            EmergencyEvent(
                level=EmergencyLevel.LOW,
                trigger='manual_reset',
                description=f"Emergency reset by {operator_id}: {reason}",
                timestamp=datetime.now(),
                sensor_data={}
            ),
            "INFO"
        )
    
    def get_emergency_status(self) -> Dict:
        """Get current emergency system status"""
        return {
            'is_active': self.is_emergency_active,
            'current_emergency': self.current_emergency,
            'emergency_count': len(self.emergency_history),
            'last_emergency': self.emergency_history[-1] if self.emergency_history else None,
            'thresholds': self.thresholds
        }