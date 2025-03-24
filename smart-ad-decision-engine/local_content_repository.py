"""
Local content repository that loads advertisements from a local folder
instead of AWS DynamoDB and S3
"""

import os
import json
import logging
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LocalContentRepository")

class LocalContentRepository:
    """
    Manages advertisement content stored locally instead of in AWS
    """
    
    def __init__(self, ads_folder="Advertisements", ads_metadata="ad_metadata.json"):
        """
        Initialize the local content repository
        
        Args:
            ads_folder (str): Path to folder containing ad images
            ads_metadata (str): Path to JSON file with ad metadata
        """
        self.ads_folder = ads_folder
        self.ads_metadata_file = ads_metadata
        self.ads = []
        
        # Ensure ads folder exists
        if not os.path.exists(ads_folder):
            logger.warning(f"Advertisements folder not found. Creating {ads_folder}")
            os.makedirs(ads_folder)
        
        # Load metadata if exists, otherwise create from image files
        if os.path.exists(ads_metadata):
            self.load_metadata()
        else:
            self.create_metadata_from_images()
    
    def load_metadata(self):
        """Load ad metadata from JSON file"""
        try:
            with open(self.ads_metadata_file, 'r') as f:
                self.ads = json.load(f)
            logger.info(f"Loaded metadata for {len(self.ads)} advertisements")
        except Exception as e:
            logger.error(f"Error loading ad metadata: {e}")
            self.create_metadata_from_images()
    
    def save_metadata(self):
        """Save ad metadata to JSON file"""
        try:
            with open(self.ads_metadata_file, 'w') as f:
                json.dump(self.ads, f, indent=2)
            logger.info(f"Saved metadata for {len(self.ads)} advertisements")
        except Exception as e:
            logger.error(f"Error saving ad metadata: {e}")
    
    def create_metadata_from_images(self):
        """Create metadata based on image files in the ads folder"""
        self.ads = []
        
        # List all image files in the ads folder
        image_files = [f for f in os.listdir(self.ads_folder) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        
        # Create basic metadata for each image
        for i, image_file in enumerate(image_files):
            # Extract title from filename (remove extension)
            title = os.path.splitext(image_file)[0]
            
            # Create a default ad entry
            ad = {
                "ad_id": str(i+1),
                "title": title,
                "image_file": image_file,
                "age_group": "all",     # Default to all ages
                "gender": "both",       # Default to both genders
                "temperature": "moderate", # Default to moderate temp
                "humidity": "medium"    # Default to medium humidity
            }
            
            self.ads.append(ad)
        
        logger.info(f"Created metadata for {len(self.ads)} advertisements")
        
        # Save the generated metadata
        self.save_metadata()
    
    def get_all_ads(self):
        """Get all advertisements"""
        return self.ads
    
    def get_ad_by_id(self, ad_id):
        """Get a specific advertisement by ID"""
        for ad in self.ads:
            if ad["ad_id"] == ad_id:
                return ad
        return None
    
    def get_ad_image_path(self, ad):
        """Get the full path to an ad image"""
        return os.path.join(self.ads_folder, ad["image_file"])
    
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
                    # Special handling for age group and gender
                    if key == "age_group":
                        if ad[key] != "all" and value != "all" and ad[key] != value:
                            match = False
                            break
                    elif key == "gender":
                        if ad[key] != "both" and value != "both" and ad[key] != value:
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
    
    def update_ad_metadata(self, ad_id, updates):
        """Update ad metadata"""
        for i, ad in enumerate(self.ads):
            if ad["ad_id"] == ad_id:
                # Update fields
                for key, value in updates.items():
                    if key != "ad_id" and key != "image_file":  # Don't change these
                        ad[key] = value
                
                # Save the updated metadata
                self.save_metadata()
                logger.info(f"Updated metadata for ad {ad_id}")
                return True
        
        logger.warning(f"Ad {ad_id} not found, cannot update")
        return False