class AdvertisementSimulator:
    def __init__(self):
        self.content_repo = MockContentRepository()
        self.rule_manager = RuleManager()
        self.decision_engine = ContentDecisionEngine(self.rule_manager, self.content_repo)
        self.logs = []
        
    def run_single_simulation(self):
        """Run a single simulation cycle"""
        # Generate mock data
        env_data = generate_mock_environmental_data()
        audience_data = generate_mock_audience_data()
        time_data = generate_mock_time_data()
        
        # Get content decision
        selection = self.decision_engine.get_content_selection(env_data, audience_data, time_data)
        
        # Get full content details if selection was made
        content_details = None
        if selection:
            content_details = self.content_repo.get_content(selection["content_id"])
        
        # Log results
        result = {
            "timestamp": datetime.datetime.now().isoformat(),
            "input": {
                "environmental": env_data,
                "audience": audience_data,
                "time": time_data
            },
            "selection": selection,
            "content_details": content_details
        }
        
        self.logs.append(result)
        return result
    
    def run_batch_simulation(self, cycles=10):
        """Run multiple simulation cycles"""
        results = []
        for _ in range(cycles):
            result = self.run_single_simulation()
            results.append(result)
        return results
    
    def save_logs(self, filename):
        """Save simulation logs to file"""
        with open(filename, 'w') as f:
            json.dump(self.logs, f, indent=2)
    
    def print_simulation_result(self, result):
        """Pretty print a simulation result"""
        print("\n===== SIMULATION RESULT =====")
        print(f"ENVIRONMENTAL: {result['input']['environmental']['temperature']}°C, " +
              f"{result['input']['environmental']['humidity']}% humidity, " +
              f"{result['input']['environmental']['weather']} weather")
        
        print(f"AUDIENCE: {result['input']['audience']['group_size']} people, " +
              f"mostly {result['input']['audience']['estimated_age_group']}")
        
        print(f"TIME: {result['input']['time']['time_of_day']} on a " +
              f"{result['input']['time']['day_of_week']}")
        
        if result['selection']:
            print(f"\nSELECTED AD: {result['content_details']['name']} (ID: {result['selection']['content_id']})")
            print(f"MATCH SCORE: {result['selection']['score']:.2f}")
        else:
            print("\nNO SUITABLE CONTENT FOUND")
        
        print("=============================\n")