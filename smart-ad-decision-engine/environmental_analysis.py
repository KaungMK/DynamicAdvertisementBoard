"""
This file simulates the environmental analysis that would normally come from sensors
"""

from datetime import datetime
import random
from mock_data import map_temperature, map_humidity, map_weather

class WeatherClassifier:
    """
    Simulates the environmental analysis component of the system
    In a real system, this would process raw sensor data
    """
    
    def __init__(self):
        # Normally would initialize sensor connections or ML models here
        pass
    
    def classify(self, temperature, humidity, weather_condition=None):
        """
        Classify current environmental conditions based on sensor data
        
        Args:
            temperature (float): Temperature in Celsius
            humidity (float): Humidity percentage
            weather_condition (str, optional): Direct weather input (for simulation)
            
        Returns:
            dict: Weather context with categorized values
        """
        # Determine time of day based on current time
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            time_of_day = "morning"
        elif 12 <= current_hour < 17:
            time_of_day = "afternoon"
        else:
            time_of_day = "evening"
            
        # Map continuous values to categorical for decision-making
        temperature_category = map_temperature(temperature)
        humidity_category = map_humidity(humidity)
        
        # In a real system, this might use sensor fusion to determine weather
        # For simulation, use provided weather or random if none
        if weather_condition is None:
            possible_conditions = ["sunny", "cloudy", "rainy"]
            weights = [0.6, 0.3, 0.1]  # Default to mostly sunny
            
            # Adjust weights based on humidity
            if humidity > 80:
                weights = [0.2, 0.3, 0.5]  # More likely to rain when humid
                
            weather_condition = random.choices(possible_conditions, weights=weights, k=1)[0]
        
        # Create weather context object
        weather_context = {
            "temperature": temperature,
            "temperature_category": temperature_category,
            "humidity": humidity,
            "humidity_category": humidity_category,
            "weather": map_weather(weather_condition),
            "time_of_day": time_of_day,
            "day_of_week": datetime.now().strftime("%A").lower()
        }
        
        return weather_context
    
    def simulate_reading(self, scenario=None):
        """
        Simulate a sensor reading (for testing without hardware)
        
        Args:
            scenario (dict, optional): Predefined environmental scenario
            
        Returns:
            dict: Simulated weather context
        """
        if scenario:
            # Use the provided scenario
            return self.classify(
                scenario["temperature"],
                scenario["humidity"],
                scenario["weather"]
            )
        else:
            # Generate random values within realistic ranges
            temperature = random.uniform(10, 35)  # 10°C to 35°C
            humidity = random.uniform(30, 90)     # 30% to 90%
            return self.classify(temperature, humidity)