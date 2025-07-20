// SafetyVision Dashboard JavaScript
class SafetyDashboard {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.chartData = {
            labels: [],
            confidence: [],
            riskScore: []
        };
        this.chart = null;
        
        this.init();
    }

    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.setupChart();
        this.startCameraFeed();
        this.generateMockData();
    }

    setupWebSocket() {
        try {
            this.socket = io('ws://localhost:8000');
            
            this.socket.on('connect', () => {
                this.isConnected = true;
                this.updateConnectionStatus();
                console.log('Connected to SafetyVision backend');
            });

            this.socket.on('disconnect', () => {
                this.isConnected = false;
                this.updateConnectionStatus();
                console.log('Disconnected from SafetyVision backend');
            });

            this.socket.on('safety_update', (data) => {
                this.updateSafetyData(data);
            });

            this.socket.on('emergency_alert', (data) => {
                this.showEmergencyAlert(data);
            });

            this.socket.on('emergency_cleared', () => {
                this.hideEmergencyAlert();
            });

        } catch (error) {
            console.log('WebSocket connection failed, using mock data');
            this.generateMockData();
        }
    }

    updateConnectionStatus() {
        const statusEl = document.getElementById('connectionStatus');
        if (this.isConnected) {
            statusEl.innerHTML = '<i class="fas fa-wifi"></i> CONNECTED';
            statusEl.className = 'px-3 py-1 rounded text-sm bg-green-600';
        } else {
            statusEl.innerHTML = '<i class="fas fa-wifi-slash"></i> DISCONNECTED';
            statusEl.className = 'px-3 py-1 rounded text-sm bg-red-600';
        }
    }

    updateSafetyData(data) {
        // Update risk level
        const riskLevel = data.risk_level || 'MINIMAL';
        document.getElementById('riskLevel').textContent = riskLevel;
        
        const riskIcon = document.getElementById('riskIcon');
        const riskCard = riskIcon.closest('.card');
        
        // Update styling based on risk level
        riskCard.classList.remove('safe', 'warning', 'danger', 'glow', 'danger-glow');
        
        switch (riskLevel.toLowerCase()) {
            case 'minimal':
            case 'low':
                riskCard.classList.add('safe', 'glow');
                riskIcon.className = 'fas fa-shield-alt text-4xl text-green-400';
                break;
            case 'moderate':
                riskCard.classList.add('warning');
                riskIcon.className = 'fas fa-exclamation-triangle text-4xl text-yellow-400';
                break;
            case 'high':
            case 'critical':
                riskCard.classList.add('danger', 'danger-glow');
                riskIcon.className = 'fas fa-radiation text-4xl text-red-400';
                break;
        }

        // Update confidence
        const confidence = Math.round((data.confidence || 0.85) * 100);
        document.getElementById('confidence').textContent = `${confidence}%`;

        // Update sensor data
        if (data.sensor_data) {
            this.updateSensorReadings(data.sensor_data);
        }

        // Update last update time
        document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();

        // Update chart
        this.updateChart(confidence, this.calculateRiskScore(riskLevel));
    }

    updateSensorReadings(sensorData) {
        // Radiation
        const radiation = (sensorData.radiation_level || 0.1).toFixed(3);
        document.getElementById('radiationLevel').textContent = `${radiation} mSv/h`;
        this.updateSensorStatus('radiation', radiation, { safe: 0.1, warning: 0.5, danger: 1.0 });

        // Temperature
        const temp = (sensorData.temperature || 25).toFixed(1);
        document.getElementById('temperature').textContent = `${temp}°C`;
        this.updateSensorStatus('temp', temp, { safe: 30, warning: 50, danger: 70 });

        // Humidity
        const humidity = Math.round(sensorData.humidity || 60);
        document.getElementById('humidity').textContent = `${humidity}%`;
        this.updateSensorStatus('humidity', humidity, { safe: 70, warning: 85, danger: 95 });

        // Pressure
        const pressure = Math.round(sensorData.pressure || 1013);
        document.getElementById('pressure').textContent = `${pressure} hPa`;
        this.updateSensorStatus('pressure', pressure, { safe: 1020, warning: 1050, danger: 1080 });
    }

    updateSensorStatus(sensor, value, thresholds) {
        const statusEl = document.getElementById(`${sensor}Status`);
        const barEl = document.getElementById(`${sensor}Bar`);
        
        let status, color, barColor, percentage;
        
        if (value <= thresholds.safe) {
            status = 'SAFE';
            color = 'bg-green-600';
            barColor = 'bg-green-400';
            percentage = (value / thresholds.safe) * 30;
        } else if (value <= thresholds.warning) {
            status = 'WARNING';
            color = 'bg-yellow-600';
            barColor = 'bg-yellow-400';
            percentage = 30 + ((value - thresholds.safe) / (thresholds.warning - thresholds.safe)) * 40;
        } else {
            status = 'DANGER';
            color = 'bg-red-600';
            barColor = 'bg-red-400';
            percentage = 70 + Math.min(((value - thresholds.warning) / (thresholds.danger - thresholds.warning)) * 30, 30);
        }
        
        statusEl.textContent = status;
        statusEl.className = `px-2 py-1 rounded text-xs ${color}`;
        barEl.className = `h-2 rounded-full ${barColor}`;
        barEl.style.width = `${Math.min(percentage, 100)}%`;
    }

    calculateRiskScore(riskLevel) {
        const scores = {
            'minimal': 10,
            'low': 25,
            'moderate': 50,
            'high': 75,
            'critical': 95
        };
        return scores[riskLevel.toLowerCase()] || 10;
    }

    setupEventListeners() {
        // Emergency stop button
        document.getElementById('emergencyBtn').addEventListener('click', () => {
            if (this.socket && this.isConnected) {
                this.socket.emit('emergency_stop');
            }
            this.showEmergencyAlert({
                description: 'Manual emergency stop activated',
                recommendations: ['All systems halted', 'Awaiting manual reset']
            });
        });

        // VLM Analysis button
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.runVLMAnalysis();
        });
    }

    showEmergencyAlert(data) {
        const alertEl = document.getElementById('emergencyAlert');
        const messageEl = document.getElementById('emergencyMessage');
        
        messageEl.textContent = data.description || 'Emergency situation detected';
        alertEl.classList.remove('hidden');
        
        // Browser notification
        if (Notification.permission === 'granted') {
            new Notification('SafetyVision Emergency Alert', {
                body: data.description,
                icon: '/favicon.ico'
            });
        }
    }

    hideEmergencyAlert() {
        document.getElementById('emergencyAlert').classList.add('hidden');
    }

    setupChart() {
        const ctx = document.getElementById('safetyChart').getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.chartData.labels,
                datasets: [{
                    label: 'Confidence %',
                    data: this.chartData.confidence,
                    borderColor: '#00e676',
                    backgroundColor: 'rgba(0, 230, 118, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Risk Score',
                    data: this.chartData.riskScore,
                    borderColor: '#ff9800',
                    backgroundColor: 'rgba(255, 152, 0, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#333' },
                        ticks: { color: '#fff' }
                    },
                    x: {
                        grid: { color: '#333' },
                        ticks: { color: '#fff' }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#fff' }
                    }
                }
            }
        });
    }

    updateChart(confidence, riskScore) {
        const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        this.chartData.labels.push(now);
        this.chartData.confidence.push(confidence);
        this.chartData.riskScore.push(riskScore);
        
        // Keep only last 20 data points
        if (this.chartData.labels.length > 20) {
            this.chartData.labels.shift();
            this.chartData.confidence.shift();
            this.chartData.riskScore.shift();
        }
        
        this.chart.update();
    }

    startCameraFeed() {
        const canvas = document.getElementById('cameraCanvas');
        const ctx = canvas.getContext('2d');
        
        const drawFrame = () => {
            // Clear canvas
            ctx.fillStyle = '#1a1a1a';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Draw facility layout
            ctx.strokeStyle = '#00e676';
            ctx.lineWidth = 2;
            ctx.strokeRect(20, 20, canvas.width - 40, canvas.height - 40);
            
            // Draw equipment
            ctx.fillStyle = '#333';
            ctx.fillRect(50, 50, 60, 40);
            ctx.fillRect(150, 50, 60, 40);
            ctx.fillRect(250, 50, 60, 40);
            
            // Labels
            ctx.fillStyle = '#00e676';
            ctx.font = '10px monospace';
            ctx.fillText('REACTOR-1', 55, 75);
            ctx.fillText('PUMP-A', 160, 75);
            ctx.fillText('VALVE-B', 255, 75);
            
            // Sensor indicators
            ctx.fillStyle = '#ff9800';
            ctx.beginPath();
            ctx.arc(80, 40, 3, 0, 2 * Math.PI);
            ctx.fill();
            
            ctx.fillStyle = '#4caf50';
            ctx.beginPath();
            ctx.arc(180, 40, 3, 0, 2 * Math.PI);
            ctx.fill();
            
            ctx.beginPath();
            ctx.arc(280, 40, 3, 0, 2 * Math.PI);
            ctx.fill();
            
            // Update timestamp
            document.getElementById('cameraTimestamp').textContent = new Date().toLocaleTimeString();
        };
        
        // Update every second
        setInterval(drawFrame, 1000);
        drawFrame(); // Initial draw
    }

    runVLMAnalysis() {
        const btn = document.getElementById('analyzeBtn');
        const result = document.getElementById('analysisResult');
        
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyzing...';
        
        setTimeout(() => {
            const analysis = 'Visual analysis temporarily disabled (PyTorch security update required). ' +
                           'Simulated analysis: Facility equipment appears operational. ' +
                           'No visible structural damage detected. Personnel protective equipment required in Zone A.';
            
            result.querySelector('p').textContent = analysis;
            result.classList.remove('hidden');
            
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-robot mr-2"></i>Analyze with VLM';
        }, 3000);
    }

    generateMockData() {
        // Generate initial mock data if not connected to backend
        setInterval(() => {
            const mockData = {
                risk_level: ['MINIMAL', 'LOW', 'MODERATE'][Math.floor(Math.random() * 3)],
                confidence: 0.7 + Math.random() * 0.3,
                sensor_data: {
                    radiation_level: 0.05 + Math.random() * 0.1,
                    temperature: 20 + Math.random() * 15,
                    humidity: 50 + Math.random() * 30,
                    pressure: 1000 + Math.random() * 40
                }
            };
            
            if (!this.isConnected) {
                this.updateSafetyData(mockData);
            }
        }, 2000);
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Request notification permission
    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    new SafetyDashboard();
});