class MockContentRepository:
    def __init__(self):
        self.ads = [
            {
                "id": "ad001",
                "name": "Summer Lemonade",
                "type": "beverage",
                "target_conditions": {
                    "temperature": {"min": 20, "max": 40},
                    "weather": ["sunny", "cloudy"],
                    "target_audience": ["teenager", "young_adult", "adult"],
                    "ideal_times": ["afternoon", "evening"]
                },
                "duration": 15,  # seconds
            },
            {
                "id": "ad002",
                "name": "Waterproof Jacket",
                "type": "clothing",
                "target_conditions": {
                    "temperature": {"min": 0, "max": 15},
                    "weather": ["rainy", "stormy", "windy"],
                    "target_audience": ["teenager", "young_adult", "adult", "senior"],
                    "ideal_times": ["morning", "evening"]
                },
                "duration": 20,
            },
            # Add more mock advertisements...
        ]
    
    def get_content(self, content_id):
        """Retrieve content by ID"""
        for ad in self.ads:
            if ad["id"] == content_id:
                return ad
        return None
    
    def get_all_content(self):
        """Get all available content"""
        return self.ads