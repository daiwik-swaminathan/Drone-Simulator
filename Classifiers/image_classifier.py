import base64
import time
import torch
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights
from torchvision import transforms
from cassandra.cluster import Cluster
from PIL import Image
from io import BytesIO
from flask import Flask, request, jsonify
# import psutil

KEYSPACE = "iotdatabase"

# Load pre-trained MobileNet model for image classification
model = mobilenet_v2(weights=MobileNet_V2_Weights.DEFAULT)
model.eval()

# Define transformation pipeline for images
transform_pipeline = transforms.Compose([
    transforms.Resize((224, 224)),  # Resize to model's input size
    transforms.ToTensor(),  # Convert to tensor
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])  # Normalization
])

# Set up Cassandra connection
def setup_cassandra_connection():
    cluster = Cluster(['54.202.118.142'], port=9042)
    session = cluster.connect()
    session.execute(f"USE {KEYSPACE}")
    return session

# Decode and classify a single image
def classify_image(encoded_data):
    image_data = base64.b64decode(encoded_data)
    image = Image.open(BytesIO(image_data)).convert("RGB")
    image_tensor = transform_pipeline(image).unsqueeze(0)

    # Run through the classifier
    with torch.no_grad():
        outputs = model(image_tensor)
    _, predicted = outputs.max(1)
    return predicted.item()

# Process a single drone table
def process_table(table_name):
    session = setup_cassandra_connection()
    try:
        print(f"Processing table: {table_name}")
        rows = session.execute(f"SELECT * FROM {table_name}")

        for row in rows:
            classification_label = classify_image(row.image_data)
            category_name = MobileNet_V2_Weights.DEFAULT.meta["categories"][classification_label]
            print(f"Image ID {row.id} classified as: {category_name}")

        return {
            "status": "success"
        }

    except Exception as e:
        print(f"Error processing table {table_name}: {str(e)}")
        return {"status": "error", "message": str(e)}

# Flask server to handle incoming requests
app = Flask(__name__)

import time

@app.route("/classify", methods=["POST"])
def classify():
    start_time = time.time()  # Record start time
    timestamp_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(start_time))
    print(f"Classification started at {timestamp_start}")

    data = request.json
    if not data or "table_name" not in data:
        return jsonify({"status": "error", "message": "Table name is required"}), 400

    table_name = data["table_name"]
    result = process_table(table_name)  # Your existing classification function

    end_time = time.time()  # Record end time
    timestamp_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(end_time))
    print(f"Classification ended at {timestamp_end}")
    return jsonify(result)

if __name__ == "__main__":
    # Start the Flask server and listen for incoming HAProxy requests
    app.run(host="0.0.0.0", port=5000)

