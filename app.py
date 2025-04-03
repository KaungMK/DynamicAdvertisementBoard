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
S3_BUCKET = "dynamicadstoragemk"
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
ad_table = dynamodb.Table('AdsTable')


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
        ads = scan_table(ads_table)
        audience = scan_table(audience_table)
        env = scan_table(environmental_table)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # === Get filters from query string ===
    gender_filter = request.args.get("gender", "All").lower()
    temp_filter = request.args.get("temperature", "All").lower()
    humidity_filter = request.args.get("humidity", "All").lower()
    age_filter = request.args.get("age_group", "All").lower()
    title_filter = request.args.get("title", "All").lower()

    # === Apply filters to ads only ===
    def match_filters(item):
        return (
            (gender_filter == "all" or str(item.get("gender", "")).lower() == gender_filter) and
            (temp_filter == "all" or str(item.get("temperature", "")).lower() == temp_filter) and
            (humidity_filter == "all" or str(item.get("humidity", "")).lower() == humidity_filter) and
            (age_filter == "all" or str(item.get("age_group", "")).lower() == age_filter) and
            (title_filter == "all" or title_filter in str(item.get("title", "")).lower())
        )

    filtered_ads = list(filter(match_filters, ads))

    # === Analytics from filtered ads ===
    gender_counts = collections.Counter()
    temp_counts = collections.Counter()
    humidity_counts = collections.Counter()
    ad_titles = collections.Counter()

    for ad in filtered_ads:
        gender = str(ad.get('gender', 'Unknown')).strip().title()
        temperature = str(ad.get('temperature', 'Unknown')).strip().title()
        humidity = str(ad.get('humidity', 'Unknown')).strip().title()
        title = str(ad.get('title', 'Unknown')).strip().title()

        gender_counts[gender] += 1
        temp_counts[temperature] += 1
        humidity_counts[humidity] += 1
        ad_titles[title] += 1

    # === Age Group counts from audience (no filtering here) ===
    age_groups = collections.Counter()
    for item in audience:
        try:
            age = int(item.get('age'))
        except:
            age = 0
        if age < 13:
            group = 'Child'
        elif age < 20:
            group = 'Teenager'
        elif age < 60:
            group = 'Adult'
        else:
            group = 'Senior'
        age_groups[group] += 1

    # === KPI Metrics ===
    total_ads = len(filtered_ads)
    female_pct = (gender_counts.get('Female', 0) / total_ads * 100) if total_ads else 0
    male_pct = (gender_counts.get('Male', 0) / total_ads * 100) if total_ads else 0
    both_pct = (gender_counts.get('Both', 0) / total_ads * 100) if total_ads else 0
    all_pct = (gender_counts.get('All', 0) / total_ads * 100) if total_ads else 0
    total_age_groups = len(age_groups)

    # === Scatter: actual temperature vs humidity from EnvironmentalData ===
    scatter_data = []
    for item in env:
        try:
            scatter_data.append({
                'x': float(item.get('api_temp', 0)),
                'y': float(item.get('humidity', 0)),
            })
        except:
            continue

    # === Chart: Average Duration by Emotion from AudienceData ===
    duration_by_emotion = collections.defaultdict(list)
    for item in audience:
        emotion = item.get("emotion", "Unknown")
        try:
            duration = float(item.get("duration", 0))
            duration_by_emotion[emotion].append(duration)
        except:
            continue

    avg_duration_chart = [
        {"x": emotion, "y": round(sum(times)/len(times), 2)} 
        for emotion, times in duration_by_emotion.items() if times
    ]

    # === Compute average duration from all audience records ===
    durations = []
    for item in audience:
        try:
            durations.append(float(item.get('duration', 0)))
        except:
            continue
    avg_duration = sum(durations) / len(durations) if durations else 0

    return jsonify({
        # KPI
        'total_ads': total_ads,
        'female_pct': round(female_pct, 1),
        'male_pct': round(male_pct, 1),
        'both_pct': round(both_pct, 1),
        'all_pct': round(all_pct, 1),
        'avg_duration': round(avg_duration, 2),  

        # Charts
        'age_groups': dict(age_groups),
        'gender_counts': dict(gender_counts),
        'temperature_counts': dict(temp_counts),
        'humidity_counts': dict(humidity_counts),
        # New charts
        'scatter': scatter_data,
        'avg_duration_emotion': avg_duration_chart,
    })


if __name__ == '__main__':
    app.run(debug=True)
