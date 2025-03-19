"""
This file simulates the audience analysis that would normally come from camera feed
"""

import random
from mock_data import map_age_group, map_gender

class AudienceAnalyzer:
    """
    Simulates the demographic analysis component of the system
    In a real system, this would use computer vision to analyze camera feeds
    """
    
    def __init__(self):
        # Normally would initialize camera connection and ML models here
        pass
    
    def analyze_frame(self, frame_data=None):
        """
        Analyze camera frame to extract audience characteristics
        
        Args:
            frame_data (bytes, optional): Raw camera frame data
            
        Returns:
            dict: Audience profile with demographic information
        """
        # In a real system, this would use ML to analyze a camera frame
        # For simulation, we'll return random but plausible values
        
        # Simulate number of people detected
        group_size = random.randint(0, 8)
        
        if group_size == 0:
            # No audience detected
            return {
                "estimated_age_group": "none",
                "gender_distribution": "none",
                "group_size": 0,
                "attention_span": 0,
                "audience_present": False
            }
            
        # Simulate audience characteristics when people are present
        age_groups = ["children", "teenager", "adult", "elderly"]
        age_weights = [0.1, 0.3, 0.5, 0.1]  # Distribution of age groups
        dominant_age = random.choices(age_groups, weights=age_weights, k=1)[0]
        
        # Simulate gender distribution
        gender_options = ["mostly_male", "mostly_female", "mixed"]
        gender_weights = [0.4, 0.4, 0.2]
        gender_distribution = random.choices(gender_options, weights=gender_weights, k=1)[0]
        
        # Simulate average attention time (1-15 seconds)
        attention_span = random.uniform(1, 15)
        
        # Create audience profile
        audience_profile = {
            "estimated_age_group": dominant_age,
            "gender_distribution": gender_distribution,
            "group_size": group_size,
            "attention_span": attention_span,
            "audience_present": True
        }
        
        return audience_profile
    
    def simulate_audience(self, scenario=None):
        """
        Simulate an audience detection (for testing without camera)
        
        Args:
            scenario (dict, optional): Predefined audience scenario
            
        Returns:
            dict: Simulated audience profile
        """
        if scenario:
            # Use the provided scenario
            return {
                "estimated_age_group": map_age_group(scenario["estimated_age_group"]),
                "gender_distribution": map_gender(scenario["gender_distribution"]),
                "group_size": scenario["group_size"],
                "attention_span": scenario["attention_span"],
                "audience_present": scenario["group_size"] > 0
            }
        else:
            # Generate a random profile
            return self.analyze_frame()