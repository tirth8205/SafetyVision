# SafetyVision: VLM-Integrated Robotics for Nuclear Environments

A safety-critical robotic system that integrates Vision Language Models with autonomous navigation for nuclear power plant inspection and maintenance tasks.

## 🚀 Features

- **VLM-Powered Safety Analysis**: Real-time hazard detection and risk assessment using Vision Language Models
- **Multimodal Sensor Fusion**: Integration of visual, thermal, and radiation sensor data
- **Natural Language Safety Protocols**: Human-readable safety communications and decision explanations
- **Autonomous Navigation**: ROS2-based navigation with safety-first pathfinding
- **Fail-Safe Mechanisms**: Multiple redundancy layers for critical safety decisions
- **Real-time Monitoring**: Live dashboard for remote operation and safety monitoring

## 🏗️ Architecture

```
SafetyVision/
├── safetyvision/
│   ├── core/
│   │   ├── vlm_safety_engine.py      # Main VLM integration
│   │   ├── sensor_fusion.py          # Multimodal data processing
│   │   ├── safety_protocols.py       # Safety rule engine
│   │   └── decision_engine.py        # AI decision making
│   ├── navigation/
│   │   ├── path_planner.py          # Safety-aware path planning
│   │   ├── obstacle_detection.py    # Enhanced obstacle detection
│   │   └── emergency_stop.py        # Emergency protocols
│   ├── sensors/
│   │   ├── radiation_monitor.py     # Radiation sensor interface
│   │   ├── thermal_camera.py        # Thermal imaging
│   │   └── visual_perception.py     # Computer vision
│   ├── communication/
│   │   ├── nlp_interface.py         # Natural language interface
│   │   ├── alert_system.py          # Safety alert management
│   │   └── human_interface.py       # Human operator interface
│   └── dashboard/
│       ├── monitoring_app.py        # Streamlit dashboard
│       └── safety_visualizer.py     # Safety data visualization
├── ros2_workspace/
│   └── src/
│       └── safetyvision_ros/
├── config/
│   ├── safety_thresholds.yaml
│   ├── robot_config.yaml
│   └── vlm_config.yaml
├── tests/
├── docs/
├── requirements.txt
├── setup.py
├── docker-compose.yml
└── README.md
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- ROS2 Humble (for robot integration)
- CUDA-capable GPU (recommended)
- Docker (optional)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/tirth8205/SafetyVision.git
cd SafetyVision

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install ROS2 dependencies (if using robot hardware)
cd ros2_workspace
colcon build
source install/setup.bash
```

### Docker Installation

```bash
# Build and run with Docker
docker-compose up --build

# Or run individual services
docker run -p 8501:8501 safetyvision:dashboard
```

## 🚀 Usage

### Safety Monitoring Dashboard

```bash
# Launch the main monitoring dashboard
streamlit run safetyvision/dashboard/monitoring_app.py
```

### VLM Safety Analysis

```python
from safetyvision.core.vlm_safety_engine import VLMSafetyEngine

# Initialize the safety engine
safety_engine = VLMSafetyEngine()

# Analyze current environment
safety_report = safety_engine.analyze_environment(
    visual_data=camera_feed,
    sensor_data=radiation_readings,
    query="Is it safe to proceed with maintenance task?"
)

print(f"Safety Status: {safety_report.status}")
print(f"Risk Level: {safety_report.risk_level}")
print(f"Explanation: {safety_report.explanation}")
```

### Robot Navigation

```bash
# Launch ROS2 navigation stack
ros2 launch safetyvision_ros safety_navigation.launch.py

# Send navigation goal with safety constraints
ros2 service call /navigate_safely safetyvision_interfaces/NavigateSafely "{
  target_x: 10.0,
  target_y: 5.0,
  max_radiation: 0.5,
  required_clearance: 2.0
}"
```

### Natural Language Commands

```python
from safetyvision.communication.nlp_interface import NLPInterface

nlp = NLPInterface()

# Give natural language instructions
response = nlp.process_command(
    "Check radiation levels in zone A and report if maintenance is safe"
)

# Get safety explanation
explanation = nlp.explain_decision(
    "Why did you recommend stopping the current task?"
)
```

