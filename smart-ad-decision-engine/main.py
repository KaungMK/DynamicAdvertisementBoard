"""
Main entry point for the Smart Advertisement Board simulation
"""

import argparse
from simulation_app import SmartAdvertisementSimulation, interactive_simulation

def main():
    """Main entry point with command line options"""
    parser = argparse.ArgumentParser(description='Smart Advertisement Board Simulation')
    
    parser.add_argument('--mode', choices=['interactive', 'auto'], default='interactive',
                        help='Run in interactive mode or auto mode')
    
    parser.add_argument('--cycles', type=int, default=5,
                        help='Number of cycles to run in auto mode')
    
    parser.add_argument('--interval', type=int, default=3,
                        help='Seconds between cycles in auto mode')
    
    parser.add_argument('--output', type=str, default='performance_data.json',
                        help='Output file for performance data')
    
    args = parser.parse_args()
    
    if args.mode == 'interactive':
        # Run interactive simulation
        interactive_simulation()
    else:
        # Run automatic simulation
        sim = SmartAdvertisementSimulation()
        sim.run_simulation(cycles=args.cycles, interval=args.interval)
        sim.save_performance_data(args.output)

if __name__ == "__main__":
    main()