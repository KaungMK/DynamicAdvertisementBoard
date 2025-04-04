# Smart Advertisement Board System

A dynamic digital advertisement system that adapts content based on real-time environmental conditions and audience analysis. The system integrates temperature/humidity sensors and computer vision-based audience detection to display the most relevant advertisements.

## System Overview

The Smart Advertisement Board consists of three main components:

1. **Sensor Systems**
   - Temperature and humidity sensing
   - Computer vision-based audience detection and analysis

2. **Decision Engine**
   - Rule-based advertisement selection
   - Context-aware decision making based on environmental and audience data
   - Scoring system for optimal ad selection

3. **Display Interface**
   - Full-screen advertisement display
   - Real-time sensor data visualization
   - Support for Raspberry Pi 5 with HDMI output

## Key Features

- **Dynamic Content Selection**: Displays ads based on current temperature, humidity, and audience demographics
- **Real-time Audience Analysis**: Detects age, gender, emotion, and engagement level of viewers
- **Weather Context**: Integrates temperature/humidity data to show weather-appropriate ads
- **Historical Tracking**: Maintains records of audience engagement and ad displays
- **Responsive Interface**: Full-screen GUI with real-time sensor data display
- **Web Dashboard**: Real-time monitoring of system and audience metrics

## Edge Computing Benefits

- **Minimized Latency**: By performing all computations locally, the system drastically reduces data transmission delays, ensuring near real-time analytics crucial for immediate-response applications
- **Heightened Privacy and Security**: Processing sensitive data, such as facial images, directly on the device eliminates the need for cloud storage, thereby significantly reducing the risk of data breaches
- **Optimized Bandwidth Consumption**: With on-device processing, raw video data is never transmitted to central servers, conserving network bandwidth and lowering operational costs
- **Increased Operational Reliability**: Edge computing enables the system to operate independently of network connectivity, ensuring uninterrupted service even in areas with unstable internet
- **Enhanced Cost Efficiency**: Reduced reliance on cloud infrastructure translates to lower operational and maintenance expenses, making the solution economically viable for large-scale deployments
- **Optimized Processing Power**: The system conserves computational resources by analyzing only engaged audiences—those meeting defined duration and head movement thresholds—ensuring that processing power is dedicated solely to relevant interactions

## Hardware Requirements

- Raspberry Pi 5 (recommended) or compatible single-board computer
- DHT11 Temperature/Humidity sensor connected to GPIO 17
- USB webcam for audience detection
- HDMI display for advertisement output
- Internet connection for API data (optional)

## Software Structure

The system consists of the following key components:

## smart_ad_display.py - Detailed Technical Documentation

The main application that manages the full-screen advertisement display interface and system orchestration.

### Core Functionality
- **Full-screen Display Management**: Creates a borderless, always-on-top window optimized for digital signage
- **Sensor Integration**: Coordinates temperature/humidity and audience detection subsystems
- **Dynamic Content Delivery**: Handles advertisement selection and display rotation
- **Real-time Data Visualization**: Shows current sensor readings in header panels

### Key Components
1. **AWSContentRepository Class**
   - Manages connection to AWS DynamoDB and S3
   - Methods:
     - `get_all_ads()`: Retrieves all advertisements from DynamoDB
     - `get_ad_by_id()`: Fetches specific advertisement by ID

2. **SmartAdDisplay Class**
   - Main application class with these critical methods:
     - `create_layout()`: Builds the complex GUI with:
       - Scrollable sensor data panels
       - Full-screen advertisement display area
       - Footer with ad metadata
       - Window control buttons
     - `start_sensor_processes()`: Launches subprocesses for:
       - Temperature/humidity monitoring
       - Audience engagement analysis
       - Flask dashboard server
     - `display_ad()`: Handles image downloading, resizing, and display with:
       - Dynamic sizing based on screen dimensions
       - Purple border styling
       - Error handling for missing images

3. **Thread Management**
   - `auto_cycle_thread()`: Controls ad rotation timing (default 10s)
   - `sensor_update_thread_func()`: Updates sensor displays every 5s

4. **Advanced Features**
   - Fullscreen/windowed mode toggling (Ctrl+M)
   - Graceful shutdown handling that:
     - Terminates all subprocesses
     - Uploads sensor data to DynamoDB
     - Maintains upload tracking to prevent duplicates
   - Dynamic ad sizing that maintains aspect ratio

### Data Flow
1. On startup:
   - Initializes AWS connections
   - Launches sensor subprocesses
   - Begins ad rotation thread
