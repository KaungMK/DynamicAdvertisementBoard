from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import boto3
from werkzeug.utils import secure_filename
from urllib.parse import urlparse
import os
import uuid
import collections

print("AWS_ACCESS_KEY_ID:", os.getenv("AWS_ACCESS_KEY_ID"))

app = Flask(__name__)
app.secret_key = '2009EDGY'

s3_client = boto3.client('s3')
S3_BUCKET = "adsbucket2009"
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
ad_table = dynamodb.Table('ads-table')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ad/create')
def create_ad():
    return render_template('ad_create.html')

@app.route('/ad/upload', methods=['POST'])
def upload_ad():
    if 'image' not in request.files:
        return redirect(request.url)

    image = request.files['image']
    if image.filename == '':
        return redirect(request.url)

    filename = secure_filename(image.filename)
    unique_id = str(uuid.uuid4())
    s3_key = f"{unique_id}_{filename}"

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=image.stream,
            ACL="public-read"
        )
        image_url = f"https://{S3_BUCKET}.s3.us-east-1.amazonaws.com/{s3_key}"

        title = request.form.get('title')
        gender = request.form.get('target_gender')
        age_group = request.form.get('target_age_group')
        temp = request.form.get('environment_temperature')
        humidity = request.form.get('environment_humidity')

        ad_table.put_item(Item={
            'ad_id': unique_id,
            'title': title,
            'gender': gender,
            'age_group': age_group,
            'temperature': temp,
            'humidity': humidity,
            'image_url': image_url,
            's3_key': s3_key
        })

        return redirect('/ad') 
    except Exception as e:
        return str(e)

@app.route('/ad/delete/<string:ad_id>', methods=['POST'])
def delete_ad(ad_id):
    try:
        response = ad_table.get_item(Key={'ad_id': ad_id})
        item = response.get('Item')

        if item and 's3_key' in item:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=item['s3_key'])

        ad_table.delete_item(Key={'ad_id': ad_id})

        flash("Advertisement deleted successfully!", "success")
        return redirect('/ad')
    except Exception as e:
        flash(f"Error deleting ad: {e}", "danger")
        return redirect('/ad')

@app.route('/ad')
def display_advertisments():
    try:
        response = ad_table.scan()
        items = response.get('Items', [])
        while 'LastEvaluatedKey' in response:
            response = ad_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        return render_template('ad.html', ads=items)
    except Exception as e:
        return str(e)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    filename = secure_filename(file.filename)

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=filename,
            Body=file.stream,
            ACL="public-read"
        )
        image_url = f"https://{S3_BUCKET}.s3.us-east-1.amazonaws.com/{filename}"
        return render_template('index.html', image_url=image_url)
    except Exception as e:
        return str(e)

# ✅ New route for analytics dashboard page
@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

# ✅ New route to serve processed data
@app.route('/dashboard-data')
def dashboard_data():
    try:
        response = ad_table.scan()
        items = response.get('Items', [])
        while 'LastEvaluatedKey' in response:
            response = ad_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        print("Scanned Items:", items)
    except Exception as e:
        print("Error reading from DynamoDB:", e)

        # Return dummy data fallback
        return jsonify({
            'emotions': {
                'happy': 10,
                'sad': 5,
                'angry': 3
            },
            'age_groups': {
                '20s': 6,
                '30s': 7,
                '40s': 5
            },
            'gender_counts': {
                'male': 9,
                'female': 8
            }
        })

    # Process actual data
    emotion_counts = collections.Counter()
    age_groups = collections.Counter()
    gender_counts = collections.Counter()

    for item in items:
        emotion = item.get('emotion', 'unknown')
        emotion_counts[emotion] += 1

        age = item.get('age_group', 'unknown')
        age_groups[age] += 1

        gender = item.get('gender', 'unknown')
        gender_counts[gender] += 1

    return jsonify({
        'emotions': dict(emotion_counts),
        'age_groups': dict(age_groups),
        'gender_counts': dict(gender_counts)
    })

if __name__ == '__main__':
    app.run(debug=True)
