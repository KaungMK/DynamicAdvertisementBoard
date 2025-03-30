# test_integration.py
import pytest
import time
import json
import os
from smart_ad_display import SmartAdDisplay
from tkinter import Tk
from unittest.mock import patch, MagicMock

class TestIntegration:
    @pytest.fixture
    def setup_files(self, tmp_path):
        # Create test files
        env_file = tmp_path / "weather_data.json"
        audience_file = tmp_path / "engagement_data.json"
        
        # Create with sample data
        env_data = [{"timestamp": "2025-03-30 10:00:00", "avg_dht_temp": 28.5, "avg_dht_humidity": 65.0}]
        audience_data = {
            "audience": [
                {"entry": "2025-03-30 10:00:00", "exit": "2025-03-30 10:01:00", 
                 "age": 35.0, "gender": "M", "emotion": "Neutral"}
            ],
            "count": 1,
            "audience_present": True,
            "current_audience": {
                "count": 1,
                "age": 35.0,
                "gender": "M",
                "emotion": "Neutral"
            }
        }
        
        env_file.write_text(json.dumps(env_data))
        audience_file.write_text(json.dumps(audience_data))
        
        return {"env_file": str(env_file), "audience_file": str(audience_file)}
    
    @patch('smart_ad_display.AWSContentRepository')
    def test_update_sensor_display(self, mock_repo, setup_files):
        mock_repo_instance = MagicMock()
        mock_repo.return_value = mock_repo_instance
        mock_repo_instance.get_all_ads.return_value = [
            {"ad_id": "1", "title": "Test Ad", "gender": "male", "age_group": "adult", 
             "temperature": "hot", "image_url": "https://example.com/ad.jpg"}
        ]
        
        # Initialize with test files
        root = Tk()
        display = SmartAdDisplay(
            root, 
            env_data_file=setup_files["env_file"],
            audience_data_file=setup_files["audience_file"]
        )
        
        # Mock requests for image loading
        with patch('smart_ad_display.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_get.return_value = mock_response
            
            # Test update with force
            display.update_sensor_display(force_update=True)
            
            # Verify that audience data is displayed correctly
            audience_text = display.audience_label.cget("text")
            assert "Present:  Yes" in audience_text
            assert "Gender:  male" in audience_text