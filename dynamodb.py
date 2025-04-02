import os
import boto3
from collections import Counter
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Initialize the DynamoDB resource
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN")
)

# Load table names
ads_table = dynamodb.Table(os.getenv("ADS_TABLE"))
audience_table = dynamodb.Table(os.getenv("AUDIENCE_TABLE"))
environmental_table = dynamodb.Table(os.getenv("ENVIRONMENTAL_TABLE"))

# === Write Sample to Ads Table ===
def write_to_ads_table():
    try:
        response = ads_table.put_item(
            Item={
                "id": 2,
                "name": "John Doeeeeee",
                "age": "idk",
                "email": "johndoe@example.com"
            }
        )
        return response
    except Exception as e:
        return {"error": str(e)}

# === Generic Scan Function ===
def scan_table(table):
    try:
        response = table.scan()
        items = response.get('Items', [])

        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))

        return items
    except Exception as e:
        return {"error": str(e)}

# === Read All from Ads Table ===
def read_all_from_ads():
    return scan_table(ads_table)

# === Read All from Audience Table ===
def read_all_from_audience():
    return scan_table(audience_table)

# === Read All from Environmental Table ===
def read_all_from_environmental():
    return scan_table(environmental_table)

# === Example Analytics Summary from Audience Table ===
def get_audience_analytics_summary():
    try:
        items = scan_table(audience_table)
        if isinstance(items, dict) and "error" in items:
            return items  # propagate error

        age_dist = Counter()
        gender_dist = Counter()
        emotion_dist = Counter()
        durations = []
        engagement_scores = []
        timestamps = []

        for item in items:
            age = item.get('age')
            gender = item.get('gender')
            emotion = item.get('emotion')
            duration = item.get('duration')
            engagement = item.get('engagement_score')
            ts = item.get('entry_timestamp')

            if age:
                age_dist[age] += 1
            if gender:
                gender_dist[gender] += 1
            if emotion:
                emotion_dist[emotion] += 1
            if duration:
                durations.append(float(duration))
            if engagement:
                engagement_scores.append(float(engagement))
            if ts:
                timestamps.append(ts)

        summary = {
            'age_distribution': dict(age_dist),
            'gender_distribution': dict(gender_dist),
            'emotion_distribution': dict(emotion_dist),
            'average_duration': sum(durations)/len(durations) if durations else 0,
            'average_engagement_score': sum(engagement_scores)/len(engagement_scores) if engagement_scores else 0,
            'total_audience': len(items),
            'timestamps': timestamps
        }

        return summary
    except Exception as e:
        return {"error": str(e)}