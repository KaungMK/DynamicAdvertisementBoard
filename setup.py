"""
Smart Advertisement Decision Engine Simulator
============================================

This script sets up a complete simulation environment for testing
an advertisement decision engine without physical hardware.

How to use:
1. Create a folder for your project
2. Save all the provided Python files to that folder
3. Run this script to start the simulator
"""

import os
import sys
import json

def create_project_structure():
    """Create the necessary project structure"""
    directories = [
        "data",
        "logs",
        "rules",
        "output"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("Created project directories")

def create_sample_rules():
    """Create sample rules file"""
    rules = [
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
        {
            "id": "rule002",
            "name": "Rainy Weather - Jackets",
            "priority": 4,
            "conditions": {
                "environmental": {
                    "temperature": {"min": 0, "max": 15},
                    "weather": ["rainy", "stormy", "windy"]
                },
                "audience": {
                    "estimated_age_group": ["teenager", "young_adult", "adult", "senior"]
                },
                "temporal": {
                    "time_of_day": ["morning", "evening"]
                }
            },
            "content_id": "ad002",  # Jacket ad
            "weight": 1.0
        },
        {
            "id": "rule003",
            "name": "Kids Products",
            "priority": 6,
            "conditions": {
                "audience": {
                    "estimated_age_group": ["child"]
                }
            },
            "content_id": "ad003",  # Kids toy ad
            "weight": 1.0
        }
    ]
    
    with open("rules/default_rules.json", "w") as f:
        json.dump(rules, f, indent=2)
    
    print("Created sample rules file at rules/default_rules.json")

def main():
    """Main setup function"""
    print("=== Smart Advertisement Decision Engine Simulator Setup ===\n")
    
    # Create project structure
    create_project_structure()
    
    # Create sample rules
    create_sample_rules()
    
    print("\nSetup complete! You can now run the simulator using:")
    print("python simulator.py")
    
    # Check if required modules are installed
    try:
        import matplotlib
        import numpy
    except ImportError:
        print("\nWARNING: Some required packages are missing.")
        print("To install required packages, run:")
        print("pip install matplotlib numpy")

if __name__ == "__main__":
    main()