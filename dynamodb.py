import boto3
from collections import Counter

# Initialize the DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Replace with your table name
TABLE_NAME = "ads-info"

# Reference the table
table = dynamodb.Table(TABLE_NAME)

def write_to_dynamodb():
    try:
        response = table.put_item(
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


def read_all_from_dynamodb():
    try:
        response = table.scan()
        items = response.get('Items', [])

        # If the scan result is paginated, continue fetching
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))

        return items
    except Exception as e:
        return {"error": str(e)}

def get_analytics_summary():
    try:
        response = table.scan()
        items = response.get('Items', [])

        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))

        age_dist = Counter()
        gender_dist = Counter()
        emotion_dist = Counter()
        attention_spans = []
        engagement_levels = []
        timestamps = []

        for item in items:
            age = item.get('age')
            gender = item.get('gender')
            emotion = item.get('emotion')
            attention = item.get('attention_span')
            engagement = item.get('engagement_level')
            ts = item.get('timestamp')

            if age:
                age_dist[age] += 1
            if gender:
                gender_dist[gender] += 1
            if emotion:
                emotion_dist[emotion] += 1
            if attention:
                attention_spans.append(float(attention))
            if engagement:
                engagement_levels.append(float(engagement))
            if ts:
                timestamps.append(ts)

        summary = {
            'age_distribution': dict(age_dist),
            'gender_distribution': dict(gender_dist),
            'emotion_distribution': dict(emotion_dist),
            'average_attention_span': sum(attention_spans)/len(attention_spans) if attention_spans else 0,
            'average_engagement_level': sum(engagement_levels)/len(engagement_levels) if engagement_levels else 0,
            'total_users': len(items),
            'timestamps': timestamps
        }

        return summary
    except Exception as e:
        return {"error": str(e)}
