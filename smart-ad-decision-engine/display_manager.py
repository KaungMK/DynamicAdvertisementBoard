"""
This file simulates the display output of the system
"""

import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DisplayManager")

class DisplayManager:
    """
    Simulates the display output of advertisements
    In a real system, this would control a physical display
    """
    
    def __init__(self):
        """Initialize the display manager"""
        self.current_ad = None
        self.display_started = None
        self.current_audience = None  # Will store audience profile data
        
    def display_ad(self, ad):
        """
        Display an advertisement
        
        Args:
            ad (dict): Advertisement data to display
        """
        # In a real system, this would communicate with a display device
        # For simulation, we'll just log the display
        
        self.current_ad = ad
        self.display_started = time.time()
        
        # Print a simulation of the display
        print("\n" + "="*50)
        print(f"DISPLAYING ADVERTISEMENT: {ad['title'].upper()}")
        print("="*50)
        print(f"ID: {ad['ad_id']}")
        print(f"Target Demographics: {ad['age_group']} / {ad['gender']}")
        print(f"Optimal Conditions: {ad['temperature']} temperature, {ad['humidity']} humidity")
        print(f"Image URL: {ad['image_url']}")
        print("="*50 + "\n")
        
        logger.info(f"Now displaying: {ad['title']} (ID: {ad['ad_id']})")
        
    def stop_display(self):
        """
        Stop displaying the current advertisement
        
        Returns:
            dict: Display metrics for the completed advertisement
        """
        if not self.current_ad or not self.display_started:
            logger.warning("No active display to stop")
            return None
            
        # Calculate display duration
        display_duration = time.time() - self.display_started
        
        # Generate realistic metrics for simulation using audience data when available
        import random
        from mock_data import map_age_group, map_gender
        
        # Use actual audience size if available, otherwise generate random
        if self.current_audience and self.current_audience.get('audience_present', False):
            estimated_viewers = self.current_audience.get('group_size', random.randint(1, 8))
        else:
            # Simulate estimated viewers based on ad characteristics
            base_viewers = random.randint(1, 8)
            if self.current_ad.get('age_group') == 'all' and self.current_ad.get('gender') == 'both':
                viewer_multiplier = 1.5
            else:
                viewer_multiplier = 1.0
            estimated_viewers = round(base_viewers * viewer_multiplier)
        
        # Calculate audience match score for more realistic attention time
        audience_match_score = 0.5  # Default middle value
        
        if self.current_audience and self.current_audience.get('audience_present', False):
            # Match ad target audience with actual audience
            ad_age = map_age_group(self.current_ad.get('age_group', 'all'))
            actual_age = map_age_group(self.current_audience.get('estimated_age_group', 'none'))
            
            ad_gender = map_gender(self.current_ad.get('gender', 'both'))
            actual_gender = map_gender(self.current_audience.get('gender_distribution', 'none'))
            
            # Calculate match score based on demographics
            if ad_age == 'all' or actual_age == 'all' or ad_age == actual_age:
                age_match = 1.0
            else:
                age_match = 0.3
                
            if ad_gender == 'both' or actual_gender == 'both' or ad_gender == actual_gender:
                gender_match = 1.0
            else:
                gender_match = 0.4
                
            audience_match_score = (age_match + gender_match) / 2
            
            # Use actual attention span if available
            if 'attention_span' in self.current_audience:
                attention_time = min(self.current_audience['attention_span'] * audience_match_score, display_duration)
            else:
                base_attention_percent = random.uniform(0.3, 0.8) * audience_match_score
                attention_time = display_duration * base_attention_percent
        else:
            # No audience data, use simple simulation
            base_attention_percent = random.uniform(0.3, 0.8)
            attention_time = display_duration * base_attention_percent
        
        metrics = {
            "display_duration": display_duration,
            "estimated_viewers": estimated_viewers,
            "attention_time": round(attention_time, 1)
        }
        
        logger.info(f"Stopped displaying {self.current_ad['title']} after {display_duration:.1f} seconds")
        logger.info(f"Performance metrics: {estimated_viewers} viewers with {attention_time:.1f}s average attention")
        
        # Reset current display
        ad_id = self.current_ad['ad_id'] 
        self.current_ad = None
        self.display_started = None
        
        return {
            "ad_id": ad_id,
            "metrics": metrics
        }
        
    def is_displaying(self):
        """Check if an advertisement is currently being displayed"""
        return self.current_ad is not None
        
    def get_current_ad(self):
        """Get the currently displayed advertisement"""
        return self.current_ad