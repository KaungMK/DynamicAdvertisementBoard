"""
Smart Advertisement Board System with improved spacing in the display layout
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
import os

# Import the decision engine
from decision_engine import ContentDecisionEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SmartAdBoard")

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

class SmartAdDisplay:
    def __init__(self, root, env_data_file="sensors/temp_humidity_data.json", audience_data_file="sensors/audience_data.json"):
        self.root = root
        self.root.title("Smart Advertisement Board")
        self.root.attributes('-fullscreen', True)  # Full screen for Raspberry Pi
        
        print(f"Looking for env data at: {env_data_file}")
        print(f"Looking for audience data at: {audience_data_file}")
        
        # Initialize components
        self.content_repository = AWSContentRepository()
        self.decision_engine = ContentDecisionEngine(
            self.content_repository,
            env_data_file=env_data_file,
            audience_data_file=audience_data_file
        )
        
        # Current state
        self.current_ad = None
        self.ad_display_thread = None
        self.stop_thread = False
        self.sensor_update_thread = None
        
        # Create the main layout
        self.create_layout()
        
        # Bind escape key to exit full screen
        self.root.bind("<Escape>", self.exit_fullscreen)
        
        # Start sensor tracking
        self.start_sensor_tracking()
        
        # Start auto-cycling ads immediately
        self.start_auto_cycle()
    
    def create_layout(self):
        """Create the display layout with persistent sensor information"""
        # Create a header frame for sensor information - increased height further
        self.header_frame = tk.Frame(self.root, bg="black", height=170)
        self.header_frame.pack(side="top", fill="x")
        
        # Make the header frame maintain its height
        self.header_frame.pack_propagate(False)
        
        # Top spacer
        tk.Frame(self.header_frame, height=5, bg="black").pack(fill="x")
        
        # Left side frame for environment data
        self.env_frame = tk.Frame(self.header_frame, bg="black")
        self.env_frame.pack(side="left", fill="both", expand=True, padx=20)
        
        # Environment data labels
        self.env_header = tk.Label(
            self.env_frame,
            text="ENVIRONMENT DATA",
            bg="black",
            fg="white",
            font=("Arial", 14, "bold")
        )
        self.env_header.pack(anchor="w", pady=(5, 10))
        
        self.env_label = tk.Label(
            self.env_frame,
            text="Waiting for sensor data...",
            bg="black",
            fg="yellow",
            font=("Arial", 12),
            justify=tk.LEFT,
            wraplength=400  # Prevent text from being cut off
        )
        self.env_label.pack(anchor="w", pady=5, fill="both", expand=True)
        
        # Right side frame for audience data
        self.audience_frame = tk.Frame(self.header_frame, bg="black")
        self.audience_frame.pack(side="right", fill="both", expand=True, padx=20)
        
        # Audience data labels
        self.audience_header = tk.Label(
            self.audience_frame,
            text="AUDIENCE DATA",
            bg="black",
            fg="white",
            font=("Arial", 14, "bold")
        )
        self.audience_header.pack(anchor="w", pady=(5, 10))
        
        self.audience_label = tk.Label(
            self.audience_frame,
            text="Waiting for audience data...",
            bg="black",
            fg="yellow",
            font=("Arial", 12),
            justify=tk.LEFT,
            wraplength=400  # Prevent text from being cut off
        )
        self.audience_label.pack(anchor="w", pady=5, fill="both", expand=True)
        
        # Separator line between header and content
        separator = tk.Frame(self.root, height=2, bg="gray")
        separator.pack(fill="x", padx=10)
        
        # Main frame for ad display
        self.ad_frame = tk.Frame(self.root, bg="black")
        self.ad_frame.pack(expand=True, fill="both")
        
        # Label to display the ad image
        self.ad_image_label = tk.Label(self.ad_frame, bg="black")
        self.ad_image_label.pack(expand=True, fill="both", pady=10)
        
        # Separator line between content and footer
        separator2 = tk.Frame(self.root, height=2, bg="gray")
        separator2.pack(fill="x", padx=10)
        
        # Footer frame for ad information - increased height
        self.footer_frame = tk.Frame(self.root, bg="black", height=80)
        self.footer_frame.pack(side="bottom", fill="x")
        
        # Make the footer frame maintain its height
        self.footer_frame.pack_propagate(False)
        
        # Label to show ad info at the bottom
        self.ad_info_label = tk.Label(
            self.footer_frame, 
            text="Loading advertisements...", 
            bg="black", 
            fg="white",
            font=("Arial", 14),
            wraplength=800  # Ensure long ad titles don't get cut off
        )
        self.ad_info_label.pack(expand=True, fill="both", padx=20, pady=20)
    
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
    
    def start_sensor_tracking(self):
        """Start a separate thread to continuously update sensor information"""
        self.sensor_update_thread = threading.Thread(target=self.sensor_update_thread_func)
        self.sensor_update_thread.daemon = True
        self.sensor_update_thread.start()
        logger.info("Started sensor tracking")
    
    def sensor_update_thread_func(self):
        """Thread function to continuously update sensor information"""
        while not self.stop_thread:
            self.update_sensor_display()
            time.sleep(2)  # Update every 2 seconds
    
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
    
    def update_sensor_display(self):
        """Update the sensor data display with current readings"""
        try:
            # Get environmental context
            env_context = self.decision_engine.get_environmental_context()
            audience_context = self.decision_engine.get_audience_context()
            
            # Format environmental data display with better spacing and abbreviated timestamp
            env_text = f"Temperature:  {env_context['temperature']:.1f}°C  ({env_context['temperature_category']})\n\n"
            env_text += f"Humidity:  {env_context['humidity']:.1f}%  ({env_context['humidity_category']})\n\n"
            # Abbreviate timestamp to prevent it from being too long
            timestamp = env_context['timestamp']
            if len(timestamp) > 19:  # If it has more than just date and time
                timestamp = timestamp[:19]  # Keep only the date and time part
            env_text += f"Timestamp:  {timestamp}"
            
            self.env_label.config(text=env_text)
            
            # Format audience data display with better spacing and abbreviated timestamp
            if audience_context['audience_present']:
                audience_text = f"Present:  Yes\n\n"
                audience_text += f"Size:  {audience_context['group_size']} people\n\n"
                audience_text += f"Age Group:  {audience_context['age_group']}\n\n"
                audience_text += f"Gender:  {audience_context['gender']}\n\n"
                # Abbreviate timestamp to prevent it from being too long
                timestamp = audience_context['timestamp']
                if len(timestamp) > 19:  # If it has more than just date and time
                    timestamp = timestamp[:19]  # Keep only the date and time part
                audience_text += f"Timestamp:  {timestamp}"
            else:
                audience_text = "Present:  No\n\n"
                # Abbreviate timestamp to prevent it from being too long
                timestamp = audience_context['timestamp']
                if len(timestamp) > 19:
                    timestamp = timestamp[:19]
                audience_text += f"Timestamp:  {timestamp}"
            
            self.audience_label.config(text=audience_text)
            
        except Exception as e:
            logger.error(f"Error updating sensor display: {e}")
            self.env_label.config(text="Error reading sensor data")
            self.audience_label.config(text="Error reading audience data")
    
    def select_next_ad(self):
        """Select and display the next advertisement using the decision engine"""
        try:
            # Use decision engine to select optimal ad
            selected_ad = self.decision_engine.select_optimal_content()
            
            if not selected_ad:
                logger.warning("No advertisement selected by decision engine")
                self.ad_info_label.config(text="No suitable advertisements available")
                return
                
            # Display the selected advertisement
            self.display_ad(selected_ad)
            
        except Exception as e:
            logger.error(f"Error selecting next ad: {e}")
    
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
                screen_height = self.root.winfo_screenheight() - self.header_frame.winfo_height() - self.footer_frame.winfo_height() - 30  # Extra space for separators
                
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
                
                # Create info text based on ad targeting with better spacing
                target_info = f" (ID: {ad['ad_id']})"
                if "age_group" in ad and ad["age_group"] not in ["all", "any"]:
                    target_info += f",  Target: {ad['age_group']}"
                if "gender" in ad and ad["gender"] not in ["both", "any"]:
                    target_info += f",  {ad['gender']}"
                if "temperature" in ad and ad["temperature"] not in ["any"]:
                    target_info += f",  {ad['temperature']} weather"
                
                # Update the info label
                self.ad_info_label.config(
                    text=f"Now Showing:  {ad['title']}{target_info}"
                )
                
                logger.info(f"Successfully displayed ad: {ad['title']} (ID: {ad['ad_id']})")
                
            except Exception as e:
                logger.error(f"Error displaying image: {e}")
                self.ad_image_label.config(image=None)
                self.ad_info_label.config(text=f"Error displaying image for: {ad['title']}")
        
        except Exception as e:
            logger.error(f"Error in display_ad: {e}")

def create_placeholder_files():
    """Create placeholder sensor data files if they don't exist"""
    # Get the directory of the current script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sensors_dir = os.path.join(base_dir, "sensors")
    
    # Create the sensors directory if it doesn't exist
    if not os.path.exists(sensors_dir):
        os.makedirs(sensors_dir)
        print(f"Created sensors directory: {sensors_dir}")
    
    # Create a placeholder temperature data file if it doesn't exist
    temp_file = os.path.join(sensors_dir, "temp_humidity_data.json")
    if not os.path.exists(temp_file):
        with open(temp_file, 'w') as f:
            f.write('''[
    {
        "id": "36a8914a-e1f1-4226-a0d1-537e148c5b30",
        "timestamp": "2025-03-28 13:25:40",
        "avg_dht_temp": 31.87,
        "avg_dht_humidity": 67.89,
        "api_temp": 31.22,
        "api_humidity": 69,
        "api_pressure": 1008
    }
]''')
        print(f"Created placeholder temperature file: {temp_file}")
    
    # Create a placeholder audience data file if it doesn't exist
    audience_file = os.path.join(sensors_dir, "audience_data.json")
    if not os.path.exists(audience_file):
        with open(audience_file, 'w') as f:
            f.write('''[
    {
        "id": "42a8914a-e1f1-4226-a0d1-537e148c5b31",
        "timestamp": "2025-03-28 13:25:40",
        "audience_present": true,
        "age_group": "adult",
        "gender": "mixed",
        "group_size": 2
    }
]''')
        print(f"Created placeholder audience file: {audience_file}")

def main():
    """Main function to run the advertisement display"""
    # Print the current working directory for debugging
    print(f"Current working directory: {os.getcwd()}")
    
    # Create absolute paths to your data files
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_data_file = os.path.join(base_dir, "sensors", "temp_humidity_data.json")
    audience_data_file = os.path.join(base_dir, "sensors", "audience_data.json")
    
    # Verify that the files exist
    print(f"Checking if env_data_file exists: {os.path.exists(env_data_file)}")
    print(f"Checking if audience_data_file exists: {os.path.exists(audience_data_file)}")
    
    # Initialize the application with the absolute paths
    root = tk.Tk()
    app = SmartAdDisplay(root, 
                       env_data_file=env_data_file, 
                       audience_data_file=audience_data_file)
    root.mainloop()

if __name__ == "__main__":
    create_placeholder_files()
    main()