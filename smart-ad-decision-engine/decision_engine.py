"""
Enhanced Decision Engine with integration for new sensor data formats
"""

import json
import random
import logging
from datetime import datetime
import os
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DecisionEngine")

class ContentDecisionEngine:
    """
    Enhanced decision engine with integration for engagement analyzer and temperature/humidity sensor
    """
    
    def __init__(self, content_repository, 
                 env_data_file="weather_data.json",
                 audience_data_file="engagement_data.json",
                 history_file="ad_display_history.json"):
        """
        Initialize the decision engine
        
        Args:
            content_repository: Repository for accessing ad content
            env_data_file (str): Path to JSON file with environmental data
            audience_data_file (str): Path to JSON file with audience data
            history_file (str): Path to JSON file to store ad display history
        """
        self.content_repository = content_repository
        self.env_data_file = env_data_file
        self.audience_data_file = audience_data_file
        self.history_file = history_file
        
        # Ad history and scores
        self.ad_scores = defaultdict(float)  # Default score is 0.0
        self.recent_displays = []  # Track recent ad displays
        self.max_history_length = 50  # Maximum number of entries to keep
        
        # Load existing history if available
        self.load_display_history()
    
    def load_display_history(self):
        """Load ad display history from file if it exists"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    history_data = json.load(f)
                    
                    if 'recent_displays' in history_data:
                        self.recent_displays = history_data['recent_displays']
                        # Limit to max_history_length
                        if len(self.recent_displays) > self.max_history_length:
                            self.recent_displays = self.recent_displays[-self.max_history_length:]
                    
                    if 'ad_scores' in history_data:
                        self.ad_scores = defaultdict(float, history_data['ad_scores'])
                        
                logger.info(f"Loaded display history for {len(self.ad_scores)} ads")
        except Exception as e:
            logger.error(f"Error loading display history: {e}")
    
    def save_display_history(self):
        """Save ad display history to file"""
        try:
            # Create parent directory if it doesn't exist
            dir_path = os.path.dirname(os.path.abspath(self.history_file))
            os.makedirs(dir_path, exist_ok=True)
            
            history_data = {
                'recent_displays': self.recent_displays,
                'ad_scores': dict(self.ad_scores)  # Convert defaultdict to regular dict for JSON
            }
            
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
                
            logger.info(f"Saved display history with {len(self.recent_displays)} recent displays")
        except Exception as e:
            logger.error(f"Error saving display history: {e}")
    
    def get_latest_weather_data(self):
        """
        Read the latest data from the weather sensor file
        
        Returns:
            dict: Latest weather data entry or default values if unavailable
        """
        try:
            # Check if file exists
            if not os.path.exists(self.env_data_file):
                logger.error(f"Weather data file {self.env_data_file} not found")
                return None
                
            # File exists, try to read it
            with open(self.env_data_file, 'r') as f:
                data = json.load(f)
                
            if not data:
                logger.warning(f"Weather data file {self.env_data_file} is empty")
                return None
                
            # Get the latest entry (last in the list)
            latest_data = data[-1]  # Last entry in the list
            
            logger.info(f"Got latest weather data: Temp={latest_data.get('avg_dht_temp', 'N/A')}°C, "
                        f"Humidity={latest_data.get('avg_dht_humidity', 'N/A')}%")
            
            return latest_data
            
        except FileNotFoundError:
            logger.error(f"Weather data file {self.env_data_file} not found")
            return None
        except json.JSONDecodeError:
            logger.error(f"Error parsing weather data file {self.env_data_file}")
            return None
        except Exception as e:
            logger.error(f"Error reading weather data: {e}")
            return None
    
    def get_latest_audience_data(self):
        """
        Read the latest data from the engagement analyzer file
        
        Returns:
            dict: Latest audience data or default values if unavailable
        """
        try:
            # Check if file exists
            if not os.path.exists(self.audience_data_file):
                logger.error(f"Audience data file {self.audience_data_file} not found")
                return None
                
            # File exists, try to read it
            with open(self.audience_data_file, 'r') as f:
                data = json.load(f)
                
            if not data or not isinstance(data, dict):
                logger.warning(f"Audience data file {self.audience_data_file} is empty or invalid")
                return None
                
            # Extract audience information
            audience_present = False
            audience_count = data.get('count', 0)
            age_group = "all"
            gender = "both"
            emotion = "neutral"
            
            # Check if there are audience records
            audience_records = data.get('audience', [])
            if audience_records:
                audience_present = True
                
                # Get the most recent record
                latest_audience = audience_records[-1]
                
                # Extract attributes
                age_group = latest_audience.get('age', 'all')
                gender = latest_audience.get('gender', 'both')
                emotion = latest_audience.get('emotion', 'neutral')
                
                logger.info(f"Got latest audience data: Count={audience_count}, "
                           f"Age={age_group}, Gender={gender}, Emotion={emotion}")
            
            return {
                "audience_present": audience_present,
                "count": audience_count,
                "age_group": age_group,
                "gender": gender,
                "emotion": emotion,
                "timestamp": datetime.now().isoformat()
            }
            
        except FileNotFoundError:
            logger.error(f"Audience data file {self.audience_data_file} not found")
            return None
        except json.JSONDecodeError:
            logger.error(f"Error parsing audience data file {self.audience_data_file}")
            return None
        except Exception as e:
            logger.error(f"Error reading audience data: {e}")
            return None
    
    def get_environmental_context(self):
        """
        Create environmental context using real sensor data
        
        Returns:
            dict: Environmental context with categorized values
        """
        weather_data = self.get_latest_weather_data()
        
        if not weather_data:
            # Default values if no sensor data available
            logger.warning("Using default environmental context due to missing sensor data")
            return {
                "temperature": 25.0,
                "temperature_category": "moderate",
                "humidity": 60.0,
                "humidity_category": "medium",
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract and categorize environmental data
        temperature = weather_data.get('avg_dht_temp', 25.0)
        humidity = weather_data.get('avg_dht_humidity', 60.0)
        
        # Categorize temperature
        if temperature < 15:
            temp_category = "cold"
        elif temperature < 25:
            temp_category = "moderate"
        else:
            temp_category = "hot"
            
        # Categorize humidity
        if humidity < 40:
            humidity_category = "low"
        elif humidity < 70:
            humidity_category = "medium"
        else:
            humidity_category = "high"
        
        # Create environmental context
        env_context = {
            "temperature": temperature,
            "temperature_category": temp_category,
            "humidity": humidity,
            "humidity_category": humidity_category
        }
        
        # Add predicted weather if available
        if 'predicted_weather' in weather_data:
            env_context['predicted_weather'] = weather_data['predicted_weather']
            
        # Add timestamp
        env_context['timestamp'] = weather_data.get('timestamp', datetime.now().isoformat())
        
        return env_context
    
    def get_audience_context(self):
        """
        Create audience context using engagement analyzer data
        
        Returns:
            dict: Audience context with demographic information
        """
        audience_data = self.get_latest_audience_data()
        
        if not audience_data:
            # Default values if no audience data available
            logger.warning("Using default audience context due to missing data")
            return {
                "audience_present": False,
                "age_group": "all",
                "gender": "both",
                "group_size": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        return audience_data
    
    def calculate_demographic_relevance(self, ad, audience_context):
        """
        Calculate how relevant an ad is for the current audience demographics
        
        Args:
            ad (dict): Advertisement data
            audience_context (dict): Audience context data
            
        Returns:
            float: Relevance score (0.0-1.0)
        """
        if not audience_context.get("audience_present", False):
            return 1.0  # If no audience, all ads are equally relevant
        
        relevance = 1.0  # Start with perfect relevance
        
        # Age relevance
        if "age_group" in ad and ad["age_group"] not in ["all", "any"]:
            audience_age = audience_context.get("age_group", "all")
            if ad["age_group"] != audience_age and audience_age != "all":
                relevance *= 0.5  # Reduce relevance for age mismatch
        
        # Gender relevance
        if "gender" in ad and ad["gender"] not in ["both", "any", "all"]:
            audience_gender = audience_context.get("gender", "both")
            if ad["gender"] != audience_gender and audience_gender != "both":
                relevance *= 0.5  # Reduce relevance for gender mismatch
        
        # Special targeting based on emotion (optional enhancement)
        if "emotion" in audience_context:
            emotion = audience_context["emotion"].lower()
            ad_title = ad.get("title", "").lower()
            
            # Boost relevance for mood-appropriate ads
            if emotion == "happy" and any(keyword in ad_title for keyword in ["fun", "joy", "happy", "celebration"]):
                relevance *= 1.2
            elif emotion == "sad" and any(keyword in ad_title for keyword in ["comfort", "relax", "care"]):
                relevance *= 1.2
        
        return relevance
    
    def calculate_environmental_relevance(self, ad, env_context):
        """
        Calculate how relevant an ad is for current environmental conditions
        with strong emphasis on temperature matching
        
        Args:
            ad (dict): Advertisement data
            env_context (dict): Environmental context data
            
        Returns:
            float: Relevance score (0.0-1.0)
        """
        relevance = 1.0  # Start with perfect relevance
        
        # Temperature relevance - strict matching
        if "temperature" in ad and ad["temperature"] not in ["any"]:
            if ad["temperature"] != env_context["temperature_category"]:
                relevance *= 0.2  # More severely reduce relevance for temperature mismatch
        
        # Humidity relevance
        if "humidity" in ad and ad["humidity"] not in ["any"]:
            if ad["humidity"] != env_context["humidity_category"]:
                relevance *= 0.7  # Slightly reduce relevance for humidity mismatch
        
        # Weather condition relevance (optional enhancement)
        if "predicted_weather" in env_context and "weather_condition" in ad:
            weather = env_context["predicted_weather"].lower()
            ad_weather = ad["weather_condition"].lower()
            
            if weather != ad_weather and ad_weather != "any":
                relevance *= 0.5
        
        return relevance
    
    def update_ad_score(self, ad_id, display_timestamp=None):
        """
        Update the score of an ad after it's been displayed
        
        Args:
            ad_id (str): Advertisement ID
            display_timestamp (str, optional): Timestamp of the display
        """
        if not display_timestamp:
            display_timestamp = datetime.now().isoformat()
        
        # Record this display in recent history
        display_record = {
            "ad_id": ad_id,
            "timestamp": display_timestamp
        }
        self.recent_displays.append(display_record)
        
        # Trim history if needed
        if len(self.recent_displays) > self.max_history_length:
            self.recent_displays = self.recent_displays[-self.max_history_length:]
        
        # Increment this ad's score
        self.ad_scores[ad_id] += 1.0
        
        # Decay all scores slightly (older displays matter less)
        for ad in self.ad_scores:
            if ad != ad_id:  # Don't decay the ad we just incremented
                self.ad_scores[ad] = max(0, self.ad_scores[ad] - 0.05)
        
        # Save the updated history
        self.save_display_history()
    
    def select_optimal_content(self):
        """
        Select the optimal advertisement based on score-based selection
        with priority given to weather-matching ads and then audience when present
        
        Returns:
            dict: The selected advertisement
        """
        # Get current contexts
        env_context = self.get_environmental_context()
        audience_context = self.get_audience_context()
        
        audience_present = audience_context.get('audience_present', False)
        
        logger.info(f"Current context - Temperature: {env_context['temperature_category']}, "
                   f"Humidity: {env_context['humidity_category']}, "
                   f"Audience: {audience_context['age_group'] if audience_present else 'None'}")
        
        # Get all ads from repository
        all_ads = self.content_repository.get_all_ads()
        
        if not all_ads:
            logger.warning("No advertisements available")
            return None
            
        # First, filter ads by temperature match
        temp_matching_ads = []
        other_ads = []
        
        current_temp = env_context['temperature_category']
        
        for ad in all_ads:
            # Check if ad has a specific temperature and if it matches current temperature
            if "temperature" in ad and ad["temperature"] not in ["any"]:
                if ad["temperature"] == current_temp:
                    temp_matching_ads.append(ad)
                else:
                    other_ads.append(ad)
            else:
                # If ad doesn't specify temperature, consider it for any temperature
                temp_matching_ads.append(ad)
        
        logger.info(f"Found {len(temp_matching_ads)} ads matching current temperature ({current_temp})")
        
        # If we don't have any temperature-matching ads, fall back to all ads
        candidate_ads = temp_matching_ads if temp_matching_ads else all_ads
        
        # Calculate scores for each candidate ad
        scored_ads = []
        for ad in candidate_ads:
            ad_id = ad["ad_id"]
            
            # Base score is the negative of current score (so lower scores are better)
            base_score = -self.ad_scores.get(ad_id, 0)
            
            # Adjust score based on demographic relevance - more important when audience present
            demographic_relevance = self.calculate_demographic_relevance(ad, audience_context)
            
            # Adjust score based on environmental relevance
            environmental_relevance = self.calculate_environmental_relevance(ad, env_context)
            
            # Combined score (higher is better)
            # When audience is present: 40% history, 40% demographic, 20% environmental
            # When no audience: 50% history, 10% demographic, 40% environmental
            if audience_present:
                combined_score = (0.4 * base_score) + (0.4 * demographic_relevance) + (0.2 * environmental_relevance)
            else:
                combined_score = (0.5 * base_score) + (0.1 * demographic_relevance) + (0.4 * environmental_relevance)
            
            scored_ads.append({
                "ad": ad,
                "score": combined_score,
                "history_score": base_score,
                "demographic_relevance": demographic_relevance,
                "environmental_relevance": environmental_relevance
            })
            
            logger.debug(f"Ad {ad_id} ({ad['title']}) - Score: {combined_score:.2f} "
                        f"(History: {base_score:.2f}, Demo: {demographic_relevance:.2f}, Env: {environmental_relevance:.2f})")
        
        # Sort by score (highest first)
        scored_ads.sort(key=lambda x: x["score"], reverse=True)
        
        # Get the top 3 ads to choose from (or fewer if we have less than 3)
        top_count = min(3, len(scored_ads))
        top_ads = scored_ads[:top_count]
        
        if top_count == 0:
            logger.warning("No suitable ads found after filtering")
            # Fall back to all ads if we filtered too aggressively
            return self.select_random_ad()
        
        # Select one of the top ads with weighted probability
        weights = [max(0.1, ad["score"] + 2) for ad in top_ads]  # Ensure positive weights
        selected_index = random.choices(range(top_count), weights=weights, k=1)[0]
        selected = top_ads[selected_index]
        
        # Update this ad's score
        self.update_ad_score(selected["ad"]["ad_id"])
        
        logger.info(f"Selected ad: {selected['ad']['title']} (ID: {selected['ad']['ad_id']}), "
                   f"Score: {selected['score']:.2f}")
        logger.info(f"Selection factors - History: {selected['history_score']:.2f}, "
                   f"Demographic: {selected['demographic_relevance']:.2f}, "
                   f"Environmental: {selected['environmental_relevance']:.2f}")
        
        return selected["ad"]
        
    def select_random_ad(self):
        """Fallback method to select a random ad when filtering is too restrictive"""
        all_ads = self.content_repository.get_all_ads()
        if not all_ads:
            return None
            
        # Exclude recently shown ads if possible
        recent_ad_ids = [record["ad_id"] for record in self.recent_displays[-5:]] if self.recent_displays else []
        fresh_ads = [ad for ad in all_ads if ad["ad_id"] not in recent_ad_ids]
        
        # Use fresh ads if available, otherwise use all ads
        candidate_ads = fresh_ads if fresh_ads else all_ads
        
        # Select a random ad
        selected_ad = random.choice(candidate_ads)
        
        # Update this ad's score
        self.update_ad_score(selected_ad["ad_id"])
        
        logger.info(f"Randomly selected ad: {selected_ad['title']} (ID: {selected_ad['ad_id']})")
        
        return selected_ad