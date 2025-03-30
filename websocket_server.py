# websocket_server.py
import asyncio
import websockets
import json
import os
import time

# Path to data files
base_dir = "/home/EDGY/Documents/DynamicAdvertisementBoard"
env_data_file = os.path.join(base_dir, "weather_data.json")
audience_data_file = os.path.join(base_dir, "engagement_data.json")

# Store connected clients
connected_clients = set()

# Function to read and send data to clients
async def broadcast_data():
    while True:
        try:
            # Read current data
            env_data = {}
            audience_data = {}
            
            if os.path.exists(env_data_file):
                with open(env_data_file, 'r') as f:
                    env_data_raw = json.load(f)
                    if env_data_raw and isinstance(env_data_raw, list):
                        env_data = env_data_raw[-1]  # Get most recent entry
            
            if os.path.exists(audience_data_file):
                with open(audience_data_file, 'r') as f:
                    audience_data = json.load(f)
            
            # Combine data
            combined_data = {
                "environmental": env_data,
                "audience": audience_data,
                "timestamp": time.time()
            }
            
            # Convert to JSON string
            data_json = json.dumps(combined_data)
            
            # Send to all connected clients
            if connected_clients:
                await asyncio.gather(
                    *[client.send(data_json) for client in connected_clients]
                )
        except Exception as e:
            print(f"Error broadcasting data: {e}")
        
        # Wait 5 seconds before next update
        await asyncio.sleep(5)

# Handler for client connections
async def handler(websocket, path):
    # Register client
    connected_clients.add(websocket)
    try:
        # Keep connection alive
        await websocket.wait_closed()
    finally:
        # Unregister client
        connected_clients.remove(websocket)

# Start server
async def main():
    # Start broadcasting task
    asyncio.create_task(broadcast_data())
    
    # Start WebSocket server
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("WebSocket server started at ws://0.0.0.0:8765")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())