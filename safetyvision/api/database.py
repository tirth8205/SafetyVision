"""
Database manager for storing safety data
"""

import asyncio
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import sqlite3
import aiosqlite
from pathlib import Path

from ..core.vlm_safety_engine import SafetyReport, RiskLevel
from .models import SafetyReportResponse, EmergencyAlert

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations for safety data"""
    
    def __init__(self, db_path: str = "data/safetyvision.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._connection = None
    
    async def initialize(self):
        """Initialize database and create tables"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS safety_reports (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME,
                    risk_level TEXT,
                    confidence REAL,
                    status TEXT,
                    explanation TEXT,
                    recommendations TEXT,
                    sensor_data TEXT,
                    visual_analysis TEXT,
                    emergency_required BOOLEAN
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS emergency_alerts (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME,
                    risk_level TEXT,
                    description TEXT,
                    recommendations TEXT,
                    auto_triggered BOOLEAN,
                    acknowledged BOOLEAN,
                    resolved BOOLEAN
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    radiation_level REAL,
                    temperature REAL,
                    humidity REAL,
                    pressure REAL,
                    gas_concentration REAL,
                    vibration_level REAL
                )
            """)
            
            # Create indexes for better query performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_reports_timestamp ON safety_reports(timestamp)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON emergency_alerts(timestamp)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_sensors_timestamp ON sensor_readings(timestamp)")
            
            await db.commit()
        
        logger.info("Database initialized successfully")
    
    async def store_safety_report(self, report: SafetyReport) -> str:
        """Store safety report in database"""
        import uuid
        report_id = str(uuid.uuid4())
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO safety_reports 
                (id, timestamp, risk_level, confidence, status, explanation, 
                 recommendations, sensor_data, visual_analysis, emergency_required)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                report.timestamp,
                report.risk_level.name,
                report.confidence,
                report.status,
                report.explanation,
                json.dumps(report.recommendations),
                json.dumps(report.sensor_data),
                report.visual_analysis,
                report.emergency_required
            ))
            await db.commit()
        
        return report_id
    
    async def get_safety_reports(
        self, 
        limit: int = 100, 
        start_time: Optional[datetime] = None
    ) -> List[SafetyReportResponse]:
        """Retrieve safety reports from database"""
        query = "SELECT * FROM safety_reports"
        params = []
        
        if start_time:
            query += " WHERE timestamp >= ?"
            params.append(start_time)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                
                reports = []
                for row in rows:
                    reports.append(SafetyReportResponse(
                        id=row['id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        risk_level=row['risk_level'],
                        confidence=row['confidence'],
                        status=row['status'],
                        explanation=row['explanation'],
                        recommendations=json.loads(row['recommendations']),
                        sensor_data=json.loads(row['sensor_data']),
                        visual_analysis=row['visual_analysis'],
                        emergency_required=bool(row['emergency_required'])
                    ))
                
                return reports
    
    async def store_emergency_alert(self, alert: EmergencyAlert):
        """Store emergency alert in database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO emergency_alerts 
                (id, timestamp, risk_level, description, recommendations, 
                 auto_triggered, acknowledged, resolved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.id,
                alert.timestamp,
                alert.risk_level.name,
                alert.description,
                json.dumps(alert.recommendations),
                alert.auto_triggered,
                alert.acknowledged,
                alert.resolved
            ))
            await db.commit()
    
    async def get_recent_alerts(self, hours: int = 24) -> List[EmergencyAlert]:
        """Get recent emergency alerts"""
        since = datetime.now() - timedelta(hours=hours)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM emergency_alerts 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
            """, (since,)) as cursor:
                rows = await cursor.fetchall()
                
                alerts = []
                for row in rows:
                    alerts.append(EmergencyAlert(
                        id=row['id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        risk_level=RiskLevel[row['risk_level']],
                        description=row['description'],
                        recommendations=json.loads(row['recommendations']),
                        auto_triggered=bool(row['auto_triggered']),
                        acknowledged=bool(row['acknowledged']),
                        resolved=bool(row['resolved'])
                    ))
                
                return alerts
    
    async def store_sensor_reading(self, sensor_data: Dict[str, float]):
        """Store sensor reading in database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO sensor_readings 
                (timestamp, radiation_level, temperature, humidity, 
                 pressure, gas_concentration, vibration_level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                sensor_data.get('radiation_level', 0),
                sensor_data.get('temperature', 0),
                sensor_data.get('humidity', 0),
                sensor_data.get('pressure', 0),
                sensor_data.get('gas_concentration', 0),
                sensor_data.get('vibration_level', 0)
            ))
            await db.commit()
    
    async def get_sensor_history(
        self, 
        hours: int = 24, 
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get sensor reading history"""
        since = datetime.now() - timedelta(hours=hours)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM sensor_readings 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (since, limit)) as cursor:
                rows = await cursor.fetchall()
                
                return [dict(row) for row in rows]
    
    async def cleanup_old_data(self, days: int = 30):
        """Clean up old data to manage database size"""
        cutoff = datetime.now() - timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Keep emergency alerts longer
            await db.execute("DELETE FROM safety_reports WHERE timestamp < ?", (cutoff,))
            await db.execute("DELETE FROM sensor_readings WHERE timestamp < ?", (cutoff,))
            await db.commit()
        
        logger.info(f"Cleaned up data older than {days} days")
    
    def is_connected(self) -> bool:
        """Check if database is accessible"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False