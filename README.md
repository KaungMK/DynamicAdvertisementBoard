# 📊 Real-time Analytics Dashboard

This branch provides a standalone web-based analytics dashboard for visualizing historical advertisement and audience data collected by the Smart Advertisement Board. It is built with Flask, Chart.js, and connects to your AWS DynamoDB table.

## Features
- ### KPI Summary Cards
  - Total Ads
  - Percentage of Female / Male / Both / All
  - Unique Age Groups Detected
- ### Interactive Filters
  - Gender
  - Temperature
  - Humidity
  - Age Group
  - Ad Title
- ### Charts
  - Age Group Distribution (Pie Chart)
  - Gender Breakdown (Doughnut Chart)
  - Ads by Temperature (Bar Chart)
  - Ads by Humidity (Bar Chart)
  - Temperature vs Humidity (Scatter Plot)
  - Top 5 Ad Titles by Count (Horizontal Bar Chart)
- ### Responsive Layout
   - Toggle between vertical and horizontal chart layouts
   - Fully responsive and mobile-friendly

## 🛠️ Installation & Running
### 1. Clone & Checkout Branch:
```
git checkout nina
```
### 2. Create a virtual environment:
```
python -m venv venv
venv\Scripts\activate
```
### 3. Install Dependencies
```
pip install -r requirements.txt
```
### 4. Add AWS Credentials
Create a .env file in the root directory and add your AWS credentials:
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=your-aws-region
S3_BUCKET_NAME=your-s3-bucket
DYNAMODB_TABLE=your-db-table
```
### 5. Run the Flask app
```
python app.py
```
Then open your browser and visit:
```
http://localhost:5000/analytics
```
