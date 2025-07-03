"""
Safety visualization components for nuclear facility monitoring
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class VisualizationConfig:
    """Configuration for safety visualizations"""
    figure_size: Tuple[int, int] = (12, 8)
    update_interval: int = 1000  # milliseconds
    color_scheme: str = "viridis"
    show_grid: bool = True
    animation_enabled: bool = True


class RadiationHeatmap:
    """Radiation level heatmap visualization"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.fig, self.ax = plt.subplots(figsize=config.figure_size)
        self.heatmap = None
        self.colorbar = None
        
    def update_data(self, radiation_map: np.ndarray, locations: List[Tuple], levels: List[float]):
        """Update radiation heatmap with new data"""
        self.ax.clear()
        
        # Create heatmap
        im = self.ax.imshow(radiation_map, cmap='Reds', interpolation='bilinear')
        
        # Add sensor locations
        for i, (x, y) in enumerate(locations):
            color = 'blue' if levels[i] < 1.0 else 'red'
            self.ax.scatter(y, x, c=color, s=100, marker='o', 
                          edgecolors='black', linewidth=2)
            self.ax.annotate(f'{levels[i]:.2f}', (y, x), 
                           xytext=(5, 5), textcoords='offset points')
        
        # Update colorbar
        if self.colorbar:
            self.colorbar.remove()
        self.colorbar = self.fig.colorbar(im, ax=self.ax, label='Radiation Level (mSv/h)')
        
        self.ax.set_title('Radiation Level Heatmap')
        self.ax.set_xlabel('Y Position')
        self.ax.set_ylabel('X Position')
        
        if self.config.show_grid:
            self.ax.grid(True, alpha=0.3)


class SafetyZoneVisualizer:
    """Visualize safety zones and restricted areas"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.fig, self.ax = plt.subplots(figsize=config.figure_size)
        self.zones = []
        
    def add_safety_zone(self, zone_type: str, coordinates: List[Tuple], level: str):
        """Add safety zone to visualization"""
        zone_colors = {
            'safe': 'green',
            'caution': 'yellow', 
            'danger': 'orange',
            'critical': 'red',
            'forbidden': 'purple'
        }
        
        color = zone_colors.get(level, 'gray')
        alpha = 0.3
        
        if zone_type == 'circle':
            center, radius = coordinates[0], coordinates[1][0]
            circle = patches.Circle(center, radius, color=color, alpha=alpha)
            self.ax.add_patch(circle)
        elif zone_type == 'rectangle':
            x, y, width, height = coordinates
            rect = patches.Rectangle((x, y), width, height, color=color, alpha=alpha)
            self.ax.add_patch(rect)
        elif zone_type == 'polygon':
            poly = patches.Polygon(coordinates, color=color, alpha=alpha)
            self.ax.add_patch(poly)
        
        self.zones.append({
            'type': zone_type,
            'coordinates': coordinates,
            'level': level,
            'color': color
        })
    
    def update_robot_position(self, position: Tuple[float, float], heading: float):
        """Update robot position on map"""
        # Clear previous robot marker
        for artist in self.ax.collections:
            if hasattr(artist, '_robot_marker'):
                artist.remove()
        
        # Add robot marker
        robot_marker = self.ax.scatter(position[0], position[1], c='blue', s=200, 
                                     marker='^', edgecolors='black', linewidth=2)
        robot_marker._robot_marker = True
        
        # Add heading indicator
        dx = 2 * np.cos(heading)
        dy = 2 * np.sin(heading)
        self.ax.arrow(position[0], position[1], dx, dy, 
                     head_width=0.5, head_length=0.3, fc='blue', ec='blue')
    
    def refresh_display(self):
        """Refresh the safety zone display"""
        self.ax.set_title('Safety Zones and Robot Position')
        self.ax.set_xlabel('X Position (m)')
        self.ax.set_ylabel('Y Position (m)')
        self.ax.set_aspect('equal')
        
        if self.config.show_grid:
            self.ax.grid(True, alpha=0.3)


class SensorStatusDashboard:
    """Dashboard for sensor status monitoring"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.fig, self.axes = plt.subplots(2, 2, figsize=config.figure_size)
        self.fig.suptitle('Sensor Status Dashboard')
        
    def update_sensor_grid(self, sensor_data: Dict[str, Any]):
        """Update sensor status grid"""
        # Clear axes
        for ax in self.axes.flat:
            ax.clear()
        
        # Radiation sensors
        self._plot_radiation_status(self.axes[0, 0], sensor_data.get('radiation', {}))
        
        # Temperature sensors  
        self._plot_temperature_status(self.axes[0, 1], sensor_data.get('temperature', {}))
        
        # Camera sensors
        self._plot_camera_status(self.axes[1, 0], sensor_data.get('cameras', {}))
        
        # System health
        self._plot_system_health(self.axes[1, 1], sensor_data.get('system', {}))
        
        plt.tight_layout()
    
    def _plot_radiation_status(self, ax, data):
        """Plot radiation sensor status"""
        sensors = data.get('sensors', [])
        if not sensors:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
            ax.set_title('Radiation Sensors')
            return
        
        names = [s['id'] for s in sensors]
        levels = [s['dose_rate'] for s in sensors]
        colors = ['red' if l > 1.0 else 'yellow' if l > 0.5 else 'green' for l in levels]
        
        bars = ax.bar(names, levels, color=colors)
        ax.set_ylabel('Dose Rate (mSv/h)')
        ax.set_title('Radiation Sensors')
        ax.tick_params(axis='x', rotation=45)
        
        # Add threshold lines
        ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.7, label='Warning')
        ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='Danger')
        ax.legend()
    
    def _plot_temperature_status(self, ax, data):
        """Plot temperature sensor status"""
        sensors = data.get('sensors', [])
        if not sensors:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
            ax.set_title('Temperature Sensors')
            return
        
        names = [s['id'] for s in sensors]
        temps = [s['temperature'] for s in sensors]
        colors = ['red' if t > 60 else 'yellow' if t > 40 else 'green' for t in temps]
        
        bars = ax.bar(names, temps, color=colors)
        ax.set_ylabel('Temperature (°C)')
        ax.set_title('Temperature Sensors')
        ax.tick_params(axis='x', rotation=45)
    
    def _plot_camera_status(self, ax, data):
        """Plot camera sensor status"""
        cameras = data.get('cameras', [])
        if not cameras:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
            ax.set_title('Camera Status')
            return
        
        names = [c['id'] for c in cameras]
        status = [c['status'] for c in cameras]
        
        # Create status visualization
        status_colors = {'online': 'green', 'offline': 'red', 'error': 'orange'}
        colors = [status_colors.get(s, 'gray') for s in status]
        
        y_pos = np.arange(len(names))
        bars = ax.barh(y_pos, [1]*len(names), color=colors)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names)
        ax.set_xlabel('Status')
        ax.set_title('Camera Status')
        ax.set_xlim(0, 1)
    
    def _plot_system_health(self, ax, data):
        """Plot overall system health metrics"""
        if not data:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
            ax.set_title('System Health')
            return
        
        metrics = ['CPU', 'Memory', 'Disk', 'Network']
        values = [
            data.get('cpu_usage', 0),
            data.get('memory_usage', 0), 
            data.get('disk_usage', 0),
            data.get('network_status', 0)
        ]
        
        colors = ['red' if v > 80 else 'yellow' if v > 60 else 'green' for v in values]
        
        bars = ax.bar(metrics, values, color=colors)
        ax.set_ylabel('Usage (%)')
        ax.set_title('System Health')
        ax.set_ylim(0, 100)


