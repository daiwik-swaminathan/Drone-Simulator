# image_classifier.py
import base64
import time
import torch
from torchvision import models, transforms
from torchvision.models import ResNet50_Weights
from cassandra.cluster import Cluster
from PIL import Image
from io import BytesIO

KEYSPACE = "iotdatabase"
NUM_DRONES = 3  # Number of drones, adjust as necessary

# Load the pre-trained ResNet model for image classification
model = models.resnet50(weights=ResNet50_Weights.DEFAULT)
model.eval()  # Set to evaluation mode

# Define a transformation pipeline for the input image
transform_pipeline = transforms.Compose([
    transforms.Resize((224, 224)),  # Resize to model's input size
    transforms.ToTensor(),  # Convert to tensor
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])  # Normalization
])

# Set up a connection to the local Cassandra instance
def setup_cassandra_connection():
    cluster = Cluster(['127.0.0.1'])  # Localhost
    session = cluster.connect()
    session.execute(f"USE {KEYSPACE}")
    return session

# Decode and classify the image
def classify_image(encoded_data):
    image_data = base64.b64decode(encoded_data)
    image = Image.open(BytesIO(image_data)).convert("RGB")
    image_tensor = transform_pipeline(image).unsqueeze(0)

    # Run through the classifier
    with torch.no_grad():
        outputs = model(image_tensor)
    _, predicted = outputs.max(1)
    return predicted.item()  # Get the predicted label

# Process new images from each drone table in a continuous loop
def continuous_image_classification():
    session = setup_cassandra_connection()
    
    # Dictionary to track the last processed image ID for each drone table
    last_processed_id = {}
    
    while True:
        for drone_id in range(NUM_DRONES):
            table_name = f"drone_{drone_id}"
            
            try:
                # Query all rows from the current drone's table
                rows = session.execute(f"SELECT * FROM {table_name}")
                
                # Initialize a variable to store the most recent image
                most_recent_image = None
                for row in rows:
                    # Compare timestamps to find the most recent image
                    if not most_recent_image or row.timestamp > most_recent_image["timestamp"]:
                        most_recent_image = {
                            "id": row.id,
                            "timestamp": row.timestamp,
                            "image_data": row.image_data
                        }
                
                # Check if there's a new image to process
                if most_recent_image and (last_processed_id.get(table_name) != most_recent_image["id"]):
                    # Classify the image and print the result
                    classification_label = classify_image(most_recent_image["image_data"])
                    # Print the category name and score
                    category_name = ResNet50_Weights.DEFAULT.meta["categories"][classification_label]

                    print(f"Drone {drone_id} - Image ID {most_recent_image['id']} classified as: {category_name}")
                    
                    # Update the last processed ID for this drone table
                    last_processed_id[table_name] = most_recent_image["id"]
                    
            except Exception as e:
                print(f"Error querying {table_name}: {str(e)}")
        
        # Pause before the next check
        print('loop')
        time.sleep(5)  # Adjust interval as necessary

if __name__ == "__main__":
    continuous_image_classification()
