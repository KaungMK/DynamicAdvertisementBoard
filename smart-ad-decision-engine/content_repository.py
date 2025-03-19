"""
This file simulates the content repository that would store and retrieve advertisements
"""

from mock_data import ADS, map_age_group, map_gender

class ContentRepository:
    """
    Simulates the content repository component of the system
    In a real system, this would connect to DynamoDB or another database
    """
    
    def __init__(self, ads_data=None):
        """
        Initialize the content repository
        
        Args:
            ads_data (list, optional): List of advertisement data to use
        """
        # Use provided ads or default to mock data
        self.ads = ads_data if ads_data is not None else ADS
        
    def get_all_ads(self):
        """
        Get all available advertisements
        
        Returns:
            list: All advertisement data
        """
        return self.ads
    
    def get_ad_by_id(self, ad_id):
        """
        Get a specific advertisement by ID
        
        Args:
            ad_id (str): The ID of the advertisement to retrieve
            
        Returns:
            dict: Advertisement data or None if not found
        """
        for ad in self.ads:
            if ad["ad_id"] == ad_id:
                return ad
        return None
    
    def filter_ads(self, criteria):
        """
        Filter advertisements based on specified criteria
        
        Args:
            criteria (dict): Filter conditions for ads
            
        Returns:
            list: Filtered advertisement data
        """
        filtered_ads = []
        
        for ad in self.ads:
            match = True
            
            # Check each criterion
            for key, value in criteria.items():
                if key in ad:
                    # Special handling for age group and gender to use standardized forms
                    if key == "age_group":
                        if map_age_group(ad[key]) != map_age_group(value):
                            if ad[key] != "all" and value != "all":  # "all" matches any age group
                                match = False
                                break
                    elif key == "gender":
                        if map_gender(ad[key]) != map_gender(value):
                            if ad[key] != "both" and value != "both":  # "both" matches any gender
                                match = False
                                break
                    elif ad[key] != value:
                        match = False
                        break
            
            if match:
                filtered_ads.append(ad)
                
        return filtered_ads
    
    def get_matching_ads(self, weather_context, audience_profile):
        """
        Get ads that match current environmental and audience conditions
        
        Args:
            weather_context (dict): Current environmental conditions
            audience_profile (dict): Current audience demographics
            
        Returns:
            list: Matching advertisement data
        """
        # Extract relevant criteria
        criteria = {}
        
        # Map environmental conditions to ad criteria
        if "temperature_category" in weather_context:
            criteria["temperature"] = weather_context["temperature_category"]
            
        if "humidity_category" in weather_context:
            criteria["humidity"] = weather_context["humidity_category"]
            
        # Map audience data to ad criteria
        if audience_profile.get("audience_present", False):
            if "estimated_age_group" in audience_profile:
                criteria["age_group"] = audience_profile["estimated_age_group"]
                
            if "gender_distribution" in audience_profile:
                gender_value = audience_profile["gender_distribution"]
                if gender_value == "mostly_male":
                    criteria["gender"] = "male"
                elif gender_value == "mostly_female":
                    criteria["gender"] = "female"
                else:
                    criteria["gender"] = "both"
        
        # Find matching ads
        return self.filter_ads(criteria)