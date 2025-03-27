import boto3
import requests
from PIL import Image, ImageTk
import tkinter as tk
from io import BytesIO

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
s3_client = boto3.client('s3')

table = dynamodb.Table('ads-table')

# Fetch data from DynamoDB
response = table.scan()
items = response.get('Items', [])

# Extract image URLs
image_data = []
bucket_name = "adsbucket2009"  

for item in items:
    image_url = item.get('image_url', '')
    title = item.get('title', 'Ad')

    if image_url:
        object_key = image_url.split("/")[-1]
        
        try:
            # Generate a pre-signed URL (valid for 1 hour)
            signed_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=3600  # 1 hour
            )
            image_data.append((signed_url, title))

        except Exception as e:
            print(f"Failed to load image: {e}")

# GUI Setup
class AdDisplayApp:
    def __init__(self, root, images):
        self.root = root
        self.root.attributes('-fullscreen', True)  # Fullscreen mode
        self.root.bind("<Escape>", self.exit_fullscreen)  # Press ESC to exit

        self.images = images
        self.index = 0

        self.label = tk.Label(root, bg="black")
        self.label.pack(expand=True, fill="both")

        self.show_next_image()

    def show_next_image(self):
        if not self.images:
            print("No images to display.")
            return

        image_url, title = self.images[self.index]

        try:
            # Download and display the image
            img_response = requests.get(image_url)
            img_response.raise_for_status()

            img = Image.open(BytesIO(img_response.content))

            # Rotate 90 degrees
            img = img.rotate(90, expand=True)

            # Resize to fit screen
            img = img.resize((self.root.winfo_screenwidth(), self.root.winfo_screenheight()), Image.Resampling.LANCZOS)
            img = ImageTk.PhotoImage(img)

            self.label.config(image=img)
            self.label.image = img  # Keep reference

        except Exception as e:
            print(f"Error displaying image: {e}")

        # Move to next image
        self.index = (self.index + 1) % len(self.images)
        self.root.after(3000, self.show_next_image)  # Change every 3 seconds

    def exit_fullscreen(self, event):
        self.root.destroy()

# Run the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = AdDisplayApp(root, image_data)
    root.mainloop()
