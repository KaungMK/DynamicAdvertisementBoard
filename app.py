from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import boto3
from werkzeug.utils import secure_filename
import os
import uuid
import collections
from dynamodb import scan_table, ads_table, audience_table, environmental_table

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
    try:
        items = scan_table(audience_table)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    emotion_counts = collections.Counter()
    gender_counts = collections.Counter()
    age_groups = collections.Counter()
    engagement_scores = []
    durations = []

    for item in items:
        emotion = str(item.get('emotion', 'Unknown')).title()
        gender = str(item.get('gender', 'Unknown')).title()
        age = int(item.get('age', 0))
        engagement = float(item.get('engagement_score', 0))
        duration = float(item.get('duration', 0))

        # Group age into buckets
        if age < 13:
            age_group = "child"
        elif age < 20:
            age_group = "teenager"
        elif age < 60:
            age_group = "adult"
        else:
            age_group = "senior"

        emotion_counts[emotion] += 1
        gender_counts[gender] += 1
        age_groups[age_group] += 1
        engagement_scores.append(engagement)
        durations.append(duration)

    return jsonify({
        'emotions': dict(emotion_counts),
        'age_groups': dict(age_groups),
        'gender_counts': dict(gender_counts),
        'average_engagement': round(sum(engagement_scores) / len(engagement_scores), 2) if engagement_scores else 0,
        'average_duration': round(sum(durations) / len(durations), 2) if durations else 0
    })

if __name__ == '__main__':
    app.run(debug=True)
