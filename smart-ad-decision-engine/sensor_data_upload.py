"""
DynamoDB Sensor Data Upload Utility with Duplicate Prevention

This code uploads sensor data from local JSON files to DynamoDB tables
for analytics purposes while preventing duplicate uploads.
"""

import boto3
import json
import time
import logging
import os
from datetime import datetime
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DynamoUploader")

class SensorDataUploader:
    """
    Uploads sensor data from local JSON files to DynamoDB
    with mechanisms to prevent duplicate uploads
    """
    
    def __init__(self, region_name='us-east-1'):
        """
        Initialize the uploader with AWS region
        
        Args:
            region_name (str): AWS region name
        """
        self.region_name = region_name
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.upload_tracking_file = os.path.join(self.base_dir, "dynamo_upload_tracking.json")
        
        # Initialize DynamoDB connection
        try:
            self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
            logger.info(f"Connected to DynamoDB in region '{region_name}'")
        except Exception as e:
            logger.error(f"Failed to connect to DynamoDB: {e}")
            raise
        
        # Load upload tracking data
        self.upload_tracking = self.load_upload_tracking()
    
    def load_upload_tracking(self):
        """
        Load tracking data for previously uploaded items
        
        Returns:
            dict: Tracking data for previously uploaded items
        """
        if os.path.exists(self.upload_tracking_file):
            try:
                with open(self.upload_tracking_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("Error parsing upload tracking file, creating new one")
                return {
                    "environmental": {},
                    "audience": {}
                }
        
        # Create new tracking data
        return {
            "environmental": {},
            "audience": {}
        }
    
    def save_upload_tracking(self):
        """
        Save tracking data for uploaded items
        """
        try:
            with open(self.upload_tracking_file, 'w') as f:
                json.dump(self.upload_tracking, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving upload tracking data: {e}")
    
    def create_tables_if_not_exist(self):
        """
        Creates the required DynamoDB tables if they don't already exist
        """
        # Check if EnvironmentalData table exists
        try:
            env_table = self.dynamodb.create_table(
                TableName='EnvironmentalData',
                KeySchema=[
                    {
                        'AttributeName': 'device_id',
                        'KeyType': 'HASH'  # Partition key
                    },
                    {
                        'AttributeName': 'timestamp',
                        'KeyType': 'RANGE'  # Sort key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'device_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'AttributeType': 'S'
                    },
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info("Creating EnvironmentalData table... Please wait.")
            env_table.meta.client.get_waiter('table_exists').wait(TableName='EnvironmentalData')
            logger.info("EnvironmentalData table created successfully!")
        except self.dynamodb.meta.client.exceptions.ResourceInUseException:
            logger.info("EnvironmentalData table already exists.")
            env_table = self.dynamodb.Table('EnvironmentalData')
        
        # Check if AudienceData table exists
        try:
            audience_table = self.dynamodb.create_table(
                TableName='AudienceData',
                KeySchema=[
                    {
                        'AttributeName': 'device_id',
                        'KeyType': 'HASH'  # Partition key
                    },
                    {
                        'AttributeName': 'entry_timestamp',
                        'KeyType': 'RANGE'  # Sort key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'device_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'entry_timestamp',
                        'AttributeType': 'S'
                    },
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info("Creating AudienceData table... Please wait.")
            audience_table.meta.client.get_waiter('table_exists').wait(TableName='AudienceData')
            logger.info("AudienceData table created successfully!")
        except self.dynamodb.meta.client.exceptions.ResourceInUseException:
            logger.info("AudienceData table already exists.")
            audience_table = self.dynamodb.Table('AudienceData')
        
        return env_table, audience_table
    
    def generate_item_hash(self, item):
        """
        Generate a unique hash for an item to track what's been uploaded
        
        Args:
            item (dict): Item data
            
        Returns:
            str: Hash representing the item
        """
        # Create a string representation of the item's key attributes
        item_str = json.dumps(item, sort_keys=True)
        return hashlib.md5(item_str.encode()).hexdigest()
    
    def upload_environmental_data(self, env_data_file, device_id="pi-001"):
        """
        Upload environmental data from JSON file to DynamoDB
        
        Args:
            env_data_file (str): Path to environmental data JSON file
            device_id (str): Unique identifier for the device
        """
        # Ensure the EnvironmentalData table exists
        env_table = self.dynamodb.Table('EnvironmentalData')
        
        try:
            # Read the JSON file
            with open(env_data_file, 'r') as f:
                env_data = json.load(f)
            
            if not env_data or not isinstance(env_data, list):
                logger.error(f"Invalid environmental data format in {env_data_file}")
                return
            
            # Get tracking data for this device
            device_tracking = self.upload_tracking["environmental"].setdefault(device_id, {})
            
            # Keep track of stats
            total_items = len(env_data)
            uploaded = 0
            skipped = 0
            
            logger.info(f"Processing {total_items} environmental data points")
            
            # Process each data point
            for data_point in env_data:
                try:
                    # Get timestamp or unique ID from the data point
                    timestamp = data_point.get('timestamp', '')
                    data_id = data_point.get('id', '')  # Some data points might have an ID
                    
                    # If we have an ID and have already processed it, skip
                    if data_id and data_id in device_tracking:
                        skipped += 1
                        continue
                    
                    # If we have a timestamp and have already processed it, skip
                    if timestamp and timestamp in device_tracking:
                        skipped += 1
                        continue
                    
                    # Prepare the item for DynamoDB
                    item = {
                        'device_id': device_id,
                        'timestamp': timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'temperature': data_point.get('avg_dht_temp', 0),
                        'humidity': data_point.get('avg_dht_humidity', 0),
                        'api_temp': data_point.get('api_temp', 0),
                        'api_humidity': data_point.get('api_humidity', 0),
                        'api_pressure': data_point.get('api_pressure', 0),
                        'predicted_weather': data_point.get('predicted_weather', 'Unknown'),
                        'date': timestamp.split()[0] if timestamp and ' ' in timestamp else datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    # Generate a hash for this item to track it
                    item_hash = self.generate_item_hash(item)
                    
                    # Check if this hash has already been uploaded
                    if item_hash in device_tracking.values():
                        skipped += 1
                        continue
                    
                    # Add item to DynamoDB
                    env_table.put_item(Item=item)
                    uploaded += 1
                    
                    # Track this item
                    if data_id:
                        device_tracking[data_id] = item_hash
                    if timestamp:
                        device_tracking[timestamp] = item_hash
                    
                    # Add a small delay to avoid exceeding throughput
                    time.sleep(0.05)
                    
                except Exception as e:
                    logger.error(f"Error uploading environmental data point: {e}")
            
            logger.info(f"Environmental data: {uploaded} uploaded, {skipped} skipped, {total_items} total")
            
            # Save tracking data
            self.save_upload_tracking()
            
        except FileNotFoundError:
            logger.error(f"Environmental data file not found: {env_data_file}")
        except json.JSONDecodeError:
            logger.error(f"Error parsing environmental data file: {env_data_file}")
        except Exception as e:
            logger.error(f"Error uploading environmental data: {e}")
    
    def upload_audience_data(self, audience_data_file, device_id="pi-001"):
        """
        Upload audience data from JSON file to DynamoDB
        
        Args:
            audience_data_file (str): Path to audience data JSON file
            device_id (str): Unique identifier for the device
        """
        # Ensure the AudienceData table exists
        audience_table = self.dynamodb.Table('AudienceData')
        
        try:
            # Read the JSON file
            with open(audience_data_file, 'r') as f:
                audience_data = json.load(f)
            
            if not audience_data or not isinstance(audience_data, dict) or 'audience' not in audience_data:
                logger.error(f"Invalid audience data format in {audience_data_file}")
                return
            
            # Get audience records
            audience_records = audience_data.get('audience', [])
            
            # Get tracking data for this device
            device_tracking = self.upload_tracking["audience"].setdefault(device_id, {})
            
            # Keep track of stats
            total_items = len(audience_records)
            uploaded = 0
            skipped = 0
            
            logger.info(f"Processing {total_items} audience data points")
            
            # Process each audience record
            for record in audience_records:
                try:
                    entry_timestamp = record.get('entry', '')
                    
                    # Skip if we've already processed this entry timestamp
                    if entry_timestamp and entry_timestamp in device_tracking:
                        skipped += 1
                        continue
                    
                    # Calculate the date from entry timestamp (for filtering in analytics)
                    date = entry_timestamp.split()[0] if " " in entry_timestamp else entry_timestamp
                    
                    # Prepare the item for DynamoDB
                    item = {
                        'device_id': device_id,
                        'entry_timestamp': entry_timestamp,
                        'exit_timestamp': record.get('exit', entry_timestamp),
                        'duration': record.get('duration', 0),
                        'age': record.get('age', 0),
                        'gender': record.get('gender', 'Unknown'),
                        'emotion': record.get('emotion', 'Neutral'),
                        'engagement_score': record.get('engagement_score', 0),
                        'date': date
                    }
                    
                    # Generate a hash for this item
                    item_hash = self.generate_item_hash(item)
                    
                    # Check if this hash has already been uploaded
                    if item_hash in device_tracking.values():
                        skipped += 1
                        continue
                    
                    # Add item to DynamoDB
                    audience_table.put_item(Item=item)
                    uploaded += 1
                    
                    # Track this item
                    if entry_timestamp:
                        device_tracking[entry_timestamp] = item_hash
                    
                    # Add a small delay to avoid exceeding throughput
                    time.sleep(0.05)
                    
                except Exception as e:
                    logger.error(f"Error uploading audience data point: {e}")
            
            logger.info(f"Audience data: {uploaded} uploaded, {skipped} skipped, {total_items} total")
            
            # Save tracking data
            self.save_upload_tracking()
            
        except FileNotFoundError:
            logger.error(f"Audience data file not found: {audience_data_file}")
        except json.JSONDecodeError:
            logger.error(f"Error parsing audience data file: {audience_data_file}")
        except Exception as e:
            logger.error(f"Error uploading audience data: {e}")
    
    def upload_all_data(self, env_data_file, audience_data_file, device_id="pi-001"):
        """
        Upload both environmental and audience data to DynamoDB
        
        Args:
            env_data_file (str): Path to environmental data JSON file
            audience_data_file (str): Path to audience data JSON file
            device_id (str): Unique identifier for the device
        """
        # Create tables if they don't exist
        self.create_tables_if_not_exist()
        
        # Upload environmental data
        self.upload_environmental_data(env_data_file, device_id)
        
        # Upload audience data
        self.upload_audience_data(audience_data_file, device_id)
        
        logger.info("Data upload complete!")

# Main function for command-line usage
def main():
    """Main function to run the uploader"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload sensor data to DynamoDB')
    parser.add_argument('--env-file', default='weather_data.json', help='Path to environmental data JSON file')
    parser.add_argument('--audience-file', default='engagement_data.json', help='Path to audience data JSON file')
    parser.add_argument('--device-id', default='pi-001', help='Unique identifier for the device')
    parser.add_argument('--region', default='us-east-1', help='AWS region name')
    parser.add_argument('--reset-tracking', action='store_true', help='Reset upload tracking data')
    
    args = parser.parse_args()
    
    uploader = SensorDataUploader(region_name=args.region)
    
    # Reset tracking if requested
    if args.reset_tracking:
        uploader.upload_tracking = {
            "environmental": {},
            "audience": {}
        }
        uploader.save_upload_tracking()
        logger.info("Upload tracking data has been reset")
    
    uploader.upload_all_data(
        env_data_file=args.env_file,
        audience_data_file=args.audience_file,
        device_id=args.device_id
    )

if __name__ == '__main__':
    main()