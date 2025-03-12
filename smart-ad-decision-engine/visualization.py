import matplotlib.pyplot as plt
import numpy as np
import json

def visualize_simulation_results(log_file):
    """Visualize results from a simulation log file"""
    # Load simulation data
    with open(log_file, 'r') as f:
        logs = json.load(f)
    
    # Extract data for plotting
    temps = [log['input']['environmental']['temperature'] for log in logs]
    weathers = [log['input']['environmental']['weather'] for log in logs]
    content_ids = [log['selection']['content_id'] if log['selection'] else 'none' for log in logs]
    scores = [log['selection']['score'] if log['selection'] else 0 for log in logs]
    
    # Create a mapping of unique content IDs to colors
    unique_content = list(set(content_ids))
    colors = plt.cm.tab10(np.linspace(0, 1, len(unique_content)))
    content_colors = {content: color for content, color in zip(unique_content, colors)}
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Temperature vs Content Selection
    for content in unique_content:
        content_indices = [i for i, c in enumerate(content_ids) if c == content]
        content_temps = [temps[i] for i in content_indices]
        content_scores = [scores[i] for i in content_indices]
        
        ax1.scatter(content_temps, content_scores, 
                   color=content_colors[content], 
                   label=content, 
                   alpha=0.7, 
                   s=100)
    
    ax1.set_xlabel('Temperature (°C)')
    ax1.set_ylabel('Selection Score')
    ax1.set_title('Content Selection by Temperature')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot 2: Weather Distribution by Content
    weather_types = list(set(weathers))
    content_weather_counts = {}
    
    for content in unique_content:
        content_indices = [i for i, c in enumerate(content_ids) if c == content]
        content_weathers = [weathers[i] for i in content_indices]
        
        weather_counts = []
        for weather in weather_types:
            count = content_weathers.count(weather)
            weather_counts.append(count)
        
        content_weather_counts[content] = weather_counts
    
    # Set the width of the bars
    bar_width = 0.8 / len(unique_content)
    
    # Set position of bars on x-axis
    positions = np.arange(len(weather_types))
    
    # Plot the bars
    for i, content in enumerate(unique_content):
        offset = (i - len(unique_content)/2 + 0.5) * bar_width
        ax2.bar(positions + offset, 
                content_weather_counts[content], 
                width=bar_width, 
                color=content_colors[content], 
                label=content)
    
    ax2.set_xlabel('Weather Type')
    ax2.set_ylabel('Count')
    ax2.set_title('Content Selection by Weather')
    ax2.set_xticks(positions)
    ax2.set_xticklabels(weather_types)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig('simulation_results.png')
    plt.close()
    
    print("Visualization saved as 'simulation_results.png'")

# Example usage
# visualize_simulation_results('simulation_logs.json')