from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import boto3
from werkzeug.utils import secure_filename
import os
import uuid
import collections

app = Flask(__name__)
app.secret_key = '2009EDGY'

s3_client = boto3.client('s3')
S3_BUCKET = "adsbucket2009"
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
ad_table = dynamodb.Table('ads-table')


@app.route('/')
def index():
    return redirect(url_for('analytics'))


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

        # Get form fields
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


@app.route('/analytics')
def analytics():
    return render_template('analytics.html')


@app.route('/dashboard-data')
def dashboard_data():
    gender_filter = request.args.get("gender")
    temp_filter = request.args.get("temperature")
    humidity_filter = request.args.get("humidity")
    age_filter = request.args.get("age_group")
    title_filter = request.args.get("title")

    try:
        response = ad_table.scan()
        items = response.get('Items', [])
        while 'LastEvaluatedKey' in response:
            response = ad_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Apply filters (case-insensitive)
    if gender_filter and gender_filter != "All":
        items = [item for item in items if str(item.get("gender", "")).strip().title() == gender_filter]

    if temp_filter and temp_filter != "All":
        items = [item for item in items if str(item.get("temperature", "")).strip().title() == temp_filter]

    if humidity_filter and humidity_filter != "All":
        items = [item for item in items if str(item.get("humidity", "")).strip().title() == humidity_filter]

    if age_filter and age_filter != "All":
        items = [item for item in items if str(item.get("age_group", "")).strip().title() == age_filter]

    if title_filter and title_filter != "All":
        items = [item for item in items if title_filter.lower() in str(item.get("title", "")).lower()]

    # Aggregations
    emotion_counts = collections.Counter()
    age_groups = collections.Counter()
    gender_counts = collections.Counter()
    humidity_counts = collections.Counter()
    temperature_counts = collections.Counter()
    ads_raw = []

    for item in items:
        emotion = str(item.get('emotion', 'Unknown')).strip().title()
        age = str(item.get('age_group', 'Unknown')).strip().title()
        gender = str(item.get('gender', 'Unknown')).strip().title()
        humidity = str(item.get('humidity', 'Unknown')).strip().title()
        temperature = str(item.get('temperature', 'Unknown')).strip().title()

        emotion_counts[emotion] += 1
        age_groups[age] += 1
        gender_counts[gender] += 1
        humidity_counts[humidity] += 1
        temperature_counts[temperature] += 1

        ads_raw.append({
            "title": item.get("title", "Unknown"),
            "temperature": temperature,
            "humidity": humidity,
            "gender": gender,
            "age_group": age
        })

    return jsonify({
        'emotions': dict(emotion_counts),
        'age_groups': dict(age_groups),
        'gender_counts': dict(gender_counts),
        'humidity_counts': dict(humidity_counts),
        'temperature_counts': dict(temperature_counts),
        'ads': ads_raw
    })


if __name__ == '__main__':
    app.run(debug=True)
