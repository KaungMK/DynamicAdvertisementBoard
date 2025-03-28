"""
Simplified AWS-based Advertisement Board System for Raspberry Pi
"""

import boto3
import json
import logging
import random
import time
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SimpleAdBoard")

class AWSContentRepository:
    """
    Manages advertisement content stored in AWS (DynamoDB and S3)
    """
    
    def __init__(self, table_name='AdsTable', region_name='us-east-1'):
        """
        Initialize the AWS content repository
        
        Args:
            table_name (str): DynamoDB table name
            region_name (str): AWS region
        """
        self.table_name = table_name
        self.region_name = region_name
        
        # Initialize AWS connections
        try:
            self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
            self.table = self.dynamodb.Table(table_name)
            self.s3_client = boto3.client('s3')
            logger.info(f"Connected to AWS: DynamoDB table '{table_name}' in region '{region_name}'")
        except Exception as e:
            logger.error(f"Failed to connect to AWS: {e}")
            raise
    
    def get_all_ads(self):
        """Get all advertisements from DynamoDB"""
        try:
            response = self.table.scan()
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response.get('Items', []))
            
            logger.info(f"Retrieved {len(items)} ads from DynamoDB")
            return items
        except Exception as e:
            logger.error(f"Error retrieving ads from DynamoDB: {e}")
            return []
    
    def get_ad_by_id(self, ad_id):
        """Get a specific advertisement by ID"""
        try:
            response = self.table.get_item(Key={'ad_id': ad_id})
            item = response.get('Item')
            return item
        except Exception as e:
            logger.error(f"Error retrieving ad {ad_id} from DynamoDB: {e}")
            return None

class SimpleAdDisplay:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Advertisement Board")
        self.root.attributes('-fullscreen', True)  # Full screen for Raspberry Pi
        
        # Initialize components
        self.content_repository = AWSContentRepository()
        self.recent_selections = []  # Track recent selections to avoid repetition
        
        # Current state
        self.current_ad = None
        self.ad_display_thread = None
        self.stop_thread = False
        
        # Main frame for ad display
        self.ad_frame = tk.Frame(self.root, bg="black")
        self.ad_frame.pack(expand=True, fill="both")
        
        # Label to display the ad image
        self.ad_image_label = tk.Label(self.ad_frame, bg="black")
        self.ad_image_label.pack(expand=True, fill="both")
        
        # Label to show ad info at the bottom
        self.ad_info_label = tk.Label(
            self.ad_frame, 
            text="Loading advertisements...", 
            bg="black", 
            fg="white",
            font=("Arial", 12)
        )
        self.ad_info_label.pack(side="bottom", fill="x", padx=10, pady=10)
        
        # Bind escape key to exit full screen
        self.root.bind("<Escape>", self.exit_fullscreen)
        
        # Start auto-cycling ads immediately
        self.start_auto_cycle()
    
    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode"""
        self.root.attributes('-fullscreen', False)
        return "break"
    
    def start_auto_cycle(self):
        """Start automatic cycling of advertisements"""
        if not self.ad_display_thread or not self.ad_display_thread.is_alive():
            self.stop_thread = False
            self.ad_display_thread = threading.Thread(target=self.auto_cycle_thread)
            self.ad_display_thread.daemon = True
            self.ad_display_thread.start()
            logger.info("Started automatic ad cycling")
    
    def stop_auto_cycle(self):
        """Stop automatic cycling of advertisements"""
        self.stop_thread = True
        logger.info("Stopped automatic ad cycling")
    
    def auto_cycle_thread(self):
        """Thread function for automatic cycling of advertisements"""
        while not self.stop_thread:
            # Select and display the next ad
            self.select_next_ad()
            
            # Wait for 5 seconds
            for _ in range(50):  # Check stop flag every 100ms
                if self.stop_thread:
                    break
                time.sleep(0.1)
    
    def select_next_ad(self):
        """Select and display the next advertisement randomly"""
        # Get all ads
        all_ads = self.content_repository.get_all_ads()
        
        if not all_ads:
            logger.warning("No advertisements available")
            self.ad_info_label.config(text="No advertisements available")
            return
        
        # Remove recently shown ads if possible to avoid immediate repetition
        recent_ad_ids = [ad["ad_id"] for ad in self.recent_selections[-5:] if "ad_id" in ad]
        fresh_ads = [ad for ad in all_ads if ad["ad_id"] not in recent_ad_ids]
        
        # Use fresh ads if available, otherwise use all ads
        candidate_ads = fresh_ads if fresh_ads else all_ads
        
        # Select a random ad from candidates
        selected_ad = random.choice(candidate_ads)
        
        # Record this selection
        selection_record = {
            "timestamp": datetime.now().isoformat(),
            "ad_id": selected_ad["ad_id"],
            "title": selected_ad["title"]
        }
        
        # Update recent selections
        self.recent_selections.append(selection_record)
        if len(self.recent_selections) > 20:  # Keep only most recent 20
            self.recent_selections.pop(0)
            
        # Display the selected advertisement
        self.display_ad(selected_ad)
    
    def display_ad(self, ad):
        """Display the selected advertisement"""
        if not ad:
            return
            
        try:
            self.current_ad = ad
            
            # Get image URL from the ad
            image_url = ad.get('image_url', '')
            
            if not image_url:
                logger.error(f"No image URL for ad {ad.get('ad_id', 'unknown')}")
                self.ad_image_label.config(image=None)
                self.ad_info_label.config(text=f"Error: No image for {ad.get('title', 'advertisement')}")
                return
            
            try:
                # Download the image
                response = requests.get(image_url)
                response.raise_for_status()
                
                # Load and display the image
                img = Image.open(BytesIO(response.content))
                
                # Resize to fit screen
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                
                # Calculate aspect ratio to maintain proportions
                img_ratio = img.width / img.height
                screen_ratio = screen_width / screen_height
                
                if img_ratio > screen_ratio:
                    # Image is wider than screen
                    new_width = screen_width
                    new_height = int(screen_width / img_ratio)
                else:
                    # Image is taller than screen
                    new_height = screen_height
                    new_width = int(screen_height * img_ratio)
                
                img = img.resize((new_width, new_height), Image.LANCZOS)
                
                # Convert to Tkinter format
                img_tk = ImageTk.PhotoImage(img)
                
                # Update the image label
                self.ad_image_label.config(image=img_tk)
                self.ad_image_label.image = img_tk  # Keep a reference
                
                # Update the info label
                self.ad_info_label.config(
                    text=f"Now Showing: {ad['title']}"
                )
                
                logger.info(f"Successfully displayed ad: {ad['title']} (ID: {ad['ad_id']})")
                
            except Exception as e:
                logger.error(f"Error displaying image: {e}")
                self.ad_image_label.config(image=None)
                self.ad_info_label.config(text=f"Error displaying image for: {ad['title']}")
        
        except Exception as e:
            logger.error(f"Error in display_ad: {e}")

def main():
    """Main function to run the advertisement display"""
    root = tk.Tk()
    app = SimpleAdDisplay(root)
    root.mainloop()

if __name__ == "__main__":
    main()