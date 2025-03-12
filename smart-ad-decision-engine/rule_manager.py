class RuleManager:
    def __init__(self, rules_file=None):
        if rules_file and os.path.exists(rules_file):
            with open(rules_file, 'r') as f:
                self.rules = json.load(f)
        else:
            # Default rules if no file exists
            self.rules = [
                {
                    "id": "rule001",
                    "name": "Hot Weather - Cold Drinks",
                    "priority": 5,
                    "conditions": {
                        "environmental": {
                            "temperature": {"min": 25, "max": 40},
                            "weather": ["sunny", "cloudy"]
                        },
                        "audience": {
                            "estimated_age_group": ["teenager", "young_adult", "adult"]
                        },
                        "temporal": {
                            "time_of_day": ["afternoon", "evening"]
                        }
                    },
                    "content_id": "ad001",  # Lemonade ad
                    "weight": 1.0
                },
                # Add more rules...
            ]
    
    def save_rules(self, filename):
        """Save current rules to a file"""
        with open(filename, 'w') as f:
            json.dump(self.rules, f, indent=2)
    
    def get_rules(self):
        return self.rules