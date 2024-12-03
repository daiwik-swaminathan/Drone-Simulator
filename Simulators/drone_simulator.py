import base64
import time
import sys
import os
import json
import random
import uuid
from cassandra.cluster import Cluster
from threading import Thread

# Local Cassandra configuration (no cloud)
KEYSPACE = "iotdatabase"
IMAGE_PATHS = ["sample1.jpeg", "sample2.jpeg", "sample3.jpeg"]

# Function to encode the image
def encode_image():
    selected_image = random.choice(IMAGE_PATHS)
    with open(selected_image, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Set up a connection to the local Cassandra instance
def setup_cassandra_connection():
    # Connect to the local Cassandra instance
    cluster = Cluster(['35.91.168.12'], port=9042)
    session = cluster.connect()

    # Create the keyspace if it doesn't exist
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{ 'class': 'SimpleStrategy', 'replication_factor': '1' }}
    """)

    # Use the keyspace
    session.execute(f"USE {KEYSPACE}")

    return session

# Function to create a table for a specific drone
def create_drone_table(session, system_id):
    table_name = f"drone_{system_id}"
    
    # Create a new table for the drone if it doesn't exist
    session.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id UUID PRIMARY KEY,
            system_id int,
            timestamp text,
            image_data text
        )
    """)

    return table_name

# Function to clear all entries from a drone table
def clear_drone_table(session, table_name):
    session.execute(f"TRUNCATE {table_name}")
    print(f"Cleared all entries from {table_name}")

# Function representing a drone's behavior
def drone_simulator(system_id, end_time):
    print(f"Starting Drone {system_id}")
    
    # Initialize the Cassandra session
    session = setup_cassandra_connection()
    
    # Create a unique table for this drone
    table_name = create_drone_table(session, system_id)
    
    # Clear all entries in the table before sending images
    clear_drone_table(session, table_name)
    
    while time.time() < end_time:
        image_data = encode_image()
        image_message = {
            "id": uuid.uuid4(),
            "system_id": system_id,
            "timestamp": time.strftime("%m/%d/%Y %H:%M:%S"),
            "image_data": image_data
        }
        
        # Insert the data into this drone's specific table
        insert_query = f"""
            INSERT INTO {table_name} (id, system_id, timestamp, image_data)
            VALUES (%s, %s, %s, %s)
        """
        session.execute(insert_query, (image_message["id"], image_message["system_id"], image_message["timestamp"], image_message["image_data"]))
        
        print(f'Drone {system_id} Published:', image_message["timestamp"])
        
        time.sleep(2)  # Send image every 5 seconds

    print(f"Drone {system_id} has completed its task.")

# Main function to start multiple drone threads
def main():
    num_drones = 40  # Adjust this number to simulate more or fewer drones
    simulation_duration = 60  # Duration of the simulation in seconds (1 minute)
    end_time = time.time() + simulation_duration  # Calculate the end time
    
    threads = []
    for i in range(num_drones):
        # Create and start a thread for each drone, passing its system_id and end_time
        t = Thread(target=drone_simulator, args=(i, end_time))
        t.start()
        threads.append(t)
    
    # Wait for all drone threads to finish
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
