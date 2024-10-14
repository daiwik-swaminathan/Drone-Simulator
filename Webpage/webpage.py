from flask import Flask, render_template, jsonify, redirect, url_for, request
from cassandra.cluster import Cluster
from threading import Thread
import threading
import time
import base64
import os
import uuid

# Cassandra local configuration
KEYSPACE = "iotdatabase"
TABLE_NAME = "imagecollection"

app = Flask(__name__)

responseDict = {}

# Setup the Cassandra connection
def setup_cassandra_connection():
    cluster = Cluster(['127.0.0.1'])  # Localhost for local Cassandra instance
    session = cluster.connect()

    # Ensure the keyspace and table are used
    session.execute(f"USE {KEYSPACE}")

    return session

def poll_cassandra():
    global responseDict
    session = setup_cassandra_connection()
    
    while True:
        # Query all rows from the image collection
        rows = session.execute(f"SELECT * FROM {TABLE_NAME}")
        
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
        
        # Update responseDict to hold only the most recent image
        responseDict = [most_recent_image] if most_recent_image else []
        
        time.sleep(2)  # Poll every 5 seconds


@app.route('/')
def index():
    global responseDict
    return render_template('index.html', images=responseDict)

@app.route('/get_images', methods=['POST'])
def get_images():
    image_urls = []
    
    for image_data in responseDict:  # Assuming responseDict has the images
        image_content = base64.b64decode(image_data['image_data'])
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
        
        # Remove the sensor from Cassandra by system_id
        session.execute(f"DELETE FROM {TABLE_NAME} WHERE system_id = %s", [int(sensor_id)])
        
        # Refresh the data
        rows = session.execute(f"SELECT * FROM {TABLE_NAME}")
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
        
        # Remove all entries from Cassandra
        session.execute(f"TRUNCATE {TABLE_NAME}")
        
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

    app.run()
