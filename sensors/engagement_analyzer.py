# Import necessary libraries
from pathlib import Path  # For file path operations
import cv2  # OpenCV for computer vision tasks
import dlib  # For face detection
import numpy as np  # Numerical operations
from wide_resnet import WideResNet  # Custom WideResNet implementation
from tensorflow.keras.utils import get_file  # For downloading model weights
from tensorflow.keras.models import load_model  # To load emotion model
import time  # For timing operations
import json  # For JSON data handling
from datetime import datetime  # For timestamp conversion
from collections import deque, Counter  # For data tracking and voting
import os  # For path operations

# ======================
# Configuration Section
# ======================
# Get the parent directory path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Construct paths to model files
emotion_model_path = os.path.join(parent_dir, 'models', 'emotion_little_vgg_2.h5')
pretrained_model_url = "https://github.com/yu4u/age-gender-estimation/releases/download/v0.5/weights.28-3.73.hdf5"
modhash = 'fbe63257a054c1c5466cfd7bf14646d6'
emotion_classes = {0: 'Angry', 1: 'Fear', 2: 'Happy', 3: 'Neutral', 4: 'Sad', 5: 'Surprise'}

# Engagement detection parameters
ENGAGEMENT_THRESHOLD = 1.5    # Minimum required attention duration in seconds
STABILITY_THRESHOLD = 80      # Maximum allowed head movement in pixels
MIN_FACE_AREA = 2000          # Minimum face area in pixels² to consider
FACE_Y_THRESHOLD = 0.1        # Ignore faces in top 10% of frame (often false positives)
TRACKING_WINDOW = 15          # Number of frames to consider for stable predictions
MIN_FACE_DIMENSION = 20       # Minimum width/height for valid face detection

# Data saving interval (in seconds)
DATA_SAVE_INTERVAL = 3

# ==================
# Model Initialization
# ==================
# Initialize WideResNet for age/gender estimation
model = WideResNet(64, depth=16, k=8)()
model.load_weights(get_file("weights.28-3.73.hdf5", pretrained_model_url,
                          cache_dir=os.path.join(parent_dir, "models"), file_hash=modhash))

# Load emotion classification model
classifier = load_model(emotion_model_path)

# ==================
# Video Setup
# ==================
detector = dlib.get_frontal_face_detector()  # Dlib's HOG-based face detector
cap = cv2.VideoCapture(0)  # Webcam capture (0 = default camera)
active_faces = {}  # Dictionary to track currently visible faces
final_records = []  # List to store finalized engagement data

# ==================
# Core Functions
# ==================

def calculate_engagement(face_data):
    """Determines if a face meets engagement criteria using:
    - Minimum duration threshold
    - Maximum movement allowance
    Returns boolean engagement status"""
    duration = face_data['exit_time'] - face_data['entry_time']
    # Calculate movement distance from initial position
    dx = face_data['last_centroid'][0] - face_data['initial_centroid'][0]
    dy = face_data['last_centroid'][1] - face_data['initial_centroid'][1]
    movement = np.sqrt(dx**2 + dy**2)
    # Engagement requires sufficient duration and limited movement
    print(f"Duration: {duration:.1f}s | Movement: {movement:.1f}px | Engaged: {duration >= ENGAGEMENT_THRESHOLD and movement <= STABILITY_THRESHOLD}")
    return duration >= ENGAGEMENT_THRESHOLD and movement <= STABILITY_THRESHOLD

def process_face(face_img):
    """Processes face image through both emotion and demographic models
    Returns tuple: (age, gender, emotion) with error handling"""
    # Handle empty input edge case
    if face_img is None or face_img.size == 0:
        return 0, "Unknown", "Neutral"

    try:
        # Emotion detection pipeline
        face_gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
        face_gray = cv2.resize(face_gray, (48, 48)) / 255.0  # Resize and normalize
        emotion_pred = classifier.predict(np.expand_dims(face_gray, axis=(0, -1)), verbose=0)
        emotion = emotion_classes[np.argmax(emotion_pred)]  # Get class label
        
        # Age/Gender detection pipeline
        face_rgb = cv2.resize(face_img, (64, 64))  # Resize for WideResNet
        results = model.predict(np.array([face_rgb]), verbose=0)
        # Weighted age prediction across 0-100 years
        age = int(results[1].dot(np.arange(0, 101)).flatten()[0])
        # Gender thresholding (0.5 = female/male cutoff)
        gender = "F" if results[0][0][0] > 0.5 else "M"
        
        return age, gender, emotion
    except Exception as e:
        print(f"Face processing error: {str(e)}")
        return 0, "Unknown", "Neutral"  # Return safe defaults on error

