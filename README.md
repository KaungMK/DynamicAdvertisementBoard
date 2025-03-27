# Smart Advertisement Board Dashboard (Local Storage Version)

This dashboard integrates with the Decision Engine for the Smart Advertisement Board system that displays dynamic content based on real-time environmental and audience analysis. This version uses local file storage instead of AWS services.

## Features

- **Two Tab Interface**:
  - **Advertisement Display** - Shows advertisements in rotation (5 seconds per ad)
  - **Admin Dashboard** - Provides control and monitoring of the system

- **Environment Simulation**:
  - Temperature, humidity, and weather condition controls
  - Predefined environmental scenarios

- **Audience Simulation**:
  - Group size, age group, and gender distribution controls
  - Predefined audience scenarios

- **Decision Engine**:
  - Rule-based advertisement selection
  - Context-aware decision making
  - Scoring system based on multiple factors
  - Performance metrics tracking

- **Local Storage**:
  - Uses local image files instead of AWS S3
  - Stores ad metadata in a local JSON file
  - No internet connection required

## Installation

1. Ensure you have Python 3.6+ installed.
2. Install required packages:

```bash
pip install pillow tkinter
```

3. Create a folder called `Advertisements` and place your advertisement images (JPG/PNG files) in it.
4. Run the create_sample_metadata.py script to generate metadata for your images:

```bash
python create_sample_metadata.py
```

## Running the Dashboard

Run the dashboard:

```bash
python run_local_dashboard.py
```

Run in fullscreen mode:

```bash
python run_local_dashboard.py --fullscreen
```

Specify a custom advertisements folder:

```bash
python run_local_dashboard.py --ads-folder="path/to/ads"
```

## Files in this Project

- **local_dashboard.py** - Main dashboard application with display and admin interfaces
- **run_local_dashboard.py** - Entry point script with command line options
- **local_content_repository.py** - Manages local advertisement content and metadata
- **create_sample_metadata.py** - Creates initial metadata for advertisement images
- **decision_engine.py** - Core decision-making logic
- **environmental_analysis.py** - Simulates environmental sensing
- **demographic_analysis.py** - Simulates audience detection
- **display_manager.py** - Handles displaying advertisements
- **mock_data.py** - Contains simulated data for testing

## Structure of ad_metadata.json

The metadata file (`ad_metadata.json`) contains information about each advertisement:

```json
[
  {
    "ad_id": "1",
    "title": "coca_cola",
    "image_file": "coca_cola.jpg",
    "age_group": "all",
    "gender": "both",
    "temperature": "hot",
    "humidity": "medium"
  },
  ...
]
```

You can edit this file manually, or use the "Edit Ad Metadata" button in the Admin Dashboard.

## Admin Dashboard Tabs

1. **Current Status** - Shows real-time system state
2. **Performance** - Displays ad performance metrics
3. **Decision Rules** - View and edit decision engine rules
4. **Ad Inventory** - Browse and manage advertisements

## Usage Instructions

1. Use the **Environment Settings** and **Audience Settings** panels to simulate different conditions
2. Apply preset scenarios using the **Scenario Presets** dropdown menus
3. Click **Show Next Advertisement** to manually advance ads or toggle **Auto-cycle ads** for automatic rotation
4. Monitor the decision-making process and performance in the **Statistics & Monitoring** tabs
5. Edit advertisement metadata by selecting an ad in the inventory and clicking **Edit Ad Metadata**

## Notes for Implementation with Hardware

To implement this system with actual Raspberry Pi and sensors:

1. Replace the simulated sensor data with actual readings from GPIO-connected sensors
2. Connect a camera and implement OpenCV or TensorFlow for audience analysis
3. Configure the display output to work with your specific display hardware
4. Set up automated startup on boot

# Smart Advertisement Board Dashboard (AWS Cloud Version)

## Connecting with aws Dynamodb & S3

## Installation

1. Ensure you have Python 3.6+ installed.
2. Install required packages:

```bash
pip install boto3

sudo apt install awscli -y
```

## AWS Setup

1. Create aws directory.

```bash
mkdir -p ~/.aws
```

2. Go to AWS Details > AWS CLI > Show copy the aws credentials.
3. Enter the aws credentials.

```bash
nano ~/.aws/credentials
```
4. Press CTRL + X to exit.
5. Press Y to confirm saving.
6. Press Enter to save the file.
7. Check aws credentials.

```bash
aws sts get-caller-identity
```
8. Should see something like below:

```bash
{
"UserId": "ABCDEFGHI1234567890",
"Account": "123456789012",
"Arn": "arn:aws:iam::123456789012:user/your-user"
}
```
