"""
Create a sample metadata file for the advertisements
based on the files in the Advertisements folder
"""

import os
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MetadataCreator")

def create_sample_metadata(ads_folder="Advertisements", output_file="ad_metadata.json"):
    """
    Create a sample metadata file for the advertisements
    """
    # Ensure ads folder exists
    if not os.path.exists(ads_folder):
        logger.warning(f"Advertisements folder not found. Creating {ads_folder}")
        os.makedirs(ads_folder)
    
    # List all image files in the ads folder
    image_files = [f for f in os.listdir(ads_folder) 
                  if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    
    if not image_files:
        logger.warning(f"No image files found in {ads_folder}")
        return
    
    # Create sample metadata for listed files
    ads = []
    
    # Sample categories for variety
    temperatures = ["cold", "moderate", "hot", "rainy"]
    humidities = ["low", "medium", "high"]
    age_groups = ["children", "teenager", "adult", "elderly", "all"]
    genders = ["male", "female", "both"]
    
    # Create default metadata based on filenames
    for i, image_file in enumerate(image_files):
        # Extract title from filename (remove extension)
        title = os.path.splitext(image_file)[0]
        
        # Create metadata based on pattern matching in filename
        # This is a simple heuristic - in a real system you'd have more sophisticated logic
        temperature = "moderate"  # default
        if "cold" in title.lower() or "winter" in title.lower() or "snow" in title.lower():
            temperature = "cold"
        elif "hot" in title.lower() or "summer" in title.lower() or "sun" in title.lower():
            temperature = "hot"
        elif "rain" in title.lower() or "umbrella" in title.lower() or "wet" in title.lower():
            temperature = "rainy"
        
        humidity = "medium"  # default
        if "dry" in title.lower() or "desert" in title.lower():
            humidity = "low"
        elif "humid" in title.lower() or "tropical" in title.lower() or "rain" in title.lower():
            humidity = "high"
        
        age_group = "all"  # default
        if "kid" in title.lower() or "child" in title.lower() or "toy" in title.lower():
            age_group = "children"
        elif "teen" in title.lower() or "youth" in title.lower():
            age_group = "teenager"
        elif "senior" in title.lower() or "elder" in title.lower() or "retire" in title.lower():
            age_group = "elderly"
        
        gender = "both"  # default
        if "men" in title.lower() or "man" in title.lower() or "male" in title.lower():
            gender = "male"
        elif "women" in title.lower() or "woman" in title.lower() or "female" in title.lower():
            gender = "female"
        
        # Create ad entry
        ad = {
            "ad_id": str(i+1),
            "title": title,
            "image_file": image_file,
            "age_group": age_group,
            "gender": gender,
            "temperature": temperature,
            "humidity": humidity
        }
        
        ads.append(ad)
    
    # Save metadata to file
    try:
        with open(output_file, 'w') as f:
            json.dump(ads, f, indent=2)
        logger.info(f"Successfully created metadata for {len(ads)} advertisements in {output_file}")
    except Exception as e:
        logger.error(f"Error saving metadata: {e}")

if __name__ == "__main__":
    create_sample_metadata()