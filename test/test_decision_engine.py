# test_decision_engine.py
import pytest
from decision_engine import ContentDecisionEngine
from unittest.mock import MagicMock, patch
import json
import os

class TestContentDecisionEngine:
    @pytest.fixture
    def mock_repository(self):
        # Create a mock content repository
        mock_repo = MagicMock()
        mock_repo.get_all_ads.return_value = [
            {"ad_id": "1", "title": "Ice Cream", "gender": "male", "age_group": "youth", "temperature": "hot"},
            {"ad_id": "2", "title": "Coffee", "gender": "female", "age_group": "adult", "temperature": "cold"},
            {"ad_id": "3", "title": "Sunglasses", "gender": "both", "age_group": "all", "temperature": "hot"}
        ]
        return mock_repo
    
    @pytest.fixture
    def engine(self, mock_repository, tmp_path):
        # Create temporary files for testing
        env_file = tmp_path / "weather_data.json"
        audience_file = tmp_path / "engagement_data.json"
        history_file = tmp_path / "ad_display_history.json"
        
        # Create empty files
        env_file.write_text("[]")
        audience_file.write_text('{"audience": [], "count": 0}')
        
        # Create the engine with mock repository and test files
        return ContentDecisionEngine(
            content_repository=mock_repository,
            env_data_file=str(env_file),
            audience_data_file=str(audience_file),
            history_file=str(history_file)
        )
    
    def test_calculate_demographic_relevance(self, engine):
        # Test with no audience
        audience_context = {"audience_present": False}
        ad = {"gender": "male", "age_group": "youth"}
        assert engine.calculate_demographic_relevance(ad, audience_context) == 1.0
        
        # Test with matching audience
        audience_context = {
            "audience_present": True, 
            "gender": "male", 
            "age_group": "youth"
        }
        assert engine.calculate_demographic_relevance(ad, audience_context) > 1.0
        
        # Test with non-matching audience
        audience_context = {
            "audience_present": True, 
            "gender": "female", 
            "age_group": "adult"
        }
        assert engine.calculate_demographic_relevance(ad, audience_context) < 0.5
    
    @patch('decision_engine.ContentDecisionEngine.get_environmental_context')
    @patch('decision_engine.ContentDecisionEngine.get_audience_context')
    def test_select_optimal_content(self, mock_audience, mock_env, engine):
        # Mock the context data
        mock_env.return_value = {
            "temperature_category": "hot",
            "humidity_category": "medium"
        }
        mock_audience.return_value = {
            "audience_present": True,
            "gender": "male",
            "age_group": "youth"
        }
        
        # Test ad selection
        selected_ad = engine.select_optimal_content()
        assert selected_ad is not None
        assert selected_ad["ad_id"] == "1"  # Should select the ice cream ad