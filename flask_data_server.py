# flask_data_server.py
from flask import Flask, jsonify, send_file, render_template_string
from flask_cors import CORS
import json
import os
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FlaskDataServer")

# Path to data files
base_dir = "/home/EDGY/Documents/DynamicAdvertisementBoard"
env_data_file = os.path.join(base_dir, "weather_data.json")
audience_data_file = os.path.join(base_dir, "engagement_data.json")

# Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# HTML template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Ad Board Dashboard</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f7f7f7;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        h1 {
            color: #333;
            margin: 0;
        }
        .container { 
            display: flex; 
            gap: 20px; 
            flex-wrap: wrap;
        }
        .card { 
            flex: 1; 
            min-width: 300px;
            border: 1px solid #ddd; 
            border-radius: 8px; 
            padding: 20px; 
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h2 { 
            margin-top: 0; 
            color: #333; 
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        .status { 
            font-weight: bold; 
            padding: 10px;
            border-radius: 4px;
            display: flex;
            align-items: center;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .connected { 
            color: green; 
            background-color: rgba(0, 128, 0, 0.1);
        }
        .connected .status-indicator {
            background-color: green;
        }
        .disconnected { 
            color: red; 
            background-color: rgba(255, 0, 0, 0.1);
        }
        .disconnected .status-indicator {
            background-color: red;
        }
        .connecting { 
            color: orange; 
            background-color: rgba(255, 165, 0, 0.1);
        }
        .connecting .status-indicator {
            background-color: orange;
        }
        .data-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 1px solid #f0f0f0;
        }
        .data-label {
            font-weight: bold;
            color: #555;
        }
        .data-value {
            color: #333;
        }
        .timestamp {
            font-size: 0.85em;
            color: #777;
            text-align: right;
            margin-top: 15px;
        }
        .info-box {
            background-color: #e8f4fd;
            border-left: 4px solid #3498db;
            padding: 10px 15px;
            margin-top: 20px;
            font-size: 0.9em;
            color: #333;
        }
        #update-timer {
            background-color: #eee;
            border-radius: 12px;
            padding: 2px 8px;
            margin-left: 10px;
            font-size: 0.8em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Smart Advertisement Board - Live Dashboard</h1>
        <div class="status connected" id="connection-status">
            <span class="status-indicator"></span>
            Status: Connected <span id="update-timer">3</span>
        </div>
    </div>
    
    <div class="container">
        <div class="card">
            <h2>Environmental Data</h2>
            <div id="env-data">
                <div class="data-row">
                    <span class="data-label">Status:</span>
                    <span class="data-value">Waiting for data...</span>
                </div>
            </div>
        </div>
        <div class="card">
            <h2>Audience Data</h2>
            <div id="audience-data">
                <div class="data-row">
                    <span class="data-label">Status:</span>
                    <span class="data-value">Waiting for data...</span>
                </div>
            </div>
        </div>
    </div>
    
    <div class="info-box">
        <strong>Dashboard Info:</strong> Data updates automatically every 3 seconds.
        Powered by Flask on Raspberry Pi (192.168.50.200).
    </div>
    
    <script>
        let updateTimer = 3;
        let updateInterval = 3000; // 3 seconds
        let timerInterval;
        
        function formatDataRow(label, value, unit = '') {
            return `
                <div class="data-row">
                    <span class="data-label">${label}:</span>
                    <span class="data-value">${value}${unit}</span>
                </div>
            `;
        }
        
        function updateDashboard() {
            fetch('/api/data')
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    // Update status
                    document.getElementById('connection-status').className = 'status connected';
                    
                    // Update environmental data
                    if (data.environmental) {
                        const env = data.environmental;
                        let envHtml = '';
                        
                        // Temperature
                        if (env.avg_dht_temp !== undefined) {
                            envHtml += formatDataRow('Temperature', env.avg_dht_temp.toFixed(1), '°C');
                        }
                        
                        // Humidity
                        if (env.avg_dht_humidity !== undefined) {
                            envHtml += formatDataRow('Humidity', env.avg_dht_humidity.toFixed(1), '%');
                        }
                        
                        // Weather
                        if (env.predicted_weather) {
                            envHtml += formatDataRow('Weather', env.predicted_weather);
                        }
                        
                        // API Data
                        if (env.api_temp !== undefined) {
                            envHtml += formatDataRow('API Temperature', env.api_temp.toFixed(1), '°C');
                        }
                        
                        if (env.api_pressure !== undefined) {
                            envHtml += formatDataRow('Pressure', env.api_pressure, ' hPa');
                        }
                        
                        // Add timestamp
                        const envTimestamp = env.timestamp || new Date().toISOString();
                        const formattedEnvTime = new Date(envTimestamp).toLocaleString();
                        envHtml += `<div class="timestamp">Updated: ${formattedEnvTime}</div>`;
                        
                        document.getElementById('env-data').innerHTML = envHtml;
                    }
                    
                    // Update audience data
                    if (data.audience) {
                        const audience = data.audience;
                        let audienceHtml = '';
                        
                        // Audience presence
                        const audiencePresent = audience.audience_present;
                        audienceHtml += formatDataRow('Audience Present', audiencePresent ? 'Yes' : 'No');
                        
                        if (audiencePresent && audience.current_audience) {
                            const current = audience.current_audience;
                            
                            // Count
                            if (current.count !== undefined) {
                                audienceHtml += formatDataRow('Count', current.count, ' people');
                            }
                            
                            // Age
                            if (current.age !== undefined) {
                                audienceHtml += formatDataRow('Average Age', current.age.toFixed(1), ' years');
                            }
                            
                            // Gender
                            if (current.gender) {
                                const genderLabel = current.gender === 'M' ? 'Male' : 
                                                current.gender === 'F' ? 'Female' : current.gender;
                                audienceHtml += formatDataRow('Gender', genderLabel);
                            }
                            
                            // Emotion
                            if (current.emotion) {
                                audienceHtml += formatDataRow('Emotion', current.emotion);
                            }
                        }
                        
                        // Total detected
                        audienceHtml += formatDataRow('Total Detected', audience.count || 0, ' people');
                        
                        // Add timestamp
                        const now = new Date().toLocaleString();
                        audienceHtml += `<div class="timestamp">Updated: ${now}</div>`;
                        
                        document.getElementById('audience-data').innerHTML = audienceHtml;
                    }
                    
                    // Reset timer
                    updateTimer = 3;
                    document.getElementById('update-timer').textContent = updateTimer;
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                    document.getElementById('connection-status').className = 'status disconnected';
                    document.getElementById('connection-status').innerHTML = '<span class="status-indicator"></span>Status: Disconnected';
                });
        }
        
        // Initial data load
        updateDashboard();
        
        // Setup timer for countdown display
        timerInterval = setInterval(() => {
            updateTimer -= 1;
            if (updateTimer <= 0) {
                updateTimer = 3;
            }
            document.getElementById('update-timer').textContent = updateTimer;
        }, 1000);
        
        // Setup automatic refresh
        setInterval(updateDashboard, updateInterval);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the dashboard HTML page"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/data')
def get_data():
    """API endpoint to get the latest sensor data"""
    try:
        # Read environmental data
        env_data = {}
        if os.path.exists(env_data_file):
            try:
                with open(env_data_file, 'r') as f:
                    env_data_raw = json.load(f)
                    if env_data_raw and isinstance(env_data_raw, list):
                        env_data = env_data_raw[-1]  # Get most recent entry
            except Exception as e:
                logger.error(f"Error reading environment file: {e}")
        
        # Read audience data
        audience_data = {}
        if os.path.exists(audience_data_file):
            try:
                with open(audience_data_file, 'r') as f:
                    audience_data = json.load(f)
            except Exception as e:
                logger.error(f"Error reading audience file: {e}")
        
        # Combine data
        combined_data = {
            "environmental": env_data,
            "audience": audience_data,
            "timestamp": time.time(),
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return jsonify(combined_data)
    except Exception as e:
        logger.error(f"Error processing data request: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Flask server on port 5000")
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}")