class AlertTimeline:
    """Timeline visualization for alerts and events"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.fig, self.ax = plt.subplots(figsize=config.figure_size)
        self.events = []
        
    def add_event(self, timestamp: datetime, event_type: str, description: str, severity: str):
        """Add event to timeline"""
        self.events.append({
            'timestamp': timestamp,
            'type': event_type,
            'description': description,
            'severity': severity
        })
        
        # Keep only recent events
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.events = [e for e in self.events if e['timestamp'] > cutoff_time]
    
    def update_timeline(self):
        """Update the timeline visualization"""
        self.ax.clear()
        
        if not self.events:
            self.ax.text(0.5, 0.5, 'No Events', ha='center', va='center')
            self.ax.set_title('Event Timeline (24h)')
            return
        
        # Sort events by timestamp
        sorted_events = sorted(self.events, key=lambda x: x['timestamp'])
        
        # Color mapping for severity
        severity_colors = {
            'info': 'blue',
            'warning': 'orange', 
            'error': 'red',
            'critical': 'darkred'
        }
        
        timestamps = [e['timestamp'] for e in sorted_events]
        severities = [e['severity'] for e in sorted_events]
        colors = [severity_colors.get(s, 'gray') for s in severities]
        
        # Plot timeline
        y_positions = range(len(sorted_events))
        scatter = self.ax.scatter(timestamps, y_positions, c=colors, s=100, alpha=0.7)
        
        # Add event descriptions
        for i, event in enumerate(sorted_events):
            self.ax.annotate(f"{event['type']}: {event['description'][:30]}...", 
                           (timestamps[i], i),
                           xytext=(10, 0), textcoords='offset points',
                           fontsize=8, alpha=0.8)
        
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Events')
        self.ax.set_title('Event Timeline (24h)')
        
        # Rotate x-axis labels
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)


class SafetyMetricsTrends:
    """Trend visualization for safety metrics"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.fig, self.axes = plt.subplots(2, 2, figsize=config.figure_size)
        self.fig.suptitle('Safety Metrics Trends')
        self.data_history = {
            'radiation': [],
            'temperature': [],
            'alerts': [],
            'system_health': []
        }
    
    def add_data_point(self, metric_type: str, timestamp: datetime, value: float):
        """Add data point to trend history"""
        self.data_history[metric_type].append({
            'timestamp': timestamp,
            'value': value
        })
        
        # Keep only recent data (24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.data_history[metric_type] = [
            d for d in self.data_history[metric_type] 
            if d['timestamp'] > cutoff_time
        ]
    
    def update_trends(self):
        """Update all trend visualizations"""
        # Clear axes
        for ax in self.axes.flat:
            ax.clear()
        
        # Plot radiation trend
        self._plot_metric_trend(self.axes[0, 0], 'radiation', 'Radiation Level (mSv/h)', 'red')
        
        # Plot temperature trend
        self._plot_metric_trend(self.axes[0, 1], 'temperature', 'Temperature (°C)', 'orange')
        
        # Plot alert frequency
        self._plot_alert_frequency(self.axes[1, 0])
        
        # Plot system health trend
        self._plot_metric_trend(self.axes[1, 1], 'system_health', 'System Health (%)', 'green')
        
        plt.tight_layout()
    
    def _plot_metric_trend(self, ax, metric_type: str, ylabel: str, color: str):
        """Plot trend for specific metric"""
        data = self.data_history[metric_type]
        
        if not data:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
            ax.set_title(f'{metric_type.title()} Trend')
            return
        
        timestamps = [d['timestamp'] for d in data]
        values = [d['value'] for d in data]
        
        ax.plot(timestamps, values, color=color, linewidth=2, marker='o', markersize=4)
        ax.set_ylabel(ylabel)
        ax.set_title(f'{metric_type.title()} Trend (24h)')
        
        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        if self.config.show_grid:
            ax.grid(True, alpha=0.3)
    
    def _plot_alert_frequency(self, ax):
        """Plot alert frequency over time"""
        alert_data = self.data_history['alerts']
        
        if not alert_data:
            ax.text(0.5, 0.5, 'No Alerts', ha='center', va='center')
            ax.set_title('Alert Frequency')
            return
        
        # Group alerts by hour
        hourly_counts = {}
        for alert in alert_data:
            hour = alert['timestamp'].replace(minute=0, second=0, microsecond=0)
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        
        if hourly_counts:
            hours = sorted(hourly_counts.keys())
            counts = [hourly_counts[h] for h in hours]
            
            ax.bar(hours, counts, color='red', alpha=0.7)
            ax.set_ylabel('Alert Count')
            ax.set_title('Alert Frequency (per hour)')
            
            # Rotate x-axis labels
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)


