import base64
import time
import torch
from torchvision import models, transforms
from torchvision.models import ResNet50_Weights
from cassandra.cluster import Cluster
from PIL import Image
from io import BytesIO
import psutil  # For CPU and memory monitoring

KEYSPACE = "iotdatabase"
NUM_DRONES = 1

# Load pre-trained ResNet model for image classification
model = models.resnet50(weights=ResNet50_Weights.DEFAULT)
model.eval()  

# Define transformation pipeline for image
transform_pipeline = transforms.Compose([
    transforms.Resize((224, 224)),  # Resize to model's input size
    transforms.ToTensor(),  # Convert to tensor
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])  # Normalization
])

# Set up a connection to the local Cassandra instance
def setup_cassandra_connection():
    cluster = Cluster(['127.0.0.1'])  
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
    return predicted.item()  

# Classify all images from each drone table after 30 seconds, and measure CPU/memory utilization
def classify_all_images_after_delay():
    session = setup_cassandra_connection()
    
    print("Starting classification of all images in each drone table.")

    # Start timing
    start_time = time.time()
    cpu_utilizations = []
    memory_utilizations = []

    for drone_id in range(NUM_DRONES):
        table_name = f"drone_{drone_id}"
        
        try:
            # Query all rows from the current drone's table
            rows = session.execute(f"SELECT * FROM {table_name}")
            
            # Classify each image in the table
            for row in rows:
                # Record CPU and memory usage
                cpu_util = psutil.cpu_percent(interval=None)  # get CPU utilization in %
                mem_util = psutil.virtual_memory().percent    # get memory utilization in %
                cpu_utilizations.append(cpu_util)
                memory_utilizations.append(mem_util)
                
                classification_label = classify_image(row.image_data)
                # Print the category name for each classified image
                category_name = ResNet50_Weights.DEFAULT.meta["categories"][classification_label]

                print(f"Drone {drone_id} - Image ID {row.id} classified as: {category_name}")
                
        except Exception as e:
            print(f"Error querying {table_name}: {str(e)}")
    
    # End timing and print elapsed time
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Total classification time (Response Time): {elapsed_time:.2f} seconds")
    
    # Calculate and print average CPU and memory utilization
    avg_cpu_util = sum(cpu_utilizations) / len(cpu_utilizations) if cpu_utilizations else 0
    avg_memory_util = sum(memory_utilizations) / len(memory_utilizations) if memory_utilizations else 0
    print(f"Average CPU Utilization: {avg_cpu_util:.2f}%")
    print(f"Average Memory Utilization: {avg_memory_util:.2f}%")

if __name__ == "__main__":
    classify_all_images_after_delay()
