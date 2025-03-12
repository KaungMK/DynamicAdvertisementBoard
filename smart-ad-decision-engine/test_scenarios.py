import json
from decision_engine import ContentDecisionEngine
from mock_repository import MockContentRepository
from rule_manager import RuleManager

def run_test_scenarios():
    """Run predefined test scenarios to validate decision engine performance"""
    # Initialize components
    content_repo = MockContentRepository()
    rule_manager = RuleManager()
    decision_engine = ContentDecisionEngine(rule_manager, content_repo)
    
    # Define test scenarios
    scenarios = [
        {
            "name": "Hot Summer Day with Young Adults",
            "environmental": {
                "temperature": 30,
                "humidity": 65,
                "weather": "sunny"
            },
            "audience": {
                "estimated_age_group": "young_adult",
                "group_size": 3
            },
            "temporal": {
                "time_of_day": "afternoon",
                "day_of_week": "saturday",
                "is_weekend": True
            },
            "expected_content": "ad001"  # Lemonade ad should win
        },
        {
            "name": "Rainy Cold Day with Adults",
            "environmental": {
                "temperature": 10,
                "humidity": 85,
                "weather": "rainy"
            },
            "audience": {
                "estimated_age_group": "adult",
                "group_size": 2
            },
            "temporal": {
                "time_of_day": "morning",
                "day_of_week": "monday",
                "is_weekend": False
            },
            "expected_content": "ad002"  # Jacket ad should win
        },
        # Add more test scenarios
    ]
    
    # Run all scenarios
    results = []
    for scenario in scenarios:
        # Run decision engine
        selection = decision_engine.get_content_selection(
            scenario["environmental"],
            scenario["audience"],
            scenario["temporal"]
        )
        
        # Check if result matches expectation
        expected_content = scenario["expected_content"]
        actual_content = selection["content_id"] if selection else "none"
        passed = expected_content == actual_content
        
        # Add result
        result = {
            "scenario": scenario["name"],
            "passed": passed,
            "expected": expected_content,
            "actual": actual_content,
            "selection_details": selection
        }
        results.append(result)
        
        # Print result
        print(f"Scenario: {scenario['name']}")
        print(f"  Expected: {expected_content}")
        print(f"  Actual: {actual_content}")
        print(f"  Result: {'PASSED' if passed else 'FAILED'}")
        print()
    
    # Calculate pass rate
    pass_count = sum(1 for r in results if r["passed"])
    pass_rate = (pass_count / len(results)) * 100
    
    print(f"SUMMARY: {pass_count}/{len(results)} tests passed ({pass_rate:.1f}%)")
    
    return results

if __name__ == "__main__":
    run_test_scenarios()