2. Continuous operation:
   - Checks sensor data files for updates
   - Requests optimal ad from decision engine
   - Displays selected ad with metadata
3. On shutdown:
   - Uploads all collected data to DynamoDB
   - Records upload tracking information
   - Cleans up all system resources

### Technical Specifications
- **Screen Resolution Handling**: Dynamically adapts to any display size
- **Image Processing**: Uses PIL for high-quality image resizing
- **Error Handling**: Comprehensive logging for all operations
- **Performance**: Optimized for Raspberry Pi 5 with:
  - Threaded operations to prevent UI freezing
  - Caching of frequently accessed data

## decision_engine.py - Detailed Technical Documentation

The brain of the system that selects the most contextually relevant advertisements.

### Core Algorithm
1. **Context Collection**:
   - Environmental (temperature, humidity, weather)
   - Audience (demographics, presence, emotion)
2. **Multi-stage Filtering**:
   - Strict demographic matching when audience present
   - Environmental matching when no audience
3. **Scoring System**:
   - Weighted combination of factors
   - Recent display penalty to ensure variety

### Key Components
1. **ContentDecisionEngine Class**
   - Main class with these critical methods:
     - `get_environmental_context()`: Reads and categorizes sensor data
     - `get_audience_context()`: Processes audience detection data
     - `select_optimal_content()`: Core decision-making algorithm

2. **Relevance Calculation**
   - `calculate_demographic_relevance()`:
     - 90% penalty for gender mismatch
     - 80% penalty for age mismatch
     - 2x bonus for perfect matches
   - `calculate_environmental_relevance()`:
     - 80% penalty for temperature mismatch
     - 30% penalty for humidity mismatch

3. **Scoring System**
   - Base score from display history
   - Audience present weights:
     - 70% demographic relevance
     - 20% display history
     - 10% environmental
   - No audience weights:
     - 60% environmental
     - 30% display history
     - 10% demographic

4. **History Management**
   - Tracks last 50 displayed ads
   - Implements score decay over time
   - Persistent storage in JSON file

### Advanced Features
1. **Multi-stage Filtering**:
   - First pass: Perfect demographic matches
   - Second pass: Gender matches only
   - Fallback: Environmental matches
2. **Weighted Random Selection**:
   - Chooses from top 3 scored ads
   - Uses score-based weighting
3. **File Watchdog**: 
   - Tracks file modifications
   - Caches data to reduce I/O
   - Force refresh capability

### flask_data_server.py - Real-time Dashboard
The Flask-based web server that provides real-time monitoring of system data.

#### Core Functionality
- **REST API Endpoint**: `/api/data` that serves:
  - Latest environmental sensor readings
  - Current audience analytics
  - System timestamp information
- **Interactive Dashboard**:
  - Auto-refreshing HTML interface
  - Visual status indicators
  - Responsive card-based layout

#### Key Features
1. **Data Handling**:
   - Reads from `weather_data.json` and `engagement_data.json`
   - Provides most recent data entry for environmental readings
   - Returns full audience detection dataset

2. **Dashboard Interface**:
   - Clean, modern UI with:
     - Status indicators
     - Timestamp tracking
     - Automatic refresh every 3 seconds
   - Client-side JavaScript for:
     - Dynamic data updates
     - Connection status monitoring
     - Visual countdown timer

3. **Technical Specifications**:
   - Built with Flask and Flask-CORS
   - Serves pre-rendered HTML template
   - Comprehensive error handling
   - Production-ready configuration (debug=False)

#### Data Endpoints
- `GET /` - Serves the dashboard HTML
- `GET /api/data` - Returns JSON with:
  ```json
  {
    "environmental": {
      "avg_dht_temp": float,
      "avg_dht_humidity": float,
      "predicted_weather": string,
      "timestamp": ISO8601
    },
    "audience": {
      "audience_present": bool,
      "count": int,
      "current_audience": {
        "age": float,
        "gender": "M/F",
        "emotion": string,
        "count": int
      }
    }
  }

### Supporting Components:
- **temp_humd_sensor.py**: Temperature and humidity sensing module
- **engagement_analyzer.py**: Computer vision-based audience detection and analysis
- **wide_resnet.py**: Neural network model for age/gender detection
- **flask_data_server.py**: Web dashboard for real-time system monitoring

## Installation

### 1. Install Required Packages

```bash
pip install -r requirements.txt
sudo apt-get install python3-opencv python3-dlib
```

### 2. Set Up Project Directory

```bash
mkdir -p ~/Documents/DynamicAdvertisementBoard
mkdir -p ~/Documents/DynamicAdvertisementBoard/sensors
mkdir -p ~/Documents/DynamicAdvertisementBoard/models
```

### 3. Download Pre-trained Models

The system uses pre-trained models for age/gender estimation and emotion detection. Download these to the models directory:

```bash
# Emotion detection model
# URL: https://github.com/oarriaga/face_classification/releases/download/v0.5/emotion_little_vgg_2.h5
# Place in: ~/Documents/DynamicAdvertisementBoard/models/
```

The age/gender model will be downloaded automatically at first run.

### 4. Connect to AWS (Optional)

For using AWS backend storage:

```bash
# Install AWS CLI
sudo apt install awscli -y

