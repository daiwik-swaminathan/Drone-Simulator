from flask import Flask, render_template, jsonify, redirect, url_for, request
from cassandra.cluster import Cluster
from threading import Thread
import time
import base64
import os
import uuid

# Cassandra local configuration
KEYSPACE = "iotdatabase"

app = Flask(__name__)

responseDict = {}

# Setup the Cassandra connection
def setup_cassandra_connection():
    cluster = Cluster(['127.0.0.1'])  # Localhost for local Cassandra instance
    session = cluster.connect()

    # Ensure the keyspace and table are used
    session.execute(f"USE {KEYSPACE}")

    return session

# Function to dynamically get the table name based on drone ID
def get_table_name(system_id):
    return f"drone_{system_id}"

def poll_cassandra():
    global responseDict
    session = setup_cassandra_connection()
    
    while True:
        responseDict = {}  # Reset the dictionary for each poll cycle
        
        # Loop through each drone's table
        for drone_id in range(3):  # Assuming 3 drones, adjust as necessary
            table_name = f"drone_{drone_id}"
            
            try:
                # Query all rows from the current drone's table
                rows = session.execute(f"SELECT * FROM {table_name}")
                
                # Initialize a variable to store the most recent image
                most_recent_image = None
                
                for row in rows:
                    # Compare timestamps to find the most recent image
                    if not most_recent_image or row.timestamp > most_recent_image['timestamp']:
                        most_recent_image = {
                            "id": str(row.id),
                            "system_id": row.system_id,
                            "timestamp": row.timestamp,
                            "image_data": row.image_data
                        }
                
                # If a most recent image was found, add it to responseDict
                if most_recent_image:
                    responseDict[drone_id] = most_recent_image
                else:
                    print(f"No data found for {table_name}")

            except Exception as e:
                print(f"Error querying {table_name}: {str(e)}")
        
        time.sleep(5)  # Poll every 2 seconds



@app.route('/')
def index():
    global responseDict
    return render_template('index.html', images=responseDict)

@app.route('/get_images', methods=['POST'])
def get_images():
    image_urls = []

    for drone_id, image_data in responseDict.items():  # Iterate over items in responseDict
        image_content = base64.b64decode(image_data['image_data'])  # Access image_data correctly
        image_path = f"static/images/{image_data['system_id']}.jpeg"

        # Save the image (overwriting previous one)
        with open(image_path, 'wb') as image_file:
            image_file.write(image_content)

        # Build the URL for the image with a cache-busting query parameter
        timestamp = int(time.time())  # This adds a unique query param each time
        image_url = url_for('static', filename=f"images/{image_data['system_id']}.jpeg", _external=True) + f"?t={timestamp}"
        image_urls.append({'timestamp': image_data['timestamp'], 'url': image_url})

    return jsonify(image_urls)

@app.route('/remove_sensor', methods=['POST'])
def remove_sensor():
    global responseDict
    sensor_id = request.form.get('sensor_id')

    if not sensor_id:
        return "Sensor ID is required", 400

    try:
        session = setup_cassandra_connection()
        table_name = get_table_name(sensor_id)

        # Remove the sensor from the specific drone's table
        session.execute(f"DELETE FROM {table_name} WHERE system_id = %s", [int(sensor_id)])

        # Refresh the data
        rows = session.execute(f"SELECT * FROM {table_name}")
        responseDict = [{ "id": str(row.id), "system_id": row.system_id, "timestamp": row.timestamp, "image_data": row.image_data } for row in rows]

        return redirect(url_for('index'))
    except Exception as e:
        print(f"Failed to remove sensor: {str(e)}")
        return f"Failed to remove sensor: {str(e)}", 500

@app.route('/remove_all', methods=['POST'])
def remove_all():
    global responseDict
    try:
        session = setup_cassandra_connection()

        # Assume you know the list of drone IDs
        drone_ids = [0, 1, 2]  # Replace with dynamic list of drones if available

        for drone_id in drone_ids:
            table_name = get_table_name(drone_id)

            # Remove all entries from each drone's table
            session.execute(f"TRUNCATE {table_name}")

        # Refresh the data (empty it out since we deleted everything)
        responseDict = []

        return redirect(url_for('index'))
    except Exception as e:
        print(f"Failed to remove all sensors: {str(e)}")
        return f"Failed to remove all sensors: {str(e)}", 500

if __name__ == '__main__':
    # Start polling Cassandra in a separate thread
    poll_thread = Thread(target=poll_cassandra)
    poll_thread.daemon = True  # Ensures the thread exits when the app exits
    poll_thread.start()

app.run(port=5001)