## 🔧 Configuration

### Safety Thresholds (`config/safety_thresholds.yaml`)

```yaml
radiation:
  safe_level: 0.1      # mSv/h
  warning_level: 0.5   # mSv/h
  danger_level: 1.0    # mSv/h

temperature:
  max_operating: 60    # Celsius
  critical: 80         # Celsius

proximity:
  minimum_clearance: 1.5  # meters
  emergency_stop: 0.5     # meters
```

### VLM Configuration (`config/vlm_config.yaml`)

```yaml
model:
  name: "gpt-4-vision-preview"
  temperature: 0.1
  max_tokens: 1000

safety_prompts:
  hazard_detection: |
    Analyze this nuclear facility image for potential safety hazards.
    Consider radiation sources, structural integrity, and personnel safety.
    Provide a detailed risk assessment with specific recommendations.

  emergency_assessment: |
    This is an emergency situation in a nuclear facility.
    Assess immediate risks and provide clear, actionable safety instructions.
```

## 📊 Safety Features

### Redundant Safety Systems

1. **VLM Primary Analysis**: Advanced reasoning about complex scenarios
2. **Rule-Based Backup**: Traditional safety rules as fallback
3. **Human Override**: Always available emergency stop
4. **Sensor Validation**: Cross-checking between multiple sensors

### Risk Assessment Framework

```python
class SafetyRisk:
    MINIMAL = 1    # Safe to proceed
    LOW = 2        # Proceed with caution
    MODERATE = 3   # Additional safety measures required
    HIGH = 4       # Recommend stopping task
    CRITICAL = 5   # Immediate evacuation
```

### Emergency Protocols

- **Automatic Emergency Stop**: Triggered by sensor thresholds
- **Radiation Exposure Limits**: Strict monitoring and alerts
- **Path Deviation Alerts**: Notification when robot leaves safe zones
- **Communication Failsafe**: Automatic safe mode if connection lost

## 🧪 Testing

```bash
# Run safety system tests
python -m pytest tests/test_safety_engine.py

# Run integration tests
python -m pytest tests/test_integration.py

# Run simulation tests
python tests/run_simulation_tests.py
```

### Safety Validation

```bash
# Validate safety thresholds
python scripts/validate_safety_config.py

# Test emergency scenarios
python scripts/test_emergency_scenarios.py
```

## 📚 Documentation

- [Safety Architecture](docs/safety_architecture.md)
- [VLM Integration Guide](docs/vlm_integration.md)
- [API Reference](docs/api_reference.md)
- [Deployment Guide](docs/deployment.md)
- [Safety Protocols](docs/safety_protocols.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-safety-feature`)
3. Commit your changes (`git commit -m 'Add amazing safety feature'`)
4. Push to the branch (`git push origin feature/amazing-safety-feature`)
5. Open a Pull Request

### Safety Guidelines for Contributors

- All safety-critical code must include comprehensive tests
- Changes to safety thresholds require peer review
- Emergency protocols cannot be modified without safety team approval

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Safety Disclaimer

**FOR RESEARCH AND DEVELOPMENT PURPOSES ONLY**

This system is designed for research and development in controlled environments. It is not certified for use in actual nuclear facilities without proper safety validation, regulatory approval, and extensive testing. All deployment in real nuclear environments must comply with relevant safety standards and regulations.

## 🙏 Acknowledgments

- **CAMEL AI**: For supporting multimodal AI research
- **Nuclear Safety Community**: For providing domain expertise
- **ROS2 Community**: For robotics framework and tools
- **OpenAI**: For Vision Language Model capabilities

## 📞 Contact

**Tirth Kanani**  
CAMEL Ambassador  
Email: tirthkanani18@gmail.com  
LinkedIn: [tirthkanani](https://linkedin.com/in/tirthkanani)  
Portfolio: [tirthkanani.com](https://tirthkanani.com)

---

**🔒 Remember: Safety is not just a feature, it's our foundation.**