def update_face_data(old_data, new_age, new_gender, new_emotion, new_centroid):
    """Updates tracking data with new observations using fixed-length queues
    Maintains initial timestamps while updating latest data"""
    old_data['age_queue'].append(new_age)
    old_data['gender_queue'].append(new_gender)
    old_data['emotion_queue'].append(new_emotion)
    return {
        'entry_time': old_data['entry_time'],  # Preserve initial timestamp
        'exit_time': time.time(),  # Update last seen time
        'age_queue': old_data['age_queue'],  # Age tracking window
        'gender_queue': old_data['gender_queue'],  # Gender history
        'emotion_queue': old_data['emotion_queue'],  # Emotion history
        'initial_centroid': old_data['initial_centroid'],  # First position
        'last_centroid': new_centroid  # Current position
    }

def weighted_gender_vote(gender_queue):
    """Determines final gender with time-weighted voting
    Recent observations have higher weight (linear weighting)"""
    if not gender_queue: 
        return "Unknown"
    # Create linear weights from 1 (oldest) to 2 (newest)
    weights = np.linspace(1, 2, num=len(gender_queue))
    # Calculate weighted scores for each gender
    female_score = sum(w for w, g in zip(weights, gender_queue) if g == "F")
    male_score = sum(w for w, g in zip(weights, gender_queue) if g == "M")
    return "F" if female_score > male_score else "M"

def get_stable_emotion(emo_queue):
    """Returns most frequent emotion in tracking window"""
    if not emo_queue: 
        return "Neutral"
    return Counter(emo_queue).most_common(1)[0][0]

def ema(values, alpha=0.3):
    """Exponential Moving Average for age smoothing
    Reduces jitter in age predictions"""
    if not values: 
        return 0
    smoothed = values[0]
    for val in values[1:]:
        smoothed = alpha * val + (1 - alpha) * smoothed
    return round(smoothed)

def load_existing_engagement_data():
    """Loads existing engagement data from file if it exists"""
    output_path = os.path.join(parent_dir, "engagement_data.json")
    
    # Check if file exists
    if os.path.exists(output_path):
        try:
            with open(output_path, "r") as f:
                data = json.load(f)
            
            # Validate file structure
            if "audience" in data and "count" in data:
                return data["audience"]
            else:
                print("Invalid engagement data structure, creating new file")
                return []
        except json.JSONDecodeError:
            print("Error decoding existing engagement data, creating new file")
            return []
        except Exception as e:
            print(f"Error loading existing engagement data: {e}")
            return []
    else:
        print("No existing engagement data file, will create new one")
        return []

def save_engagement_data():
    """Saves the current engagement data to a JSON file, preserving history"""
    global final_records
    
    # Load existing records first
    existing_records = load_existing_engagement_data()
    
    # Determine which records are new (not already in existing_records)
    new_records = []
    existing_entries = set()
    
    # Create a set of existing entry timestamps for efficient lookup
    for record in existing_records:
        if "entry" in record:
            existing_entries.add(record["entry"])
    
    # Add only new records that aren't already in the existing data
    for record in final_records:
        if record["entry"] not in existing_entries:
            new_records.append(record)
            
    # Combine existing and new records
    combined_records = existing_records + new_records
    
    # Check if there are currently any active faces being tracked
    current_audience_present = len(active_faces) > 0
    
    # Update the output data
    output_data = {
        "audience": combined_records,
        "count": len(combined_records),
        "audience_present": current_audience_present
    }
    
    # Add additional real-time information if there are active faces
    if current_audience_present:
        # Calculate average demographics of currently visible faces
        all_ages = []
        gender_counts = {"M": 0, "F": 0}
        emotion_counts = {}
        
        # Gather data from all active faces
        for face_id, face_data in active_faces.items():
            # Get age data
            if face_data['age_queue']:
                all_ages.extend(face_data['age_queue'])
            
            # Get gender data
            for gender in face_data['gender_queue']:
                if gender in ["M", "F"]:
                    gender_counts[gender] += 1
            
            # Get emotion data
            for emotion in face_data['emotion_queue']:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Determine dominant gender and emotion
        dominant_gender = "M" if gender_counts["M"] >= gender_counts["F"] else "F"
        dominant_emotion = "Neutral"
        if emotion_counts:
            dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        
        # Calculate average age
        avg_age = float(np.mean(all_ages)) if all_ages else 30.0
        
        # Add to output data
        output_data["current_audience"] = {
            "count": len(active_faces),
            "age": avg_age,
            "gender": dominant_gender,
            "emotion": dominant_emotion
        }
    
    # Save engagement data to JSON file in parent directory
    output_path = os.path.join(parent_dir, "engagement_data.json")
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Saved engagement data: {len(new_records)} new records, {len(combined_records)} total, Current audience: {current_audience_present}")
    
    # Clear the final_records list since they've been saved
    final_records = []

