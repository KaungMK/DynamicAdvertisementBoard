"""
Enhanced Decision Engine with integration for new sensor data formats
and support for checking JSON files every 5 seconds
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
        
        # Cache for sensor data
        self.cached_env_data = None
        self.cached_audience_data = None
        
        # Track file modification times for watchdog functionality
        self.env_file_last_modified = 0
        self.audience_file_last_modified = 0
        
        # Track last file check time for periodic updates
        self.last_env_check_time = 0
        self.last_audience_check_time = 0
        
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
    
    def check_env_file_updated(self):
        """
        Check if the environment data file has been modified since the last check
        
        Returns:
            bool: True if file has been modified, False otherwise
        """
        try:
            # If file doesn't exist, return False
            if not os.path.exists(self.env_data_file):
                return False
                
            # Get the current modification time
            current_mtime = os.path.getmtime(self.env_data_file)
            
            # Check if the file has been modified
            if current_mtime > self.env_file_last_modified:
                # Update the last modified time
                self.env_file_last_modified = current_mtime
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking environment file: {e}")
            return False
            
    def check_audience_file_updated(self):
        """
        Check if the audience data file has been modified since the last check
        
        Returns:
            bool: True if file has been modified, False otherwise
        """
        try:
            # If file doesn't exist, return False
            if not os.path.exists(self.audience_data_file):
                return False
                
            # Get the current modification time
            current_mtime = os.path.getmtime(self.audience_data_file)
            
            # Check if the file has been modified
            if current_mtime > self.audience_file_last_modified:
                # Update the last modified time
                self.audience_file_last_modified = current_mtime
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking audience file: {e}")
            return False
            
    def get_latest_weather_data(self, skip_check=False):
        """
        Read the latest data from the weather sensor file
        
        Args:
            skip_check (bool): If True, skip checking if file has been modified
                            and always read the file
        
        Returns:
            dict: Latest weather data entry or default values if unavailable
        """
        try:
            # Check if file exists
            if not os.path.exists(self.env_data_file):
                logger.error(f"Weather data file {self.env_data_file} not found")
                return None
            
            # Always read the file when skip_check is True, ignoring cache completely
            if skip_check:
                # Force setting the last modified time to 0 to ensure check_env_file_updated returns True next time
                self.env_file_last_modified = 0
                self.cached_env_data = None
                logger.debug("Force reading weather data due to skip_check=True")
                
            # Check if we need to read the file or can use cached data
            if not skip_check and self.cached_env_data and not self.check_env_file_updated():
                logger.debug("Using cached weather data since file hasn't changed")
                return self.cached_env_data
                
            # File exists and has changed (or skip_check is True), try to read it
            with open(self.env_data_file, 'r') as f:
                data = json.load(f)
                
            if not data:
                logger.warning(f"Weather data file {self.env_data_file} is empty")
                return None
                
            # Get the latest entry (last in the list)
            latest_data = data[-1]  # Last entry in the list
            
            logger.info(f"Got latest weather data: Temp={latest_data.get('avg_dht_temp', 'N/A')}°C, "
                        f"Humidity={latest_data.get('avg_dht_humidity', 'N/A')}%")
            
            # Cache the data for next time
            self.cached_env_data = latest_data
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
    
    def get_latest_audience_data(self, skip_check=False):
        """
        Read the latest data from the engagement analyzer file
        
        Args:
            skip_check (bool): If True, skip checking if file has been modified
                              and always read the file
        
        Returns:
            dict: Latest audience data or default values if unavailable
        """
        try:
            # Check if file exists
            if not os.path.exists(self.audience_data_file):
                logger.error(f"Audience data file {self.audience_data_file} not found")
                return None
            
            # Always read the file when skip_check is True, ignoring cache completely
            if skip_check:
                # Force setting the last modified time to 0 to ensure check_audience_file_updated returns True next time
                self.audience_file_last_modified = 0
                self.cached_audience_data = None
                logger.debug("Force reading audience data due to skip_check=True")
            elif self.cached_audience_data and not self.check_audience_file_updated():
                logger.debug("Using cached audience data since file hasn't changed")
                return self.cached_audience_data
                
            # File exists and has changed (or skip_check is True), try to read it
            with open(self.audience_data_file, 'r') as f:
                data = json.load(f)
                
            if not data or not isinstance(data, dict):
                logger.warning(f"Audience data file {self.audience_data_file} is empty or invalid")
                return None
                
            # Extract audience information
            audience_count = data.get('count', 0)
            age_group = "all"
            gender = "both"
            emotion = "neutral"
            group_size = 0
            
            # Check if audience_present key exists directly in the data
            audience_present = data.get('audience_present', False)
            
            # If current_audience key exists, use that for real-time audience data
            if audience_present and 'current_audience' in data:
                current = data['current_audience']
                group_size = current.get('count', 1)
                
                # Map age value to an age group category
                age_value = current.get('age', 30)
                if age_value < 18:
                    age_group = "youth"
                elif age_value < 35:
                    age_group = "young_adult"
                elif age_value < 55:
                    age_group = "adult"
                else:
                    age_group = "senior"
                    
                # Handle gender format (in your JSON it's 'M' or 'F')
                gender_code = current.get('gender', '')
                if gender_code == 'M':
                    gender = "male"
                elif gender_code == 'F':
                    gender = "female"
                else:
                    gender = "both"
                    
                # Handle emotion with proper capitalization
                emotion = current.get('emotion', 'neutral')
                if emotion:
                    emotion = emotion.lower()
                
                logger.info(f"Got current audience data: Present={audience_present}, Count={group_size}, "
                           f"Age Group={age_group}, Gender={gender}, Emotion={emotion}")
            else:
                # No current audience
                logger.info("No active audience currently detected")
                
            # Use current timestamp 
            timestamp = datetime.now().isoformat()
            
            audience_data = {
                "audience_present": audience_present,
                "count": audience_count,
                "group_size": group_size,
                "age_group": age_group,
                "gender": gender,
                "emotion": emotion,
                "timestamp": timestamp
            }
            
            # Cache the data for next time
            self.cached_audience_data = audience_data
            return audience_data
            
        except FileNotFoundError:
            logger.error(f"Audience data file {self.audience_data_file} not found")
            return None
        except json.JSONDecodeError:
            logger.error(f"Error parsing audience data file {self.audience_data_file}")
            return None
        except Exception as e:
            logger.error(f"Error reading audience data: {e}")
            return None
    
    def get_environmental_context(self, skip_check=False):
        """
        Create environmental context using real sensor data
        
        Args:
            skip_check (bool): If True, force read the file even if it hasn't changed
        
        Returns:
            dict: Environmental context with categorized values
        """
        weather_data = self.get_latest_weather_data(skip_check=skip_check)
        
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
    
    def get_audience_context(self, skip_check=False):
        """
        Create audience context using engagement analyzer data
        
        Args:
            skip_check (bool): If True, force read the file even if it hasn't changed
        
        Returns:
            dict: Audience context with demographic information
        """
        audience_data = self.get_latest_audience_data(skip_check=skip_check)
        
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
        Calculate demographic relevance with extreme emphasis on correct matching
        """
        if not audience_context.get("audience_present", False):
            return 1.0  # No audience present
        
        base_relevance = 1.0
        
        # Get audience attributes
        audience_gender = audience_context.get("gender", "both")
        audience_age = audience_context.get("age_group", "all")
        
        # Get ad targeting
        ad_gender = ad.get("gender", "both")
        ad_age = ad.get("age_group", "all")
        
        # GENDER MATCHING - Critical
        if ad_gender not in ["both", "any", "all"]:
            if ad_gender != audience_gender:
                # Severe penalty for wrong gender
                base_relevance *= 0.1
        
        # AGE MATCHING - Very important
        if ad_age not in ["all", "any"]:
            if ad_age != audience_age:
                # Strong penalty for wrong age group
                base_relevance *= 0.2
        
        # Extra boost for perfect matches
        if (ad_gender == audience_gender or ad_gender in ["both", "any", "all"]) and \
        (ad_age == audience_age or ad_age in ["all", "any"]):
            base_relevance *= 2.0
        
        return base_relevance
    
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
    
    def select_optimal_content(self, force_update=False):
        """
        Select the optimal advertisement based on strict demographic filtering
        """
        # Get current contexts
        env_context = self.get_environmental_context(skip_check=force_update)
        audience_context = self.get_audience_context(skip_check=force_update)
        
        audience_present = audience_context.get('audience_present', False)
        audience_age_group = audience_context.get('age_group', 'all')
        audience_gender = audience_context.get('gender', 'both')
        
        logger.info(f"Current context - Audience present: {audience_present}, "
                    f"Age group: {audience_age_group}, Gender: {audience_gender}, "
                    f"Temperature: {env_context['temperature_category']}")
        
        # Get all ads from repository
        all_ads = self.content_repository.get_all_ads()
        
        if not all_ads:
            logger.warning("No advertisements available")
            return None
        
        # If audience is present, strictly filter by demographics
        if audience_present:
            # STEP 1: First filter by both gender and age
            perfect_match_ads = []
            
            for ad in all_ads:
                ad_gender = ad.get("gender", "both")
                ad_age = ad.get("age_group", "all")
                
                # Check for perfect demographic match
                gender_match = (ad_gender == audience_gender or ad_gender in ["both", "any", "all"])
                age_match = (ad_age == audience_age_group or ad_age in ["all", "any"])
                
                if gender_match and age_match:
                    perfect_match_ads.append(ad)
            
            # Log what we found
            logger.info(f"Found {len(perfect_match_ads)} ads matching both gender '{audience_gender}' and age '{audience_age_group}'")
            
            # STEP 2: If no perfect matches, try gender match with any age
            if not perfect_match_ads:
                gender_match_ads = []
                
                for ad in all_ads:
                    ad_gender = ad.get("gender", "both")
                    
                    if ad_gender == audience_gender or ad_gender in ["both", "any", "all"]:
                        gender_match_ads.append(ad)
                
                logger.info(f"Found {len(gender_match_ads)} ads matching gender '{audience_gender}' with any age")
                
                # If we have gender matches, use those
                if gender_match_ads:
                    perfect_match_ads = gender_match_ads
            
            # STEP 3: If we have audience-matched ads, use only those
            if perfect_match_ads:
                candidate_ads = perfect_match_ads
            else:
                # Fall back to all ads if no matches
                candidate_ads = all_ads
                logger.warning("No demographic matches found, using all ads")
        else:
            # No audience, filter by temperature
            temp_matching_ads = []
            
            current_temp = env_context['temperature_category']
            
            for ad in all_ads:
                ad_temp = ad.get("temperature", "any")
                if ad_temp == current_temp or ad_temp in ["any"]:
                    temp_matching_ads.append(ad)
            
            # Use temperature-matched ads or all ads
            candidate_ads = temp_matching_ads if temp_matching_ads else all_ads
            logger.info(f"Found {len(candidate_ads)} ads matching temperature '{current_temp}'")
        
        # Calculate scores for remaining candidate ads
        scored_ads = []
        for ad in candidate_ads:
            ad_id = ad["ad_id"]
            
            # Log ad details for debugging
            logger.info(f"Considering ad {ad_id} ({ad.get('title', 'Unknown')}), "
                        f"Gender: {ad.get('gender', 'any')}, Age: {ad.get('age_group', 'any')}")
            
            # Base score from history
            base_score = -self.ad_scores.get(ad_id, 0)
            
            # Audience relevance
            demographic_relevance = self.calculate_demographic_relevance(ad, audience_context)
            
            # Environmental relevance
            environmental_relevance = self.calculate_environmental_relevance(ad, env_context)
            
            # Final score calculation
            if audience_present:
                # When audience is present, demographics are most important
                combined_score = (0.2 * base_score) + (0.7 * demographic_relevance) + (0.1 * environmental_relevance)
            else:
                # When no audience, temperature is most important
                combined_score = (0.3 * base_score) + (0.1 * demographic_relevance) + (0.6 * environmental_relevance)
            
            scored_ads.append({
                "ad": ad,
                "score": combined_score,
                "demographic_relevance": demographic_relevance,
                "environmental_relevance": environmental_relevance
            })
        
        # Sort by score (highest first)
        scored_ads.sort(key=lambda x: x["score"], reverse=True)
        
        # If we have candidates, choose from top 3
        if scored_ads:
            top_count = min(3, len(scored_ads))
            top_ads = scored_ads[:top_count]
            
            # For each top ad, show its details for debugging
            for i, ad_data in enumerate(top_ads):
                ad = ad_data["ad"]
                logger.info(f"Top {i+1}: {ad.get('title', 'Unknown')} - "
                            f"Gender: {ad.get('gender', 'any')}, Age: {ad.get('age_group', 'any')}, "
                            f"Score: {ad_data['score']:.2f}")
            
            # Select with weighted probability
            weights = [max(0.1, ad["score"] + 2) for ad in top_ads]
            selected_index = random.choices(range(top_count), weights=weights, k=1)[0]
            selected = top_ads[selected_index]
            
            # Update ad score
            self.update_ad_score(selected["ad"]["ad_id"])
            
            return selected["ad"]
        else:
            # Fall back to random ad
            return self.select_random_ad()
        
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