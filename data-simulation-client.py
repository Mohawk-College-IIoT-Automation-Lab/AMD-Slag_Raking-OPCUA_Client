#!/home/daniil/miniconda3/envs/opcua/bin/python
import paho.mqtt.client as mqtt
import json
import random
import signal
import sys
import os
import shutil

from paho.mqtt.enums import CallbackAPIVersion

# Configuration
BROKER = "localhost"
PORT = 1883
TOPIC_SUB = "test/events"
TOPIC_PUB = "test/data"
SAVE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "test_jsons")

# Initialize state
# Global variable to store the generated data
current_data = None
file_counter = 1

# Setup directory: Clear old ones on restart, then create fresh
if os.path.exists(SAVE_DIR):
    shutil.rmtree(SAVE_DIR)
os.makedirs(SAVE_DIR)

print(f"Files will be saved to: {SAVE_DIR}")

def generate_random_data():
    """Generates data based on user-specified ranges."""
    steel_start = round(random.random(), 2)
    steel_end = round(random.uniform(3.0, 10.0), 2)
    total_slag_start = round(100.0 - steel_start, 2)
    total_slag_end = round(100.0 - steel_end, 2)
    liquid_slag_start = round(random.uniform(total_slag_start*0.2, total_slag_start*0.4), 2)
    liquid_slag_end = round(random.uniform(total_slag_end*0.2, total_slag_end*0.4), 2)
    data = {
        "total_time_seconds": random.randint(50, 200),
        "num_pulls": random.randint(5, 15),
        "slag_index": round(random.random(), 2),
        "overall": {
            "steel_pct_start": steel_start,
            "steel_pct_end": steel_end,
            "total_slag_pct_start": total_slag_start,
            "total_slag_pct_end": total_slag_end,
            "solid_slag_pct_start": total_slag_start - liquid_slag_start,
            "solid_slag_pct_end": total_slag_end - liquid_slag_end,
            "liquid_slag_pct_start": liquid_slag_start,
            "liquid_slag_pct_end": liquid_slag_end
            }
    }
    return data

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print(f"Connected to {BROKER} successfully.")
        client.subscribe(TOPIC_SUB, qos=2)
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    global current_data, file_counter
    data = msg.payload.decode("utf-8")
    event = json.loads(data)
    
    if event["state"] == "1":
        # Generate and Save
        current_data = generate_random_data()
        file_path = os.path.join(SAVE_DIR, f"ladle_{file_counter:02d}.json")
        
        with open(file_path, "w") as f:
            json.dump(current_data, f, indent=2)
            
        print(f"Generated & Saved: {file_path}")
        file_counter += 1
        
    elif event["state"] == "0":
        # Publish
        if current_data:
            current_data["heat_id"] =  event["heat_id"]
            client.publish(TOPIC_PUB, json.dumps(current_data), qos=2)
            print(f"Published latest data to {TOPIC_PUB}")
            current_data = None 
        else:
            print("No data staged. Send '1' first.")


# Graceful shutdown handler
def signal_handler(sig, frame):
    print("\nDisconnecting from broker...")
    client.disconnect()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Client Setup
client = mqtt.Client(CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60)
    print("Application running. Press Ctrl+C to exit.")
    client.loop_forever()
except KeyboardInterrupt:
    print("\nUser interrupted. Disconnecting...")
    client.disconnect()
except Exception as e:
    print(f"Fatal error: {e}")