# ==================
# Main Processing Loop
# ==================
try:
    last_save_time = time.time()  # Initialize last save time
    
    # Initialize by loading any existing engagement data first
    print("Initializing engagement analyzer...")
    existing_records = load_existing_engagement_data()
    print(f"Loaded {len(existing_records)} existing audience records")
    
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret: 
            print("Failed to capture frame")
            break
        
        current_time = time.time()
        height, width = frame.shape[:2]
        detected = detector(frame, 1)  # Detect faces using dlib
        updated_ids = []  # Track faces seen in current frame

        # Process each detected face
        for d in detected:
            try:
                # Get face coordinates with boundary checks
                x1, y1, x2, y2 = max(0, d.left()), max(0, d.top()), min(width, d.right()), min(height, d.bottom())
                
                # Validate face meets size requirements
                if (x2 - x1) < MIN_FACE_DIMENSION or (y2 - y1) < MIN_FACE_DIMENSION:
                    continue  # Skip too small faces
                    
                face_area = (x2 - x1) * (y2 - y1)
                
                # Apply detection filters
                if face_area < MIN_FACE_AREA or y1 < height * FACE_Y_THRESHOLD:
                    continue  # Skip small faces or those in top frame area
                    
                # Extract face ROI with boundary checks
                face_img = frame[y1:y2, x1:x2]
                if face_img.size == 0:
                    continue  # Skip empty images
                    
                # Get demographic and emotion data
                age, gender, emotion = process_face(face_img)
                centroid = ((x1 + x2) // 2, (y1 + y2) // 2)  # Face center point

                # Face tracking logic: Find closest existing face
                closest = None
                min_dist = STABILITY_THRESHOLD  # Initialize with threshold
                for fid, data in active_faces.items():
                    # Calculate centroid of tracked face
                    fx1, fy1, fx2, fy2 = fid
                    f_centroid = ((fx1 + fx2) // 2, (fy1 + fy2) // 2)
                    # Euclidean distance between centroids
                    dx = centroid[0] - f_centroid[0]
                    dy = centroid[1] - f_centroid[1]
                    dist = np.sqrt(dx**2 + dy**2)
                    # Find closest within stability threshold
                    if dist < min_dist:
                        min_dist = dist
                        closest = fid

                # Update existing or create new face record
                if closest:  # Existing face found
                    data = active_faces.pop(closest)  # Remove old entry
                    updated_data = update_face_data(data, age, gender, emotion, centroid)
                    active_faces[(x1,y1,x2,y2)] = updated_data  # Add updated entry
                else:  # New face detected
                    # Initialize tracking queues
                    age_queue = deque(maxlen=TRACKING_WINDOW)
                    gender_queue = deque(maxlen=TRACKING_WINDOW)
                    emotion_queue = deque(maxlen=TRACKING_WINDOW)
                    # Add initial observation
                    age_queue.append(age)
                    gender_queue.append(gender)
                    emotion_queue.append(emotion)
                    
                    # Create new face entry
                    active_faces[(x1,y1,x2,y2)] = {
                        'entry_time': current_time,
                        'exit_time': current_time,
                        'age_queue': age_queue,
                        'gender_queue': gender_queue,
                        'emotion_queue': emotion_queue,
                        'initial_centroid': centroid,
                        'last_centroid': centroid
                    }
                updated_ids.append((x1,y1,x2,y2))  # Mark as seen
                
            except Exception as e:
                print(f"Error processing face detection: {str(e)}")
                continue

        # Handle faces that left the frame
        # Find faces not updated in current frame and older than 5s
        expired = [fid for fid in active_faces 
                  if fid not in updated_ids and 
                  current_time - active_faces[fid]['exit_time'] > 5]
        
        # Process expired faces for engagement recording
        for fid in expired:
            data = active_faces.pop(fid)
            if calculate_engagement(data):
                duration = data['exit_time'] - data['entry_time']
                final_records.append({
                    "entry": datetime.fromtimestamp(data['entry_time']).strftime('%Y-%m-%d %H:%M:%S'),
                    "exit": datetime.fromtimestamp(data['exit_time']).strftime('%Y-%m-%d %H:%M:%S'),
                    "duration": round(duration, 1),
                    "age": float(np.median(list(data['age_queue']))),  # Robust age estimate as float
                    "gender": Counter(data['gender_queue']).most_common(1)[0][0],  # Most frequent gender
                    "emotion": Counter(data['emotion_queue']).most_common(1)[0][0],  # Dominant emotion
                    "engagement_score": min(100, int((duration/10)*100))  # Score capped at 100
                })
        
        # Check if it's time to save data (every DATA_SAVE_INTERVAL seconds)
        if current_time - last_save_time >= DATA_SAVE_INTERVAL:
            save_engagement_data()
            last_save_time = current_time
            
        # Listen for ESC key to exit, but without showing the frame
        if cv2.waitKey(1) == 27:  # ESC key to exit
            break

finally:
    # Cleanup and final data saving
    cap.release()
    # No need to destroy windows since we're not showing them
    
    # Save engagement data one final time
    save_engagement_data()