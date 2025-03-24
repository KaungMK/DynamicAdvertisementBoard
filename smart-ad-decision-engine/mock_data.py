"""
This file contains mock data to simulate sensors and advertisements,
updated to use the actual DynamoDB ad data structure
"""

# Simulated advertisements (structure based on your DynamoDB format)
ADS = [
    {
        "ad_id": "19",
        "age_group": "adult",
        "gender": "female",
        "humidity": "high",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/zara.jpg",
        "temperature": "rainy",
        "title": "zara"
    },
    {
        "ad_id": "18",
        "age_group": "teenager", 
        "gender": "female",
        "humidity": "high",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/sunscreen.jpg",
        "temperature": "hot",
        "title": "sunscreen"
    },
    {
        "ad_id": "17",
        "age_group": "adults",
        "gender": "both",
        "humidity": "high",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/sia.jpg",
        "temperature": "hot",
        "title": "singapore airlines"
    },
    {
        "ad_id": "16",
        "age_group": "adults",
        "gender": "female",
        "humidity": "moderate",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/sephora.jpg",
        "temperature": "cool",
        "title": "sephora"
    },
    {
        "ad_id": "15",
        "age_group": "adult",
        "gender": "female",
        "humidity": "high",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/puma.jpg",
        "temperature": "hot",
        "title": "puma"
    },
    {
        "ad_id": "14",
        "age_group": "children",
        "gender": "both",
        "humidity": "moderate",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/pizza_hut.png",
        "temperature": "cool",
        "title": "pizza hut"
    },
    {
        "ad_id": "13",
        "age_group": "adults",
        "gender": "both",
        "humidity": "high",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/ikea.jpg",
        "temperature": "rainy",
        "title": "ikea"
    },
    {
        "ad_id": "12",
        "age_group": "children",
        "gender": "male",
        "humidity": "high",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/ice_cream.jpg",
        "temperature": "hot",
        "title": "cornetto ice cream"
    },
    {
        "ad_id": "11",
        "age_group": "children",
        "gender": "male",
        "humidity": "high",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/ice_cream_mcd.jpg",
        "temperature": "hot",
        "title": "macdonald ice cream"
    },
    {
        "ad_id": "10",
        "age_group": "senior",
        "gender": "both",
        "humidity": "moderate",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/healthy_365.jpg",
        "temperature": "cool",
        "title": "healthy 365"
    },
    {
        "ad_id": "9",
        "age_group": "adults",
        "gender": "male",
        "humidity": "high",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/Gillette_shaver.jpg",
        "temperature": "hot",
        "title": "gillette shaver"
    },
    {
        "ad_id": "8",
        "age_group": "adults",
        "gender": "female",
        "humidity": "moderate",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/chanel_perfume_women.jpg",
        "temperature": "cool",
        "title": "chanel perfume"
    },
    {
        "ad_id": "7",
        "age_group": "adults",
        "gender": "female",
        "humidity": "moderate",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/beauty.jpg",
        "temperature": "cool",
        "title": "beauty"
    },
    {
        "ad_id": "6",
        "age_group": "adults",
        "gender": "all",
        "humidity": "high",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/anytime_fitness.jpg",
        "temperature": "hot",
        "title": "anytime fitness"
    },
    {
        "ad_id": "5",
        "age_group": "adults",
        "gender": "all",
        "humidity": "high",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/adidas.jpg",
        "temperature": "hot",
        "title": "adidas"
    },
    {
        "ad_id": "4",
        "age_group": "teenager",
        "gender": "male",
        "humidity": "high",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/100PLUS.jpg",
        "temperature": "hot",
        "title": "100 plus"
    },
    {
        "ad_id": "3",
        "age_group": "adults",
        "gender": "female",
        "humidity": "high",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/avatar_movie.jpg",
        "temperature": "rainy",
        "title": "avatar movie"
    },
    {
        "ad_id": "2",
        "age_group": "adults",
        "gender": "male",
        "humidity": "moderate",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/dior_perfume_men.jpg",
        "temperature": "cool",
        "title": "dior perfume"
    },
    {
        "ad_id": "1",
        "age_group": "teenagers",
        "gender": "male",
        "humidity": "high",
        "image_url": "https://adsbucket2009.s3.us-east-1.amazonaws.com/cocacola.jpg",
        "temperature": "high",
        "title": "cocacola"
    }
]

# Simulated environment scenarios
ENVIRONMENT_SCENARIOS = [
    {
        "name": "Hot Summer Day",
        "temperature": 32,  # Celsius
        "humidity": 65,     # Percentage
        "weather": "sunny",
        "time_of_day": "afternoon"
    },
    {
        "name": "Rainy Morning",
        "temperature": 22,
        "humidity": 85,
        "weather": "rainy",
        "time_of_day": "morning"
    },
    {
        "name": "Cool Evening",
        "temperature": 18,
        "humidity": 45,
        "weather": "clear",
        "time_of_day": "evening"
    },
    {
        "name": "Humid Overcast Day",
        "temperature": 26,
        "humidity": 78,
        "weather": "cloudy",
        "time_of_day": "afternoon"
    }
]

# Simulated audience scenarios
AUDIENCE_SCENARIOS = [
    {
        "name": "Young Adults Group",
        "estimated_age_group": "adult",
        "gender_distribution": "mixed",  # 'mostly_male', 'mostly_female', 'mixed'
        "group_size": 3,
        "attention_span": 8  # seconds
    },
    {
        "name": "Family with Children",
        "estimated_age_group": "mixed",
        "gender_distribution": "mixed",
        "group_size": 4,
        "attention_span": 5
    },
    {
        "name": "Elderly Couple",
        "estimated_age_group": "elderly",
        "gender_distribution": "mixed",
        "group_size": 2,
        "attention_span": 12
    },
    {
        "name": "Teenage Friends",
        "estimated_age_group": "teenager",
        "gender_distribution": "mostly_female",
        "group_size": 5,
        "attention_span": 4
    }
]

# Return mapped values based on raw sensor data
def map_temperature(temp_celsius):
    """Map temperature in Celsius to categorical value"""
    if temp_celsius < 15:
        return "cold"
    elif temp_celsius < 25:
        return "moderate"
    else:
        return "hot"

def map_humidity(humidity_percent):
    """Map humidity percentage to categorical value"""
    if humidity_percent < 40:
        return "low"
    elif humidity_percent < 70:
        return "medium"
    else:
        return "high"

def map_weather(weather_condition):
    """Map detailed weather to simplified categories"""
    weather_mapping = {
        "sunny": "clear",
        "clear": "clear",
        "partly_cloudy": "clear",
        "cloudy": "cloudy",
        "overcast": "cloudy",
        "rainy": "rainy",
        "drizzle": "rainy",
        "stormy": "rainy"
    }
    return weather_mapping.get(weather_condition, "clear")

def map_age_group(age_group):
    """Standardize age group terminology"""
    mapping = {
        "child": "children",
        "children": "children",
        "teen": "teenager",
        "teenager": "teenager",
        "adult": "adult",
        "adults": "adult",
        "elderly": "elderly",
        "senior": "elderly",
        "all": "all",
        "any": "all",
        "mixed": "all"
    }
    return mapping.get(age_group.lower(), "all")

def map_gender(gender_value):
    """Standardize gender terminology"""
    mapping = {
        "male": "male",
        "female": "female",
        "both": "both",
        "any": "both",
        "mixed": "both",
        "mostly_male": "male",
        "mostly_female": "female",
        "all": "both"
    }
    return mapping.get(gender_value.lower(), "both")