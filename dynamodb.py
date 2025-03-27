import boto3

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


# result = write_to_dynamodb()
# result = read_all_from_dynamodb()

print(result)
