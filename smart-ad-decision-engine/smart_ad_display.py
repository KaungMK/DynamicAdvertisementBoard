"""
Smart Advertisement Board System with integrated sensors and engagement analysis
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
import subprocess
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SmartAdBoard")

# Import the decision engine
from decision_engine import ContentDecisionEngine

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
    def __init__(self, root, env_data_file, audience_data_file):
        self.root = root
        self.root.title("Smart Advertisement Board")
        
        # Multiple approaches to ensure fullscreen works on Raspberry Pi 5
        self.root.attributes('-fullscreen', True)  # Standard approach
        
        # Additional methods for Raspberry Pi
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window size to fill screen
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Make sure window stays on top
        self.root.attributes('-topmost', True)
        
        logger.info(f"Display initialized with resolution: {screen_width}x{screen_height}")
        logger.info(f"Looking for environment data at: {env_data_file}")
        logger.info(f"Looking for audience data at: {audience_data_file}")
        
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
        
        # Sensor subprocess objects
        self.sensor_process = None
        self.engagement_process = None
        
        # Create the main layout
        self.create_layout()
        
        # Bind escape key to exit full screen
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.bind("<Control-q>", lambda event: self.on_closing())
        self.root.bind("<Control-c>", lambda event: self.on_closing())
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start sensor processes
        self.start_sensor_processes()
        
        # Start sensor tracking
        self.start_sensor_tracking()
        
        # Start auto-cycling ads immediately
        self.start_auto_cycle()
    
    def create_layout(self):
        """Create the display layout with scrollable sensor information"""
        # Create a header frame for sensor information - increased height further
        self.header_frame = tk.Frame(self.root, bg="black", height=170)
        self.header_frame.pack(side="top", fill="x")
        
        # Make the header frame maintain its height
        self.header_frame.pack_propagate(False)
        
        # Add close button in the top-right corner
        close_button = tk.Button(
            self.header_frame, 
            text="X", 
            font=("Arial", 16, "bold"),
            bg="red", 
            fg="white", 
            command=self.on_closing,  # This calls the proper cleanup function
            width=2,
            height=1,
            relief=tk.RAISED,
            bd=3
        )
        close_button.place(x=self.root.winfo_screenwidth()-50, y=5)
        
        # Add keyboard shortcut instructions
        shortcut_label = tk.Label(
            self.header_frame,
            text="Press Ctrl+Q to exit",
            bg="black",
            fg="gray",
            font=("Arial", 8)
        )
        shortcut_label.place(x=self.root.winfo_screenwidth()-150, y=45)
        
        # Create a container frame for both data panels to ensure proper alignment
        data_container = tk.Frame(self.header_frame, bg="black")
        data_container.pack(fill="both", expand=True, padx=30, pady=10)
        
        # LEFT SIDE - Environment Data with Scrollbar
        env_container = tk.Frame(data_container, bg="black", width=450)
        env_container.pack(side="left", fill="both", padx=20)
        env_container.pack_propagate(False)  # Keep fixed width
        
        # Environment data header
        self.env_header = tk.Label(
            env_container,
            text="ENVIRONMENT DATA",
            bg="black",
            fg="white",
            font=("Arial", 14, "bold")
        )
        self.env_header.pack(anchor="w", pady=(0, 10))
        
        # Create scrollable frame for environment data
        env_canvas = tk.Canvas(env_container, bg="black", highlightthickness=0)
        env_scrollbar = ttk.Scrollbar(env_container, orient="vertical", command=env_canvas.yview)
        env_scrollable_frame = tk.Frame(env_canvas, bg="black")
        
        env_scrollable_frame.bind(
            "<Configure>",
            lambda e: env_canvas.configure(scrollregion=env_canvas.bbox("all"))
        )
        
        env_canvas.create_window((0, 0), window=env_scrollable_frame, anchor="nw")
        env_canvas.configure(yscrollcommand=env_scrollbar.set)
        
        env_canvas.pack(side="left", fill="both", expand=True)
        env_scrollbar.pack(side="right", fill="y")
        
        # Environment data label inside scrollable frame
        self.env_label = tk.Label(
            env_scrollable_frame,
            text="Waiting for sensor data...",
            bg="black",
            fg="yellow",
            font=("Arial", 12),
            justify=tk.LEFT,
            wraplength=400,  # Prevent text from being cut off
            anchor="w"       # Left-align text
        )
        self.env_label.pack(anchor="w", fill="both", expand=True)
        
        # RIGHT SIDE - Audience Data with Scrollbar
        audience_container = tk.Frame(data_container, bg="black", width=450)
        audience_container.pack(side="right", fill="both", padx=20)
        audience_container.pack_propagate(False)  # Keep fixed width
        
        # Audience data header
        self.audience_header = tk.Label(
            audience_container,
            text="AUDIENCE DATA",
            bg="black",
            fg="white",
            font=("Arial", 14, "bold")
        )
        self.audience_header.pack(anchor="w", pady=(0, 10))
        
        # Create scrollable frame for audience data
        audience_canvas = tk.Canvas(audience_container, bg="black", highlightthickness=0)
        audience_scrollbar = ttk.Scrollbar(audience_container, orient="vertical", command=audience_canvas.yview)
        audience_scrollable_frame = tk.Frame(audience_canvas, bg="black")
        
        audience_scrollable_frame.bind(
            "<Configure>",
            lambda e: audience_canvas.configure(scrollregion=audience_canvas.bbox("all"))
        )
        
        audience_canvas.create_window((0, 0), window=audience_scrollable_frame, anchor="nw")
        audience_canvas.configure(yscrollcommand=audience_scrollbar.set)
        
        audience_canvas.pack(side="left", fill="both", expand=True)
        audience_scrollbar.pack(side="right", fill="y")
        
        # Audience data label inside scrollable frame
        self.audience_label = tk.Label(
            audience_scrollable_frame,
            text="Waiting for audience data...",
            bg="black",
            fg="yellow",
            font=("Arial", 12),
            justify=tk.LEFT,
            wraplength=400,  # Prevent text from being cut off
            anchor="w"       # Left-align text
        )
        self.audience_label.pack(anchor="w", fill="both", expand=True)
        
        # Configure mouse wheel scrolling for both canvases
        def bind_mousewheel(event, canvas):
            canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        def unbind_mousewheel(event):
            # The issue is here - we need to know which canvas to unbind from
            event.widget.unbind_all("<MouseWheel>")  # Use event.widget instead of canvas

        env_canvas.bind("<Enter>", lambda e: bind_mousewheel(e, env_canvas))
        env_canvas.bind("<Leave>", unbind_mousewheel)
        audience_canvas.bind("<Enter>", lambda e: bind_mousewheel(e, audience_canvas))
        audience_canvas.bind("<Leave>", unbind_mousewheel)

        # Separator line between header and content
        separator = tk.Frame(self.root, height=2, bg="gray")
        separator.pack(fill="x", padx=0)
        
        # Main frame for ad display
        self.ad_frame = tk.Frame(self.root, bg="black")
        self.ad_frame.pack(expand=True, fill="both")
        
        # Frame to hold the image with padding
        image_container = tk.Frame(self.ad_frame, bg="black")
        image_container.pack(expand=True, fill="both", padx=50, pady=20)
        
        # Label to display the ad image
        self.ad_image_label = tk.Label(image_container, bg="black")
        self.ad_image_label.pack(expand=True, fill="both")
        
        # Separator line between content and footer
        separator2 = tk.Frame(self.root, height=2, bg="gray")
        separator2.pack(fill="x", padx=0)
        
        # Footer frame for ad information - increased height significantly
        self.footer_frame = tk.Frame(self.root, bg="black", height=100)
        self.footer_frame.pack(side="bottom", fill="x")
        
        # Make the footer frame maintain its height
        self.footer_frame.pack_propagate(False)
        
        # Label to show ad info at the bottom with increased padding
        self.ad_info_label = tk.Label(
            self.footer_frame, 
            text="Loading advertisements...", 
            bg="black", 
            fg="white",
            font=("Arial", 16, "bold"),
            wraplength=800  # Ensure long ad titles don't get cut off
        )
        self.ad_info_label.pack(expand=True, fill="both", padx=40, pady=30)
    
    def start_sensor_processes(self):
        """Start the temperature/humidity sensor and engagement analyzer processes"""
        try:
            # Use the correct path for sensor scripts
            sensors_dir = "/home/EDGY/Documents/DynamicAdvertisementBoard/sensors"
            base_dir = "/home/EDGY/Documents/DynamicAdvertisementBoard"  # Root directory
            
            # Set environment variables to tell scripts where to save files
            env = os.environ.copy()
            env["OUTPUT_DIR"] = base_dir  # Set this to tell scripts where to save data
            
            # Start the temperature/humidity sensor process
            sensor_script = os.path.join(sensors_dir, "temp_humd_sensor.py")
            if os.path.exists(sensor_script):
                logger.info(f"Starting temperature/humidity sensor at {sensor_script}")
                # Use Popen to run the script in the background with environment variables
                self.sensor_process = subprocess.Popen(
                    [sys.executable, sensor_script], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    cwd=base_dir,  # Run in base directory instead of sensors
                    env=env
                )
                logger.info(f"Temperature/humidity sensor started with PID {self.sensor_process.pid}")
            else:
                logger.error(f"Temperature/humidity sensor script not found at {sensor_script}")
            
            # Start the engagement analyzer process
            engagement_script = os.path.join(sensors_dir, "engagement_analyzer.py")
            if os.path.exists(engagement_script):
                logger.info(f"Starting engagement analyzer at {engagement_script}")
                # Use Popen to run the script in the background
                self.engagement_process = subprocess.Popen(
                    [sys.executable, engagement_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=base_dir,  # Run in base directory instead of sensors
                    env=env
                )
                logger.info(f"Engagement analyzer started with PID {self.engagement_process.pid}")
            else:
                logger.error(f"Engagement analyzer script not found at {engagement_script}")
                
        except Exception as e:
            logger.error(f"Error starting sensor processes: {e}")
    
    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode"""
        self.root.attributes('-fullscreen', False)
        self.root.overrideredirect(False)  # Restore window decorations
        self.root.attributes('-topmost', False)  # Remove always-on-top
        self.root.geometry('800x600')  # Set a reasonable window size
        return "break"
    
    def on_closing(self):
        """Handle window closing by terminating subprocesses"""
        self.stop_thread = True
        
        # Terminate sensor processes
        if self.sensor_process:
            try:
                logger.info(f"Terminating temperature/humidity sensor process (PID {self.sensor_process.pid})")
                self.sensor_process.terminate()
            except Exception as e:
                logger.error(f"Error terminating sensor process: {e}")
            
        if self.engagement_process:
            try:
                logger.info(f"Terminating engagement analyzer process (PID {self.engagement_process.pid})")
                self.engagement_process.terminate()
            except Exception as e:
                logger.error(f"Error terminating engagement process: {e}")
            
        # Destroy the window
        self.root.destroy()
    
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
            
            # Wait for 10 seconds (increased from 5 seconds)
            for _ in range(100):  # Check stop flag every 100ms (100 * 100ms = 10 seconds)
                if self.stop_thread:
                    break
                time.sleep(0.1)
    
    def update_sensor_display(self):
        """Update the sensor data display with current readings"""
        try:
            # Check if files have been modified before reading them
            env_updated = self.decision_engine.check_env_file_updated()
            audience_updated = self.decision_engine.check_audience_file_updated()
            
            update_needed = False
            
            # Only update environmental data if file has changed
            if env_updated:
                # Get environmental context
                env_context = self.decision_engine.get_environmental_context()
                
                # Format environmental data display with better spacing and abbreviated timestamp
                env_text = f"Temperature:  {env_context['temperature']:.1f}°C  ({env_context['temperature_category']})\n\n"
                env_text += f"Humidity:  {env_context['humidity']:.1f}%  ({env_context['humidity_category']})\n\n"
                
                # Check if 'predicted_weather' is in the context and add it
                if 'predicted_weather' in env_context:
                    env_text += f"Weather:  {env_context['predicted_weather']}\n\n"
                else:
                    env_text += f"Weather:  Unknown\n\n"
                    
                # Abbreviate timestamp to prevent it from being too long
                timestamp = env_context['timestamp']
                if len(timestamp) > 19:  # If it has more than just date and time
                    timestamp = timestamp[:19]  # Keep only the date and time part
                env_text += f"Timestamp:  {timestamp}"
                
                # Update the display
                self.env_label.config(text=env_text)
                update_needed = True
                logger.info("Environmental data updated based on file changes")
            
            # Only update audience data if file has changed
            if audience_updated:
                # Get audience context
                audience_context = self.decision_engine.get_audience_context()
                
                # Format audience data display with better spacing and abbreviated timestamp
                if audience_context['audience_present']:
                    audience_text = f"Present:  Yes\n\n"
                    if 'count' in audience_context:
                        audience_text += f"Count:  {audience_context['count']} people\n\n"
                    if 'group_size' in audience_context:
                        audience_text += f"Size:  {audience_context['group_size']} people\n\n"
                    audience_text += f"Age Group:  {audience_context['age_group']}\n\n"
                    audience_text += f"Gender:  {audience_context['gender']}\n\n"
                    if 'emotion' in audience_context:
                        audience_text += f"Emotion:  {audience_context['emotion']}\n\n"
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
                
                # Update the display
                self.audience_label.config(text=audience_text)
                update_needed = True
                logger.info("Audience data updated based on file changes")
            
            # If anything was updated, consider refreshing the ad selection
            if update_needed and random.random() < 0.2:  # 20% chance to refresh ad on data update
                self.select_next_ad()
                
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
                
                # Get available space for the image
                screen_width = self.root.winfo_screenwidth() - 100  # Account for padding
                screen_height = self.root.winfo_screenheight() - self.header_frame.winfo_height() - self.footer_frame.winfo_height() - 60  # Account for separators and padding
                
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
                
                # Add a colored border/frame around the image
                # Create a larger canvas with a colored border
                border_width = 8  # Width of the border in pixels
                border_color = (100, 0, 150)  # Purple color for border
                
                # Create a new image with space for the border
                bordered_img = Image.new('RGB', (new_width + 2*border_width, new_height + 2*border_width), border_color)
                # Paste the original image in the center
                bordered_img.paste(img, (border_width, border_width))
                
                # Convert to Tkinter format
                img_tk = ImageTk.PhotoImage(bordered_img)
                
                # Update the image label
                self.ad_image_label.config(image=img_tk)
                self.ad_image_label.image = img_tk  # Keep a reference
                
                # Create info text based on ad targeting with better spacing
                target_info = f" (ID: {ad['ad_id']})"
                
                # Create a list of targeting criteria (limit to essential info)
                targeting = []
                if "age_group" in ad and ad["age_group"] not in ["all", "any"]:
                    targeting.append(f"Target: {ad['age_group']}")
                if "gender" in ad and ad["gender"] not in ["both", "any"]:
                    targeting.append(f"{ad['gender']}")
                if "temperature" in ad and ad["temperature"] not in ["any"]:
                    targeting.append(f"{ad['temperature']} weather")
                
                # Join with commas and add parentheses only if there is targeting info
                if targeting:
                    target_info += ",  " + ",  ".join(targeting[:2])  # Limit to 2 targeting criteria
                
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

def main():
    """Main function to run the advertisement display"""
    # Create absolute paths to your data files - using the correct paths
    sensors_dir = "/home/EDGY/Documents/DynamicAdvertisementBoard"
    env_data_file = os.path.join(sensors_dir, "weather_data.json")
    audience_data_file = os.path.join(sensors_dir, "engagement_data.json")

    
    # Initialize the application with the absolute paths
    root = tk.Tk()
    
    # Set no window decorations before window is drawn
    root.overrideredirect(True)
    
    # Configure window to maximize when created
    root.attributes('-zoomed', True)  # This helps on some Linux window managers
    
    # Create application after setting initial window properties
    app = SmartAdDisplay(root, 
                       env_data_file=env_data_file, 
                       audience_data_file=audience_data_file)
    
    # Enter the main loop
    root.mainloop()

if __name__ == "__main__":
    main()