"""
This file implements the core Content Decision Engine
"""

import json
import random
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DecisionEngine")

class ContentDecisionEngine:
    """
    The core decision engine that selects the optimal advertisement
    based on environmental conditions and audience demographics
    """
    
    def __init__(self, content_repository, rules_file=None):
        """
        Initialize the decision engine
        
        Args:
            content_repository: Repository for accessing ad content
            rules_file (str, optional): Path to JSON rules file
        """
        self.content_repository = content_repository
        self.rules = self._load_rules(rules_file)
        self.recent_selections = []  # Track recent selections to avoid repetition
        self.performance_log = []    # Track ad performance for learning
        
    def _load_rules(self, rules_file):
        """
        Load decision rules from a JSON file
        
        Args:
            rules_file (str): Path to JSON rules file
            
        Returns:
            list: Loaded rules or default rules if file not found
        """
        if rules_file:
            try:
                with open(rules_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load rules from {rules_file}: {e}")
                logger.info("Using default rules")
                
        # Default rules if no file provided or loading failed
        return [
            {
                "id": "rule_001",
                "name": "Hot Weather - Cold Drinks",
                "priority": 5,
                "conditions": {
                    "temperature": "hot",
                    "audience_age": ["all", "teenager", "adult"]
                },
                "weight": 1.0
            },
            {
                "id": "rule_002",
                "name": "Rainy Weather - Umbrellas",
                "priority": 8,
                "conditions": {
                    "weather": "rainy",
                    "audience_age": ["all", "adult", "elderly"]
                },
                "weight": 1.0
            },
            {
                "id": "rule_003",
                "name": "Kids Present - Child-Friendly Ads",
                "priority": 7,
                "conditions": {
                    "audience_age": ["children"]
                },
                "weight": 1.0
            }
        ]
        
    def calculate_ad_score(self, ad, weather_context, audience_profile):
        """
        Calculate a score for each advertisement based on current conditions
        
        Args:
            ad (dict): Advertisement data
            weather_context (dict): Current environmental conditions
            audience_profile (dict): Current audience demographics
            
        Returns:
            float: Score representing how well the ad matches current conditions
        """
        score = 0.0
        
        # Base score components
        weather_score = 0.0
        audience_score = 0.0
        novelty_score = 0.0
        
        # 1. Weather matching score (0-40 points)
        # Temperature match
        if "temperature_category" in weather_context and "temperature" in ad:
            if weather_context["temperature_category"] == ad["temperature"]:
                weather_score += 20
            elif (weather_context["temperature_category"] == "moderate" and 
                  ad["temperature"] in ["hot", "cold"]):
                weather_score += 5  # Partial match
                
        # Humidity match
        if "humidity_category" in weather_context and "humidity" in ad:
            if weather_context["humidity_category"] == ad["humidity"]:
                weather_score += 20
            elif weather_context["humidity_category"] == "medium" and ad["humidity"] in ["high", "low"]:
                weather_score += 10  # Partial match
                
        # 2. Audience matching score (0-40 points)
        if audience_profile.get("audience_present", False):
            # Age group match
            if "estimated_age_group" in audience_profile and "age_group" in ad:
                audience_age = map_age_group(audience_profile["estimated_age_group"])
                ad_age = map_age_group(ad["age_group"])
                
                if ad_age == "all" or audience_age == ad_age:
                    audience_score += 20
                    
            # Gender match
            if "gender_distribution" in audience_profile and "gender" in ad:
                audience_gender = audience_profile["gender_distribution"]
                ad_gender = ad["gender"]
                
                if ad_gender == "both":
                    audience_score += 20  # "both" matches any audience
                elif (audience_gender == "mostly_male" and ad_gender == "male") or \
                     (audience_gender == "mostly_female" and ad_gender == "female"):
                    audience_score += 20
                elif audience_gender == "mixed":
                    audience_score += 15  # Mixed audience gets partial match for targeted ads
                
        else:
            # No audience detected, prioritize general ads
            if "age_group" in ad and ad["age_group"] == "all":
                audience_score += 30
            if "gender" in ad and ad["gender"] == "both":
                audience_score += 10
        
        # 3. Novelty score (0-20 points)
        # Check if ad was recently shown
        if ad["ad_id"] in [recent["ad_id"] for recent in self.recent_selections[-5:]]:
            novelty_score = 0  # Ad was very recently shown
        elif ad["ad_id"] in [recent["ad_id"] for recent in self.recent_selections[-10:-5]]:
            novelty_score = 10  # Ad was shown a bit ago
        else:
            novelty_score = 20  # Ad hasn't been shown recently
            
        # 4. Apply rule-based adjustments
        rule_multiplier = 1.0
        for rule in self.rules:
            rule_match = True
            
            # Check all rule conditions
            for condition_key, condition_value in rule["conditions"].items():
                if condition_key == "temperature" and "temperature_category" in weather_context:
                    if weather_context["temperature_category"] != condition_value:
                        rule_match = False
                        break
                elif condition_key == "weather" and "weather" in weather_context:
                    if weather_context["weather"] != condition_value:
                        rule_match = False
                        break
                elif condition_key == "audience_age" and "estimated_age_group" in audience_profile:
                    audience_age = map_age_group(audience_profile["estimated_age_group"])
                    if isinstance(condition_value, list):
                        if audience_age not in condition_value and "all" not in condition_value:
                            rule_match = False
                            break
                    elif audience_age != condition_value and condition_value != "all":
                        rule_match = False
                        break
            
            # Apply rule weight and priority if matched
            if rule_match:
                rule_multiplier = max(rule_multiplier, rule["weight"] * (rule["priority"] / 5))
        
        # Calculate final score
        # Weights: 40% weather, 40% audience, 20% novelty
        base_score = (0.4 * weather_score) + (0.4 * audience_score) + (0.2 * novelty_score)
        final_score = base_score * rule_multiplier
        
        logger.debug(f"Scored ad '{ad['title']}': {final_score} (W:{weather_score} A:{audience_score} N:{novelty_score} R:{rule_multiplier})")
        
        # Store these scores for displaying in selection feedback
        ad['_score_details'] = {
            'weather_score': weather_score,
            'audience_score': audience_score,
            'novelty_score': novelty_score,
            'rule_multiplier': rule_multiplier
        }
        
        return final_score
    
    def select_optimal_content(self, weather_context, audience_profile):
        """
        Select the optimal advertisement based on current conditions
        
        Args:
            weather_context (dict): Current environmental conditions
            audience_profile (dict): Current audience demographics
            
        Returns:
            dict: The selected advertisement with score information
        """
        # Get all potentially matching ads
        matching_ads = self.content_repository.get_matching_ads(weather_context, audience_profile)
        
        # If no specific matches, get all ads
        if not matching_ads:
            matching_ads = self.content_repository.get_all_ads()
            logger.info("No specific matches found, considering all ads")
        
        # Calculate scores for each ad
        scored_ads = []
        for ad in matching_ads:
            score = self.calculate_ad_score(ad, weather_context, audience_profile)
            scored_ads.append({
                "ad": ad,
                "score": score
            })
            
        # Sort by score (highest first)
        scored_ads.sort(key=lambda x: x["score"], reverse=True)
        
        # Select the highest scoring ad
        if scored_ads:
            selected = scored_ads[0]
            
            # Record this selection
            selection_record = {
                "timestamp": datetime.now().isoformat(),
                "ad_id": selected["ad"]["ad_id"],
                "title": selected["ad"]["title"],
                "score": selected["score"],
                "weather_context": weather_context,
                "audience_profile": audience_profile
            }
            
            # Update recent selections
            self.recent_selections.append(selection_record)
            if len(self.recent_selections) > 20:  # Keep only most recent 20
                self.recent_selections.pop(0)
                
            logger.info(f"Selected ad: {selected['ad']['title']} (Score: {selected['score']:.2f})")
            if '_score_details' in selected['ad']:
                details = selected['ad']['_score_details']
                logger.info(f"Selection factors - Weather: {details['weather_score']:.1f}, Audience: {details['audience_score']:.1f}, Novelty: {details['novelty_score']:.1f}, Rule multiplier: {details['rule_multiplier']:.1f}x")
            
            # Return full ad data with score
            return {
                "ad": selected["ad"],
                "score": selected["score"],
                "alternatives": [{"ad_id": a["ad"]["ad_id"], "title": a["ad"]["title"], "score": a["score"]} 
                                for a in scored_ads[1:3]]  # Also include top 2 alternatives
            }
        else:
            logger.warning("No suitable advertisements found")
            return None
            
    def record_performance(self, ad_id, metrics):
        """
        Record performance metrics for a displayed advertisement
        
        Args:
            ad_id (str): ID of the displayed advertisement
            metrics (dict): Performance metrics (attention_time, audience_size_change, etc.)
        """
        if not self.recent_selections:
            logger.warning(f"Can't record performance for ad {ad_id} - no recent selections")
            return
            
        # Find this ad in recent selections
        for selection in reversed(self.recent_selections):
            if selection["ad_id"] == ad_id:
                # Record performance
                performance_record = {
                    "timestamp": datetime.now().isoformat(),
                    "ad_id": ad_id,
                    "score_at_selection": selection["score"],
                    "metrics": metrics,
                    "weather_context": selection.get("weather_context", {}),
                    "audience_profile": selection.get("audience_profile", {})
                }
                
                self.performance_log.append(performance_record)
                logger.info(f"Recorded performance for ad {ad_id}: {metrics}")
                
                # In a real system, this would be used to update ML models or rules
                return
                
        logger.warning(f"Ad {ad_id} not found in recent selections")
    
    def update_rules(self, performance_data=None):
        """
        Update decision rules based on performance data
        
        Args:
            performance_data (list, optional): External performance data to incorporate
        """
        # In a real system, this would analyze past performance and adjust rules
        # For this simulation, we'll just log that it happened
        data_source = performance_data if performance_data else self.performance_log
        logger.info(f"Updating rules based on {len(data_source)} performance records")
        
        # Here you would implement ML to adjust rule weights and priorities
        # For simulation, we'll just make small random adjustments
        for rule in self.rules:
            # Small random adjustment to weight (±10%)
            adjustment = random.uniform(-0.1, 0.1)
            rule["weight"] = max(0.5, min(2.0, rule["weight"] + adjustment))
            logger.debug(f"Adjusted rule {rule['id']} weight to {rule['weight']:.2f}")