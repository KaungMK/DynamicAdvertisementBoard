# system_test.py
import os
import time
import subprocess
import json
import signal
import sys

def run_system_test():
    """
    Run a full system test of the Smart Advertisement Board
    """
    print("Starting system test...")
    
    # Create test data
    create_test_data()
    
    # Start the application
    print("Starting main application...")
    process = subprocess.Popen([sys.executable, "smart_ad_display.py"])
    
    try:
        # Wait for application to initialize
        time.sleep(5)
        
        # Test different scenarios
        test_no_audience()
        test_male_adult()
        test_female_youth()
        test_temperature_change()
        
        print("All tests completed successfully!")
        
    finally:
        # Clean up
        print("Terminating application...")
        process.send_signal(signal.SIGTERM)
        process.wait()

def create_test_data():
    # Create test environmental data
    env_data = [{"timestamp": "2025-03-30 10:00:00", "avg_dht_temp": 28.5, "avg_dht_humidity": 65.0}]
    with open("weather_data.json", "w") as f:
        json.dump(env_data, f)
    
    # Create test audience data with no audience
    audience_data = {"audience": [], "count": 0, "audience_present": False}
    with open("engagement_data.json", "w") as f:
        json.dump(audience_data, f)

def test_no_audience():
    print("Testing no audience scenario...")
    time.sleep(5)  # Give time for application to respond

def test_male_adult():
    print("Testing male adult audience...")
    audience_data = {
        "audience": [],
        "count": 0,
        "audience_present": True,
        "current_audience": {
            "count": 1,
            "age": 45.0,
            "gender": "M",
            "emotion": "Neutral"
        }
    }
    with open("engagement_data.json", "w") as f:
        json.dump(audience_data, f)
    time.sleep(10)  # Give time for application to respond

# Additional test functions...

if __name__ == "__main__":
    run_system_test()