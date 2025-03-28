import time
import json
import adafruit_dht
import board
import requests
import uuid
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenWeather API Configuration
API_KEY = os.getenv("API_KEY")  # Get API key from .env
CITY = "Singapore"
API_URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"

# Initialize DHT11 Sensor on GPIO 4
dht_device = adafruit_dht.DHT11(board.D4)

# File to store JSON data
json_filename = "weather_data.json"
api_cache_filename = "latest_api_data.json"

# Function to get weather data from API (every 5 minutes)
def get_weather():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            api_data = {
                "temp": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "timestamp": time.time()  # Store timestamp for checking
            }
            with open(api_cache_filename, "w") as file:
                json.dump(api_data, file, indent=4)
            return api_data
        else:
            print("Error fetching API data")
            return None
    except Exception as e:
        print(f"API Error: {e}")
        return None

# Function to read stored API data
def get_stored_api_data():
    try:
        with open(api_cache_filename, "r") as file:
            data = json.load(file)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# Function to read sensor data
def get_dht11_data():
    try:
        # Directly access temperature and humidity from the sensor
        temperature_c = dht_device.temperature
        humidity = dht_device.humidity
        print(f"Temp: {temperature_c:.1f} C    Humidity: {humidity}%")
        return {"temp": temperature_c, "humidity": humidity}
    except RuntimeError as err:
        print(f"Sensor Error: {err.args[0]}")
    return None

# Function to predict weather based on sensor and API data
def predict_weather(dht_temp, dht_humidity, api_temp, api_humidity, api_pressure):
    
    # Compute final averages inside the function
    avg_temp = (dht_temp + api_temp) / 2
    avg_humidity = (dht_humidity + api_humidity) / 2

    print(f"avg temp: {avg_temp}")
    print(f"avg hum: {avg_humidity}")


    # Clear weather (Moderate humidity, high pressure)
    if avg_temp >= 27 and avg_temp <= 30 and avg_humidity < 70 and api_pressure > 1010:
        return "Clear"
    
    # Cloudy weather (High humidity, moderate temperature)
    elif avg_temp >= 25 and avg_temp <= 30 and avg_humidity >= 70 and avg_humidity < 85 and api_pressure >= 1000 and api_pressure <= 1010:
        return "Cloudy"
    
    # Rainy weather (Very high humidity, low pressure)
    elif avg_humidity >= 85 and api_humidity >= 85 and api_pressure < 1000:
        return "Rain"
    
    # Heavy rain (Very low pressure, extreme humidity)
    elif api_pressure < 990 and api_humidity > 90:
        return "Heavy Rain"
    
    # Sunny (Very hot, lower humidity)
    elif avg_temp > 30 and avg_humidity < 65:
        return "Sunny"
        
    # Clear (Warm temperature, ignore humidity)
    elif avg_temp >= 27 and avg_temp <= 30:
        return "Clear"
        
    # Sunny (High temperature, ignore humidity)
    elif avg_temp > 31:
        return "Sunny"
        
    
    return "Unknown"

# Settings
SENSOR_READ_INTERVAL = 2  # Collect data every 2 sec
AVG_PERIOD = 30  # Average over 30 seconds
API_UPDATE_INTERVAL = 300  # Fetch API data every 5 minutes (300 seconds)

last_api_update = 0
sensor_readings = []

# Main Loop
while True:
    # Check if we need to fetch new API data
    current_time = time.time()
    api_data = get_stored_api_data()
    
    if not api_data or (current_time - api_data["timestamp"] >= API_UPDATE_INTERVAL):
        print("Fetching new API data...")
        api_data = get_weather()
    else:
        print("Using cached API data.")

    if not api_data:
        print("No API data available, skipping cycle.")
        time.sleep(SENSOR_READ_INTERVAL)
        continue

    # Start collecting sensor data
    start_time = time.time()
    sensor_readings.clear()

    while time.time() - start_time < AVG_PERIOD:
        dht_data = get_dht11_data()
        if dht_data:
            sensor_readings.append(dht_data)
        time.sleep(SENSOR_READ_INTERVAL)

    # Compute Averages
    if sensor_readings:
        avg_temp = sum(d["temp"] for d in sensor_readings) / len(sensor_readings)
        avg_humidity = sum(d["humidity"] for d in sensor_readings) / len(sensor_readings)
    else:
        print("No valid sensor data collected.")
        continue

    # Predict Weather
    predicted_weather = predict_weather(avg_temp, avg_humidity, api_data["temp"], api_data["humidity"], api_data["pressure"])

    # Prepare JSON Data
    weather_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "avg_dht_temp": round(avg_temp, 2),
        "avg_dht_humidity": round(avg_humidity, 2),
        "api_temp": api_data["temp"],
        "api_humidity": api_data["humidity"],
        "api_pressure": api_data["pressure"],
        "predicted_weather": predicted_weather
    }

    # Save JSON Data
    try:
        with open(json_filename, "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append(weather_entry)

    with open(json_filename, "w") as file:
        json.dump(data, file, indent=4)

    print(f"Data Saved - {weather_entry}")

