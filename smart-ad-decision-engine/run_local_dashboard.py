"""
Main script to run the Smart Advertisement Board Dashboard
with local file storage
"""

import tkinter as tk
import logging
import argparse
import os
import sys
from local_dashboard import SmartAdDashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SmartAdBoard")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Smart Advertisement Board Dashboard')
    parser.add_argument('--fullscreen', action='store_true',
                      help='Start in fullscreen mode')
    parser.add_argument('--ads-folder', type=str, default='Advertisements',
                      help='Folder containing advertisement images')
    
    args = parser.parse_args()
    
    # Ensure the advertisements folder exists
    if not os.path.exists(args.ads_folder):
        logger.info(f"Creating advertisements folder: {args.ads_folder}")
        os.makedirs(args.ads_folder)
    
    # Check if there are any images in the folder
    image_files = [f for f in os.listdir(args.ads_folder) 
                  if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        logger.warning(f"No images found in {args.ads_folder} folder.")
        print(f"\nWARNING: No images found in the '{args.ads_folder}' folder.")
        print("Please add your advertisement images to this folder.")
        print("The image filenames will be used as advertisement titles.\n")
        response = input("Do you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Initialize Tkinter
    root = tk.Tk()
    root.title("Smart Advertisement Board")
    
    # Set window size
    if args.fullscreen:
        root.attributes('-fullscreen', True)
    else:
        # Set a default size that works for most displays
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.geometry(f"{int(screen_width*0.8)}x{int(screen_height*0.8)}")
    
    # Initialize and start the dashboard
    app = SmartAdDashboard(root)
    
    # Start the Tkinter main loop
    root.mainloop()

if __name__ == "__main__":
    main()