import base64
import time
import sys
import os
import json
import random
import uuid
from cassandra.cluster import Cluster

# Local Cassandra configuration (no cloud)
KEYSPACE = "iotdatabase"
TABLE_NAME = "imagecollection"
IMAGE_PATHS = ["sample1.jpeg", "sample2.jpeg", "sample3.jpeg"]

# Check for proper argument count
if len(sys.argv) != 2:
    print("Usage: python3 simulator.py <IMAGE_PATH>")
    sys.exit(1)

def encode_image():
    selected_image = random.choice(IMAGE_PATHS)
    with open(selected_image, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Set up a connection to the local Cassandra instance
def setup_cassandra_connection():
    # Connect to the local Cassandra instance
    cluster = Cluster(['127.0.0.1'])  # Localhost (no Docker)
    session = cluster.connect()

    # Create the keyspace if it doesn't exist
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{ 'class': 'SimpleStrategy', 'replication_factor': '1' }}
    """)

    # Use the keyspace
    session.execute(f"USE {KEYSPACE}")

    # Create the table if it doesn't exist
    session.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id UUID PRIMARY KEY,
            system_id int,
            timestamp text,
            image_data text
        )
    """)

    return session

# Main function to send images every 5 seconds
def main():
    print("Starting Image Simulator")
    
    # Initialize the Cassandra session
    session = setup_cassandra_connection()
    
    while True:
        image_data = encode_image()
        image_message = {
            "id": uuid.uuid4(),
            "system_id": 0,
            "timestamp": time.strftime("%m/%d/%Y %H:%M:%S"),
            "image_data": image_data
        }
        
        # Insert the data into the local Cassandra instance
        insert_query = f"""
            INSERT INTO {TABLE_NAME} (id, system_id, timestamp, image_data)
            VALUES (%s, %s, %s, %s)
        """
        session.execute(insert_query, (image_message["id"], image_message["system_id"], image_message["timestamp"], image_message["image_data"]))
        
        print('Published:', image_message["timestamp"])
        time.sleep(2)

if __name__ == "__main__":
    main()
