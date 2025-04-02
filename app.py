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
        ads = scan_table(ads_table)
        audience = scan_table(audience_table)
        env = scan_table(environmental_table)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # KPI counts
    gender_counts = collections.Counter()
    temp_counts = collections.Counter()
    humidity_counts = collections.Counter()
    ad_titles = collections.Counter()

    for ad in ads:
        gender = str(ad.get('gender', 'Unknown')).strip().title()
        temperature = str(ad.get('temperature', 'Unknown')).strip().title()
        humidity = str(ad.get('humidity', 'Unknown')).strip().title()
        title = str(ad.get('title', 'Unknown')).strip().title()

        gender_counts[gender] += 1
        temp_counts[temperature] += 1
        humidity_counts[humidity] += 1
        ad_titles[title] += 1

    # Audience data for age groups
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

    # KPI metrics
    total_ads = len(ads)
    female_pct = (gender_counts.get('Female', 0) / total_ads * 100) if total_ads else 0
    male_pct = (gender_counts.get('Male', 0) / total_ads * 100) if total_ads else 0
    both_pct = (gender_counts.get('Both', 0) / total_ads * 100) if total_ads else 0
    all_pct = (gender_counts.get('All', 0) / total_ads * 100) if total_ads else 0
    total_age_groups = len(age_groups)

    # EnvironmentalData for scatter chart
    scatter_data = []
    for item in env:
        try:
            t = float(item.get('temp'))
            h = float(item.get('humidity'))
            scatter_data.append({'x': t, 'y': h})
        except:
            continue

    return jsonify({
        # KPI boxes
        'total_ads': total_ads,
        'female_pct': round(female_pct, 1),
        'male_pct': round(male_pct, 1),
        'both_pct': round(both_pct, 1),
        'all_pct': round(all_pct, 1),
        'total_age_groups': total_age_groups,

        # Pie/bar charts
        'age_groups': dict(age_groups),
        'gender_counts': dict(gender_counts),
        'temperature_counts': dict(temp_counts),
        'humidity_counts': dict(humidity_counts),
        'top_ads': dict(ad_titles.most_common(5)),

        # Scatter plot
        'scatter': scatter_data
    })

if __name__ == '__main__':
    app.run(debug=True)