class SafetyVisualizationManager:
    """Main manager for all safety visualizations"""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        
        # Initialize visualization components
        self.radiation_heatmap = RadiationHeatmap(self.config)
        self.safety_zones = SafetyZoneVisualizer(self.config)
        self.sensor_dashboard = SensorStatusDashboard(self.config)
        self.alert_timeline = AlertTimeline(self.config)
        self.metrics_trends = SafetyMetricsTrends(self.config)
        
        # Animation support
        self.animations = {}
        self.update_callbacks = []
        
        logger.info("Safety visualization manager initialized")
    
    def update_all_visualizations(self, data: Dict[str, Any]):
        """Update all visualizations with new data"""
        try:
            # Update radiation heatmap
            if 'radiation_map' in data:
                self.radiation_heatmap.update_data(
                    data['radiation_map']['grid'],
                    data['radiation_map']['sensor_locations'],
                    data['radiation_map']['sensor_levels']
                )
            
            # Update safety zones
            if 'robot_position' in data:
                self.safety_zones.update_robot_position(
                    data['robot_position']['location'],
                    data['robot_position']['heading']
                )
            
            # Update sensor dashboard
            if 'sensor_status' in data:
                self.sensor_dashboard.update_sensor_grid(data['sensor_status'])
            
            # Update alert timeline
            if 'new_alerts' in data:
                for alert in data['new_alerts']:
                    self.alert_timeline.add_event(
                        alert['timestamp'],
                        alert['type'],
                        alert['description'],
                        alert['severity']
                    )
                self.alert_timeline.update_timeline()
            
            # Update trends
            if 'metrics' in data:
                for metric_type, metric_data in data['metrics'].items():
                    self.metrics_trends.add_data_point(
                        metric_type,
                        metric_data['timestamp'],
                        metric_data['value']
                    )
                self.metrics_trends.update_trends()
            
            # Trigger callbacks
            for callback in self.update_callbacks:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in visualization callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error updating visualizations: {e}")
    
    def register_update_callback(self, callback: callable):
        """Register callback for visualization updates"""
        self.update_callbacks.append(callback)
    
    def save_visualizations(self, output_dir: str):
        """Save all current visualizations to files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            self.radiation_heatmap.fig.savefig(f"{output_dir}/radiation_heatmap.png")
            self.safety_zones.fig.savefig(f"{output_dir}/safety_zones.png")
            self.sensor_dashboard.fig.savefig(f"{output_dir}/sensor_dashboard.png")
            self.alert_timeline.fig.savefig(f"{output_dir}/alert_timeline.png")
            self.metrics_trends.fig.savefig(f"{output_dir}/metrics_trends.png")
            
            logger.info(f"Visualizations saved to {output_dir}")
            
        except Exception as e:
            logger.error(f"Error saving visualizations: {e}")
    
    def show_all(self):
        """Display all visualizations"""
        plt.show()
    
    def close_all(self):
        """Close all visualization windows"""
        plt.close('all')