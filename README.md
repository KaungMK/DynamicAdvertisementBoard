# Smart Advertisement Board Simulation

This project simulates the Content Decision Engine for a Smart Advertisement Board system that uses real-time environmental and audience analysis to display targeted advertisements.

## System Architecture

The system follows the architecture shown in the design diagram, with the following components:

1. **Environmental Analysis** - Simulates temperature, humidity, and weather data.
2. **Audience Analysis** - Simulates demographic data from a camera feed.
3. **Content Repository** - Stores and retrieves advertisements.
4. **Decision Engine** - Selects optimal content based on current conditions.
5. **Display Manager** - Simulates the display of advertisements.

## Files and Components

- `mock_data.py` - Contains simulated data for testing without hardware
- `environmental_analysis.py` - Simulates weather sensing and classification
- `demographic_analysis.py` - Simulates audience detection and analysis
- `content_repository.py` - Simulates the advertisement content database
- `decision_engine.py` - Implements the core decision-making logic
- `display_manager.py` - Simulates the display output
- `simulation_app.py` - Ties everything together in a simulation
- `main.py` - Entry point with command-line options

## How to Run the Simulation

1. Ensure you have Python 3.6+ installed.
2. Run the simulation in interactive mode:

```bash
python main.py
```

Or run in automatic mode with specified cycles:

```bash
python main.py --mode auto --cycles 10 --interval 3
```

## Interactive Mode Options

In interactive mode, you can:

1. Run a single decision cycle with random conditions
2. Run a single cycle with specific scenarios
3. Run a continuous simulation with multiple cycles
4. View available advertisements
5. Check system status
6. Exit and save performance data

## How the Decision Engine Works

The Decision Engine is the core component that selects advertisements based on:

1. **Weather context** - Temperature, humidity, and weather conditions
2. **Audience profile** - Demographics of viewers (age, gender, group size)
3. **Content rules** - Priorities and conditions for displaying specific ads
4. **Performance history** - Learning from past ad performance

The engine uses a scoring system to rank advertisements based on how well they match current conditions. It considers:

- Weather matching (temperature and humidity)
- Audience matching (age group and gender)
- Novelty (avoiding repetition)
- Rule-based adjustments

## Extending the Simulation

To extend this simulation:

1. Add more advertisements to `mock_data.py`
2. Create custom rules for the Decision Engine
3. Implement the ML component for learning from performance data
4. Connect to real data sources (sensors, cameras, database)

## Future Enhancements

1. Implement machine learning models for audience analysis
2. Add reinforcement learning to optimize content selection
3. Create a web interface for monitoring and configuration
4. Integrate with actual hardware (Raspberry Pi, sensors, display)
5. Connect to a real database for content management