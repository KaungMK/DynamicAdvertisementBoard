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

## Hardware Requirements

- Raspberry Pi 5 (recommended) or compatible single-board computer
- DHT11 Temperature/Humidity sensor connected to GPIO 17
- USB webcam for audience detection
- HDMI display for advertisement output
- Internet connection for API data (optional)

## Software Structure

The system consists of the following key components:

- **smart_ad_display.py**: Main application that manages the GUI and ad rotation
- **decision_engine.py**: Core logic for selecting optimal advertisements
- **temp_humd_sensor.py**: Temperature and humidity sensing module
- **engagement_analyzer.py**: Computer vision-based audience detection and analysis
- **wide_resnet.py**: Neural network model for age/gender detection

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

## Understanding the Data Flow

1. **Sensor Data Collection**:
   - Temperature/humidity data is saved to `weather_data.json`
   - Audience detection data is saved to `engagement_data.json`

2. **Decision Engine**:
   - Reads sensor data files every 5 seconds
   - Scores advertisements based on relevance to current conditions
   - Selects optimal advertisement to display

3. **Advertisement Display**:
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

### 1. Switch to the nina branch on a separate device:
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
