"""
SafetyVision Monitoring Dashboard
Real-time safety monitoring interface using Streamlit
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import asyncio
import cv2
from PIL import Image
import time

# Import our safety engine
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.vlm_safety_engine import VLMSafetyEngine, SensorReading, RiskLevel


class SafetyDashboard:
    """Real-time safety monitoring dashboard"""
    
    def __init__(self):
        self.safety_engine = VLMSafetyEngine()
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        if 'safety_reports' not in st.session_state:
            st.session_state.safety_reports = []
        if 'current_risk_level' not in st.session_state:
            st.session_state.current_risk_level = RiskLevel.MINIMAL
        if 'emergency_active' not in st.session_state:
            st.session_state.emergency_active = False
        if 'robot_status' not in st.session_state:
            st.session_state.robot_status = "Operational"
    
    def run_dashboard(self):
        """Main dashboard interface"""
        st.set_page_config(
            page_title="SafetyVision Nuclear Monitoring",
            page_icon="🔬",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for emergency styling
        st.markdown("""
        <style>
        .emergency-alert {
            background-color: #ff4444;
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .warning-alert {
            background-color: #ffaa00;
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-size: 18px;
            margin-bottom: 15px;
        }
        .safe-alert {
            background-color: #00aa44;
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-size: 18px;
            margin-bottom: 15px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.title("🔬 SafetyVision: Nuclear Facility Monitoring")
        st.markdown("**Real-time VLM-powered safety analysis for nuclear environments**")
        
        # Emergency alert banner
        if st.session_state.emergency_active:
            st.markdown("""
            <div class="emergency-alert">
                🚨 EMERGENCY PROTOCOLS ACTIVE 🚨<br>
                Immediate evacuation required
            </div>
            """, unsafe_allow_html=True)
        
        # Sidebar controls
        self.render_sidebar()
        
        # Main dashboard layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.render_main_monitoring()
        
        with col2:
            self.render_status_panel()
        
        # Bottom section
        self.render_detailed_analysis()
    
    def render_sidebar(self):
        """Render sidebar controls"""
        st.sidebar.header("🎛️ System Controls")
        
        # Robot status
        st.sidebar.subheader("Robot Status")
        robot_status = st.sidebar.selectbox(
            "Current Status",
            ["Operational", "Maintenance", "Emergency Stop", "Offline"]
        )
        st.session_state.robot_status = robot_status
        
        # Manual safety analysis
        st.sidebar.subheader("Manual Analysis")
        if st.sidebar.button("🔍 Run Safety Analysis", type="primary"):
            self.run_safety_analysis()
        
        # Emergency controls
        st.sidebar.subheader("Emergency Controls")
        if st.sidebar.button("🚨 Emergency Stop", type="secondary"):
            st.session_state.emergency_active = True
            st.sidebar.success("Emergency stop activated!")
        
        if st.sidebar.button("✅ Reset Emergency"):
            st.session_state.emergency_active = False
            st.sidebar.success("Emergency reset!")
        
        # Settings
        st.sidebar.subheader("⚙️ Settings")
        
        # VLM model selection
        vlm_model = st.sidebar.selectbox(
            "VLM Model",
            ["GPT-4 Vision", "BLIP-2", "LLaVA", "Flamingo"]
        )
        
        # Safety threshold adjustment
        radiation_threshold = st.sidebar.slider(
            "Radiation Warning (mSv/h)",
            0.1, 2.0, 0.5, 0.1
        )
        
        temp_threshold = st.sidebar.slider(
            "Temperature Warning (°C)",
            50, 100, 70, 5
        )
        
        # Analysis frequency
        analysis_frequency = st.sidebar.selectbox(
            "Analysis Frequency",
            ["Continuous", "Every 30s", "Every 1min", "Manual Only"]
        )
    
    def render_main_monitoring(self):
        """Render main monitoring interface"""
        st.subheader("🎥 Live Environment Feed")
        
        # Simulated camera feed
        camera_tab, thermal_tab, radiation_tab = st.tabs(["📹 Visual Camera", "🌡️ Thermal", "☢️ Radiation Map"])
        
        with camera_tab:
            # Generate simulated camera feed
            demo_image = self.generate_demo_image()
            st.image(demo_image, caption="Nuclear Facility Camera Feed", use_column_width=True)
            
            # VLM analysis overlay
            if st.button("🤖 Analyze with VLM"):
                with st.spinner("VLM analyzing environment..."):
                    analysis = self.simulate_vlm_analysis()
                    st.success("✅ Analysis Complete")
                    st.info(f"**VLM Assessment:** {analysis}")
        
        with thermal_tab:
            # Thermal heatmap
            thermal_data = np.random.normal(45, 10, (20, 30))
            fig_thermal = px.imshow(
                thermal_data,
                color_continuous_scale="Viridis",
                title="Thermal Distribution (°C)",
                labels={"color": "Temperature (°C)"}
            )
            st.plotly_chart(fig_thermal, use_container_width=True)
        
        with radiation_tab:
            # Radiation level map
            radiation_data = np.random.exponential(0.3, (20, 30))
            fig_radiation = px.imshow(
                radiation_data,
                color_continuous_scale="Reds",
                title="Radiation Levels (mSv/h)",
                labels={"color": "Radiation (mSv/h)"}
            )
            st.plotly_chart(fig_radiation, use_container_width=True)
        
        # Real-time sensor data
        st.subheader("📊 Real-time Sensor Data")
        self.render_sensor_charts()
    
    def render_status_panel(self):
        """Render status and alerts panel"""
        st.subheader("🚦 System Status")
        
        # Current risk level indicator
        risk_level = st.session_state.current_risk_level
        risk_colors = {
            RiskLevel.MINIMAL: "🟢",
            RiskLevel.LOW: "🟡",
            RiskLevel.MODERATE: "🟠",
            RiskLevel.HIGH: "🔴",
            RiskLevel.CRITICAL: "🚨"
        }
        
        st.markdown(f"""
        **Current Risk Level:** {risk_colors[risk_level]} **{risk_level.name}**
        
        **Robot Status:** {st.session_state.robot_status}
        
        **VLM Engine:** ✅ Active
        
        **Last Analysis:** {datetime.now().strftime('%H:%M:%S')}
        """)
        
        # Safety alerts
        st.subheader("⚠️ Active Alerts")
        
        # Generate demo alerts based on current status
        alerts = self.generate_demo_alerts()
        
        if alerts:
            for alert in alerts:
                if "CRITICAL" in alert:
                    st.error(f"🚨 {alert}")
                elif "WARNING" in alert:
                    st.warning(f"⚠️ {alert}")
                else:
                    st.info(f"ℹ️ {alert}")
        else:
            st.success("✅ No active alerts")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("📍 Get Robot Position"):
            st.info("Robot Location: Zone A, Sector 3\nCoordinates: (15.2, 8.7, 1.5)")
        
        if st.button("🗣️ Natural Language Query"):
            self.render_nlp_interface()
        
        if st.button("📋 Generate Safety Report"):
            self.generate_safety_report()
    
    def render_sensor_charts(self):
        """Render real-time sensor data charts"""
        # Generate time series data
        time_range = pd.date_range(
            start=datetime.now() - timedelta(minutes=30),
            end=datetime.now(),
            freq='1min'
        )
        
        # Radiation levels
        radiation_data = np.random.exponential(0.3, len(time_range))
        radiation_df = pd.DataFrame({
            'Time': time_range,
            'Radiation (mSv/h)': radiation_data
        })
        
        fig_radiation = px.line(
            radiation_df, 
            x='Time', 
            y='Radiation (mSv/h)',
            title="Radiation Levels - Last 30 Minutes"
        )
        fig_radiation.add_hline(y=0.5, line_dash="dash", line_color="orange", annotation_text="Warning Level")
        fig_radiation.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Danger Level")
        st.plotly_chart(fig_radiation, use_container_width=True)
        
        # Temperature and other sensors in columns
        col1, col2 = st.columns(2)
        
        with col1:
            # Temperature
            temp_data = np.random.normal(45, 5, len(time_range))
            temp_df = pd.DataFrame({
                'Time': time_range,
                'Temperature (°C)': temp_data
            })
            
            fig_temp = px.line(
                temp_df,
                x='Time',
                y='Temperature (°C)',
                title="Temperature Monitoring"
            )
            st.plotly_chart(fig_temp, use_container_width=True)
        
        with col2:
            # Gas levels
            gas_data = {
                'Hydrogen': np.random.exponential(200, len(time_range)),
                'Methane': np.random.exponential(100, len(time_range)),
                'CO2': np.random.normal(400, 50, len(time_range))
            }
            
            gas_df = pd.DataFrame(gas_data)
            gas_df['Time'] = time_range
            gas_df_melted = gas_df.melt(id_vars=['Time'], var_name='Gas', value_name='Level (ppm)')
            
            fig_gas = px.line(
                gas_df_melted,
                x='Time',
                y='Level (ppm)',
                color='Gas',
                title="Gas Level Monitoring"
            )
            st.plotly_chart(fig_gas, use_container_width=True)
    
    def render_detailed_analysis(self):
        """Render detailed analysis section"""
        st.subheader("🔍 Detailed Safety Analysis")
        
        analysis_tab, history_tab, reports_tab = st.tabs(["Current Analysis", "Historical Data", "Safety Reports"])
        
        with analysis_tab:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**VLM Visual Analysis:**")
                st.text_area(
                    "",
                    value="""Visual inspection reveals:
- Equipment operational status: Normal
- Structural integrity: Good condition
- Safety signage: Visible and compliant
- Personnel protective equipment: Available
- Emergency exits: Clear and accessible

Potential concerns:
- Minor corrosion visible on pipe joint (Section B-3)
- Lighting levels below optimal in southeast corner
- Routine maintenance indicator active on pump station""",
                    height=200,
                    disabled=True
                )
            
            with col2:
                st.markdown("**Safety Recommendations:**")
                recommendations = [
                    "✅ Continue current operations with standard monitoring",
                    "🔧 Schedule maintenance for pipe joint inspection",
                    "💡 Improve lighting in southeast corner",
                    "📋 Complete routine pump maintenance within 48 hours",
                    "👥 Maintain minimum 2-person teams in this zone"
                ]
                
                for rec in recommendations:
                    st.markdown(rec)
        
        with history_tab:
            st.markdown("**Safety Event History**")
            
            # Historical data table
            history_data = {
                'Timestamp': [
                    '2024-01-15 14:30:22',
                    '2024-01-15 13:45:18',
                    '2024-01-15 12:15:33',
                    '2024-01-15 11:22:45'
                ],
                'Event Type': ['Warning', 'Info', 'Warning', 'Info'],
                'Risk Level': ['Moderate', 'Low', 'Moderate', 'Low'],
                'Description': [
                    'Elevated radiation in Zone B',
                    'Routine maintenance completed',
                    'Temperature spike detected',
                    'Robot navigation update'
                ],
                'Action Taken': [
                    'Enhanced monitoring activated',
                    'System update applied',
                    'Cooling system checked',
                    'Path recalibrated'
                ]
            }
            
            history_df = pd.DataFrame(history_data)
            st.dataframe(history_df, use_container_width=True)
            
            # Download historical data
            if st.button("📥 Download Historical Data"):
                csv = history_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"safety_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with reports_tab:
            st.markdown("**Automated Safety Reports**")
            
            if st.button("📊 Generate Comprehensive Report"):
                with st.spinner("Generating comprehensive safety report..."):
                    time.sleep(2)  # Simulate processing
                    
                    report_content = f"""
                    # SafetyVision Comprehensive Report
                    **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    
                    ## Executive Summary
                    Current facility status indicates **{st.session_state.current_risk_level.name}** risk level.
                    All systems operating within acceptable parameters.
                    
                    ## Key Findings
                    - Radiation levels: Within safe limits (avg: 0.3 mSv/h)
                    - Temperature monitoring: Normal operational range
                    - Equipment status: Fully operational
                    - VLM analysis confidence: 94%
                    
                    ## Recommendations
                    1. Continue standard monitoring protocols
                    2. Schedule preventive maintenance as indicated
                    3. Maintain current safety procedures
                    
                    ## Next Review
                    Scheduled for: {(datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')}
                    """
                    
                    st.markdown(report_content)
                    
                    # Download report
                    st.download_button(
                        label="📥 Download Report",
                        data=report_content,
                        file_name=f"safety_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown"
                    )
    
    def render_nlp_interface(self):
        """Render natural language query interface"""
        st.subheader("🗣️ Natural Language Safety Queries")
        
        user_query = st.text_input(
            "Ask about safety conditions:",
            placeholder="e.g., 'Is it safe to perform maintenance in Zone A?'"
        )
        
        if user_query:
            with st.spinner("Processing query with VLM..."):
                time.sleep(1)  # Simulate VLM processing
                
                # Simulate intelligent response based on query
                if "safe" in user_query.lower():
                    response = f"""
                    Based on current environmental analysis:
                    
                    **Safety Assessment:** Currently safe for operations with standard precautions
                    **Risk Level:** {st.session_state.current_risk_level.name}
                    **Radiation:** 0.3 mSv/h (within safe limits)
                    **Temperature:** 45°C (normal operating range)
                    
                    **Recommendations:**
                    - Follow standard safety protocols
                    - Ensure proper PPE is worn
                    - Maintain communication with safety team
                    """
                elif "radiation" in user_query.lower():
                    response = """
                    **Radiation Analysis:**
                    - Current level: 0.3 mSv/h
                    - Status: SAFE (below 0.5 mSv/h warning threshold)
                    - Trend: Stable over last 30 minutes
                    - Highest reading today: 0.4 mSv/h at 10:30 AM
                    """
                else:
                    response = f"""
                    I understand you're asking about: "{user_query}"
                    
                    Based on current facility monitoring:
                    - All systems operating normally
                    - No immediate safety concerns detected
                    - VLM analysis shows standard operational conditions
                    
                    For specific safety questions, please contact the safety officer.
                    """
                
                st.success("Query processed successfully!")
                st.info(response)
    
    def generate_demo_image(self):
        """Generate demo nuclear facility image"""
        # Create a simulated facility image
        img = np.ones((400, 600, 3), dtype=np.uint8) * 50
        
        # Add some facility-like elements
        cv2.rectangle(img, (50, 50), (550, 350), (100, 100, 100), -1)  # Room
        cv2.rectangle(img, (100, 100), (200, 200), (80, 80, 200), -1)  # Equipment
        cv2.rectangle(img, (300, 150), (400, 250), (80, 200, 80), -1)  # Control panel
        cv2.circle(img, (450, 125), 30, (200, 200, 80), -1)  # Warning sign
        
        # Add some text
        cv2.putText(img, "NUCLEAR FACILITY", (150, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(img, "ZONE A - SECTOR 3", (200, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        return img
    
    def simulate_vlm_analysis(self):
        """Simulate VLM analysis of the environment"""
        analyses = [
            "Equipment appears operational with no visible damage or leaks detected.",
            "Safety signage is clearly visible and emergency exits are unobstructed.",
            "Control panels show normal operational indicators with no warning lights.",
            "Work area is clear of debris and properly maintained.",
            "Radiation warning symbols are visible and properly positioned."
        ]
        return np.random.choice(analyses)
    
    def generate_demo_alerts(self):
        """Generate demo alerts based on current system state"""
        alerts = []
        
        if st.session_state.emergency_active:
            alerts.extend([
                "CRITICAL: Emergency protocols active",
                "CRITICAL: Robot movement restricted",
                "WARNING: Personnel evacuation in progress"
            ])
        elif st.session_state.current_risk_level == RiskLevel.HIGH:
            alerts.extend([
                "WARNING: Elevated radiation levels detected",
                "INFO: Enhanced monitoring activated"
            ])
        elif st.session_state.robot_status == "Maintenance":
            alerts.extend([
                "INFO: Robot in maintenance mode",
                "INFO: Scheduled maintenance in progress"
            ])
        
        return alerts
    
    def run_safety_analysis(self):
        """Run manual safety analysis"""
        with st.spinner("Running comprehensive safety analysis..."):
            time.sleep(2)  # Simulate analysis time
            
            # Randomly adjust risk level for demo
            risk_levels = list(RiskLevel)
            st.session_state.current_risk_level = np.random.choice(risk_levels[:3])  # Keep it reasonable
            
            st.success("✅ Safety analysis complete!")
            st.info(f"Updated risk level: {st.session_state.current_risk_level.name}")
    
    def generate_safety_report(self):
        """Generate downloadable safety report"""
        with st.spinner("Generating safety report..."):
            time.sleep(1)
            
            report = f"""
            SAFETYVISION SAFETY REPORT
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            CURRENT STATUS: {st.session_state.current_risk_level.name}
            ROBOT STATUS: {st.session_state.robot_status}
            EMERGENCY ACTIVE: {st.session_state.emergency_active}
            
            SENSOR READINGS:
            - Radiation: 0.3 mSv/h (SAFE)
            - Temperature: 45°C (NORMAL)
            - Humidity: 65% (ACCEPTABLE)
            
            VLM ANALYSIS:
            Environment shows normal operational conditions with no immediate safety concerns.
            All equipment appears functional and safety protocols are being followed.
            
            RECOMMENDATIONS:
            - Continue standard monitoring
            - Maintain current safety procedures
            - Schedule routine maintenance as planned
            """
            
            st.download_button(
                label="📥 Download Safety Report",
                data=report,
                file_name=f"safety_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )


def main():
    """Main function to run the dashboard"""
    dashboard = SafetyDashboard()
    dashboard.run_dashboard()


if __name__ == "__main__":
    main()