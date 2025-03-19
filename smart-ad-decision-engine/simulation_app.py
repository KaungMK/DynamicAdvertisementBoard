"""
This is the main simulation application that ties everything together
"""

import time
import random
import logging
from datetime import datetime
import json

# Import components
from environmental_analysis import WeatherClassifier
from demographic_analysis import AudienceAnalyzer
from content_repository import ContentRepository
from decision_engine import ContentDecisionEngine
from display_manager import DisplayManager
from mock_data import ENVIRONMENT_SCENARIOS, AUDIENCE_SCENARIOS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SmartAdSimulation")

class SmartAdvertisementSimulation:
    """
    Simulation of the Smart Advertisement Board system
    """
    
    def __init__(self):
        """Initialize the simulation with all components"""
        # Initialize components
        self.weather_classifier = WeatherClassifier()
        self.audience_analyzer = AudienceAnalyzer()
        self.content_repository = ContentRepository()
        self.decision_engine = ContentDecisionEngine(self.content_repository)
        self.display_manager = DisplayManager()
        
        # Simulation state
        self.current_weather = None
        self.current_audience = None
        self.running = False
        self.cycle_count = 0
        self.last_decision_time = 0
        
        logger.info("Smart Advertisement Simulation initialized")
        
    def run_single_cycle(self, env_scenario=None, audience_scenario=None):
        """
        Run a single decision cycle
        
        Args:
            env_scenario (dict, optional): Environment scenario to use
            audience_scenario (dict, optional): Audience scenario to use
            
        Returns:
            dict: Results of this cycle
        """
        # 1. Get environmental data
        logger.info("Getting environmental data...")
        weather_context = self.weather_classifier.simulate_reading(env_scenario)
        self.current_weather = weather_context
        
        # 2. Get audience data
        logger.info("Analyzing audience...")
        audience_profile = self.audience_analyzer.simulate_audience(audience_scenario)
        self.current_audience = audience_profile
        
        # 3. Make content decision
        logger.info("Making content decision...")
        selection = self.decision_engine.select_optimal_content(
            weather_context, audience_profile
        )
        
        # 4. Display the selected content
        if selection:
            # If already displaying, stop current ad and record metrics
            if self.display_manager.is_displaying():
                display_result = self.display_manager.stop_display()
                if display_result:
                    self.decision_engine.record_performance(
                        display_result["ad_id"], display_result["metrics"]
                    )
            
            # Display new ad and pass current audience info for metrics generation
            self.display_manager.current_audience = audience_profile
            self.display_manager.display_ad(selection["ad"])
            
            # Print selection reasoning (for educational purposes)
            print("\nWhy this advertisement was selected:")
            
            # Weather match explanation
            if 'temperature_category' in weather_context and 'temperature' in selection['ad']:
                if weather_context['temperature_category'] == selection['ad']['temperature']:
                    print(f"✓ Current temperature ({weather_context['temperature_category']}) matches ad's optimal temperature")
                else:
                    print(f"✗ Current temperature ({weather_context['temperature_category']}) differs from ad's optimal temperature ({selection['ad']['temperature']})")
                    
            if 'humidity_category' in weather_context and 'humidity' in selection['ad']:
                if weather_context['humidity_category'] == selection['ad']['humidity']:
                    print(f"✓ Current humidity ({weather_context['humidity_category']}) matches ad's optimal humidity")
                else:
                    print(f"✗ Current humidity ({weather_context['humidity_category']}) differs from ad's optimal humidity ({selection['ad']['humidity']})")
                    
            # Audience match explanation
            if audience_profile.get('audience_present', False):
                if 'estimated_age_group' in audience_profile and 'age_group' in selection['ad']:
                    if selection['ad']['age_group'] == 'all':
                        print(f"✓ Ad targets all age groups, including current audience ({audience_profile['estimated_age_group']})")
                    elif audience_profile['estimated_age_group'] == selection['ad']['age_group']:
                        print(f"✓ Audience age group ({audience_profile['estimated_age_group']}) matches ad's target demographic")
                    else:
                        print(f"✗ Audience age group ({audience_profile['estimated_age_group']}) differs from ad's target ({selection['ad']['age_group']})")
                        
                if 'gender_distribution' in audience_profile and 'gender' in selection['ad']:
                    audience_gender = audience_profile['gender_distribution']
                    ad_gender = selection['ad']['gender']
                    
                    if ad_gender == 'both':
                        print(f"✓ Ad targets all genders, including current audience ({audience_gender})")
                    elif (audience_gender == 'mostly_male' and ad_gender == 'male') or \
                         (audience_gender == 'mostly_female' and ad_gender == 'female'):
                        print(f"✓ Audience gender ({audience_gender}) matches ad's target demographic")
                    else:
                        print(f"✗ Audience gender ({audience_gender}) differs from ad's target ({ad_gender})")
            else:
                print("ℹ No audience detected, selecting based on environmental factors only")
                
            # Other selection factors
            if '_score_details' in selection['ad']:
                details = selection['ad']['_score_details']
                if details['novelty_score'] >= 15:
                    print("✓ Ad has not been shown recently (high novelty score)")
                elif details['novelty_score'] >= 5:
                    print("ℹ Ad was shown a while ago (medium novelty score)")
                else:
                    print("✗ Ad was shown recently (low novelty score)")
                    
                if details['rule_multiplier'] > 1.0:
                    print(f"✓ Ad received a priority boost from rules (multiplier: {details['rule_multiplier']:.1f}x)")
            
            # Record decision timestamp
            self.last_decision_time = time.time()
            
            result = {
                "cycle": self.cycle_count,
                "weather": weather_context,
                "audience": audience_profile,
                "selection": selection
            }
        else:
            logger.warning("No content selected in this cycle")
            result = {
                "cycle": self.cycle_count,
                "weather": weather_context,
                "audience": audience_profile,
                "selection": None
            }
            
        self.cycle_count += 1
        return result
        
    def run_simulation(self, cycles=5, interval=5):
        """
        Run a continuous simulation
        
        Args:
            cycles (int): Number of decision cycles to run
            interval (int): Seconds between decision cycles
        """
        self.running = True
        self.cycle_count = 0
        
        logger.info(f"Starting simulation for {cycles} cycles with {interval}s interval")
        
        try:
            for i in range(cycles):
                # Randomly select scenarios for variation
                env_scenario = random.choice(ENVIRONMENT_SCENARIOS)
                audience_scenario = random.choice(AUDIENCE_SCENARIOS)
                
                logger.info(f"Cycle {i+1}/{cycles}: {env_scenario['name']} with {audience_scenario['name']}")
                
                # Run a single cycle
                cycle_result = self.run_single_cycle(env_scenario, audience_scenario)
                
                # In a real system, we might store these results or send to monitoring
                
                # Wait for next cycle if not the last one
                if i < cycles - 1:
                    time.sleep(interval)
                    
            # Stop the last displayed ad
            if self.display_manager.is_displaying():
                display_result = self.display_manager.stop_display()
                if display_result:
                    self.decision_engine.record_performance(
                        display_result["ad_id"], display_result["metrics"]
                    )
                    
            # Update rules based on performance data
            self.decision_engine.update_rules()
                    
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
        finally:
            self.running = False
            logger.info(f"Simulation completed after {self.cycle_count} cycles")
            
    def get_system_status(self):
        """
        Get the current status of the system
        
        Returns:
            dict: System status information
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "running": self.running,
            "cycle_count": self.cycle_count,
            "current_weather": self.current_weather,
            "current_audience": self.current_audience,
            "current_ad": self.display_manager.get_current_ad(),
            "last_decision_time": self.last_decision_time,
            "recent_selections": self.decision_engine.recent_selections[-5:] if self.decision_engine.recent_selections else []
        }
        
    def save_performance_data(self, filename="performance_data.json"):
        """
        Save performance data to a file
        
        Args:
            filename (str): Path to output file
        """
        data = {
            "timestamp": datetime.now().isoformat(),
            "cycles_completed": self.cycle_count,
            "performance_log": self.decision_engine.performance_log,
            "recent_selections": self.decision_engine.recent_selections
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Performance data saved to {filename}")

# Interactive simulation example
def interactive_simulation():
    """
    Run an interactive simulation
    """
    sim = SmartAdvertisementSimulation()
    
    print("\n===== Smart Advertisement Board Simulation =====\n")
    print("This simulation demonstrates the Decision Engine for the")
    print("Smart Advertisement Board system without requiring hardware.\n")
    
    while True:
        print("\nOptions:")
        print("1. Run a single cycle with random conditions")
        print("2. Run a single cycle with specific scenario")
        print("3. Run continuous simulation (multiple cycles)")
        print("4. Show available advertisements")
        print("5. Show system status")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == "1":
            sim.run_single_cycle()
            
        elif choice == "2":
            # Show available scenarios
            print("\nAvailable Environment Scenarios:")
            for i, scenario in enumerate(ENVIRONMENT_SCENARIOS):
                print(f"{i+1}. {scenario['name']} - {scenario['temperature']}°C, {scenario['humidity']}% humidity, {scenario['weather']}")
                
            env_choice = int(input("\nSelect environment scenario (1-4): ")) - 1
            
            print("\nAvailable Audience Scenarios:")
            for i, scenario in enumerate(AUDIENCE_SCENARIOS):
                print(f"{i+1}. {scenario['name']} - {scenario['group_size']} people, {scenario['estimated_age_group']} age group")
                
            audience_choice = int(input("\nSelect audience scenario (1-4): ")) - 1
            
            sim.run_single_cycle(
                ENVIRONMENT_SCENARIOS[env_choice],
                AUDIENCE_SCENARIOS[audience_choice]
            )
            
        elif choice == "3":
            cycles = int(input("\nEnter number of cycles (1-20): "))
            interval = int(input("Enter seconds between cycles (1-10): "))
            
            sim.run_simulation(min(20, max(1, cycles)), min(10, max(1, interval)))
            
        elif choice == "4":
            ads = sim.content_repository.get_all_ads()
            print("\nAvailable Advertisements:")
            for ad in ads:
                print(f"ID: {ad['ad_id']} - {ad['title']} - {ad['temperature']} temp, {ad['humidity']} humidity, {ad['age_group']}/{ad['gender']}")
                
        elif choice == "5":
            status = sim.get_system_status()
            print("\nSystem Status:")
            print(f"Running: {status['running']}")
            print(f"Cycles completed: {status['cycle_count']}")
            
            if status['current_weather']:
                print(f"\nCurrent Weather:")
                print(f"  Temperature: {status['current_weather']['temperature']}°C ({status['current_weather']['temperature_category']})")
                print(f"  Humidity: {status['current_weather']['humidity']}% ({status['current_weather']['humidity_category']})")
                print(f"  Weather: {status['current_weather']['weather']}")
                
            if status['current_audience']:
                print(f"\nCurrent Audience:")
                print(f"  Age Group: {status['current_audience']['estimated_age_group']}")
                print(f"  Gender: {status['current_audience']['gender_distribution']}")
                print(f"  Group Size: {status['current_audience']['group_size']}")
                
            if status['current_ad']:
                print(f"\nCurrently Displaying:")
                print(f"  Title: {status['current_ad']['title']}")
                print(f"  ID: {status['current_ad']['ad_id']}")
                
            print("\nRecent Selections:")
            for selection in status['recent_selections']:
                print(f"  {selection['timestamp']} - {selection['title']} (Score: {selection['score']:.2f})")
                
        elif choice == "6":
            # Save performance data before exiting
            sim.save_performance_data()
            print("\nThank you for using the Smart Advertisement Board Simulation!")
            break
            
        else:
            print("\nInvalid choice. Please enter a number between 1 and 6.")

if __name__ == "__main__":
    interactive_simulation()