# Set up credentials
mkdir -p ~/.aws
nano ~/.aws/credentials
```

Enter your AWS credentials in the format:
```
[default]
aws_access_key_id=YOUR_ACCESS_KEY
aws_secret_access_key=YOUR_SECRET_KEY
region=us-east-1
```

Verify your credentials:
```bash
aws sts get-caller-identity
```

## Running the System

### 1. Start the Main Application

```bash
cd ~/Documents/DynamicAdvertisementBoard
python smart_ad_display.py
```

### 2. Sensor Scripts (Auto-started by Main App)

The main application automatically starts the following sensor scripts:

- `sensors/temp_humd_sensor.py`: Reads temperature and humidity data
- `sensors/engagement_analyzer.py`: Analyzes audience using computer vision
- `flask_data_server.py`: Launches web dashboard for real-time monitoring

### 3. Accessing the Web Dashboard

- **URL**: `http://[RASPBERRY_PI_IP]:5000`
- **Features**: 
  - Real-time sensor data visualization
  - Audience demographics
  - System status indicators
- Dashboard auto-updates every 3 seconds

## Understanding the Data Flow

1. **Sensor Data Collection**:
   - Temperature/humidity data is saved to `weather_data.json`
   - Audience detection data is saved to `engagement_data.json`

2. **Decision Engine**:
   - Reads sensor data files every 5 seconds
   - Scores advertisements based on relevance to current conditions
   - Selects optimal advertisement to display

3. **Web Dashboard**:
   - Flask-based real-time monitoring interface
   - Provides `/api/data` endpoint for accessing current sensor and audience data
   - Auto-refreshes every 3 seconds
   - Displays:
     - Environmental sensor readings
     - Audience demographic information
     - System status indicators

4. **Advertisement Display**:
   - Updates the full-screen interface with the selected ad
   - Shows current sensor data in the header panels
   - Rotates advertisements automatically

## Troubleshooting

- **Sensor Connectivity**: Ensure the DHT11 sensor is properly connected to GPIO 17(or whichever you prefer)
- **Camera Issues**: Verify that the webcam is recognized (`ls /dev/video*`)
- **Display Problems**: Use `xrandr` to check available display resolutions
- **Audience Detection**: Ensure proper lighting for better face detection

## Analytics Dashboard (nina branch)
This branch contains a standalone Flask-based analytics dashboard for visualizing historical ad data. It includes interactive filters, KPI summaries, and insightful charts to better understand audience and ad performance trends.

### 1. Switch to the branch on a separate device:
```
git checkout nina
```

### 2. Set up a virtual environment:
```
python -m venv venv
# For Windows
venv/Scripts/activate
```

### 3. Install dependencies:
```
pip install -r requirements.txt
```

### 4. Run the Flask app:
```
python app.py
```

### 5. Open your browser and go to:
```
http://localhost:5000/analytics
```

## Notes for Implementation

- The system is designed to run on boot on a Raspberry Pi 5
- To make the system start on boot, add to `/etc/rc.local`:
  ```
  python /home/EDGY/Documents/DynamicAdvertisementBoard/smart_ad_display.py &
  ```
- Press ESC key to exit fullscreen mode, or Ctrl+Q to quit entirely
- Use VNC or SSH for remote management

## Advanced Configuration

### AWS Integration

The system can integrate with AWS services:

- **DynamoDB**: Stores advertisement metadata
- **S3**: Stores advertisement images

Edit the `AWSContentRepository` class parameters in `smart_ad_display.py` to configure your AWS settings:

```python
self.content_repository = AWSContentRepository(
    table_name='your-dynamodb-table',
    region_name='your-aws-region'
)
```

### Local Storage Mode

To use local storage instead of AWS, modify the `AWSContentRepository` to use local file storage.
