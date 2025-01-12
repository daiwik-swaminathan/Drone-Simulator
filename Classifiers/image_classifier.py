import base64
import time
import torch
from torchvision import models, transforms
# from torchvision.models import ResNet50_Weights
# from torchvision.models import ResNet18_Weights, resnet18
# from torchvision.models import mobilenet_v2, MobileNet_V2_Weights
from efficientnet_pytorch import EfficientNet
from cassandra.cluster import Cluster
from PIL import Image
from io import BytesIO
import psutil  # For CPU and memory monitoring

KEYSPACE = "iotdatabase"
NUM_DRONES = 5

# Load pre-trained ResNet model for image classification
# model = models.resnet50(weights=ResNet50_Weights.DEFAULT)
# model = resnet18(weights=ResNet18_Weights.DEFAULT)
# model = mobilenet_v2(weights=MobileNet_V2_Weights.DEFAULT)
# model = models.shufflenet_v2_x1_0(pretrained=True)
model = EfficientNet.from_pretrained('efficientnet-b0')
model.eval()

# Define transformation pipeline for image
transform_pipeline = transforms.Compose([
    transforms.Resize((224, 224)),  # Resize to model's input size
    transforms.ToTensor(),  # Convert to tensor
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])  # Normalization
])

# Set up a connection to the local Cassandra instance
def setup_cassandra_connection():
    cluster = Cluster(['35.91.77.33'], port=9042)
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
from concurrent.futures import ThreadPoolExecutor, as_completed

# Classify all images from each drone table after 30 seconds, and measure CPU/memory utilization
def classify_all_images_after_delay():
    session = setup_cassandra_connection()

    print("Starting classification of all images in each drone table.")

    response_times = []  # List to store the response time for each drone table
    cpu_utilizations = []
    memory_utilizations = []

    # Universal start time
    universal_start_time = time.time()

    def process_table(drone_id):
        table_name = f"drone_{drone_id}"
        try:
            # Query all rows from the current drone's table
            rows = session.execute(f"SELECT * FROM {table_name}")

            # Start timing for this table
            table_start_time = time.time()

            # Classify each image in the table
            for row in rows:
                # Record CPU and memory usage
                cpu_util_per_core = psutil.cpu_percent(interval=None, percpu=True)  # get per-core CPU utilization in %
                mem_util = psutil.virtual_memory().percent  # get memory utilization in %
                cpu_utilizations.append(cpu_util_per_core)
                memory_utilizations.append(mem_util)

                classification_label = classify_image(row.image_data)
                # Print the category name for each classified image
                # category_name = ResNet50_Weights.DEFAULT.meta["categories"][classification_label]
                # category_name = ResNet18_Weights.DEFAULT.meta["categories"][classification_label]
                # category_name = MobileNet_V2_Weights.DEFAULT.meta["categories"][classification_label]
                # category_name = models.shufflenet_v2_x1_0().meta["categories"][classification_label]
                # category_name = EfficientNet._ALLOWED_MODELS['efficientnet-lite0'].meta["categories"][classification_label]
                # print(f"Drone {drone_id} - Image ID {row.id} classified as: {category_name}")

            # End timing for this table
            table_end_time = time.time()
            elapsed_time = table_end_time - universal_start_time  # Use universal start time
            print(f"Response time for {table_name}: {elapsed_time:.2f} seconds")
            return elapsed_time  # Return response time for this table

        except Exception as e:
            print(f"Error querying {table_name}: {str(e)}")
            return None

    # Use ThreadPoolExecutor to process tables concurrently
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_drone = {executor.submit(process_table, drone_id): drone_id for drone_id in range(NUM_DRONES)}

        for future in as_completed(future_to_drone):
            elapsed_time = future.result()
            if elapsed_time is not None:
                response_times.append(elapsed_time)

    # Calculate average response time
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        print(f"Average Response Time across all drone tables: {avg_response_time:.2f} seconds")
    else:
        print("No response times recorded.")

    # Calculate and print average CPU and memory utilization
    avg_cpu_util = [sum(core) / len(core) for core in zip(*cpu_utilizations)]  # average per-core usage
    avg_memory_util = sum(memory_utilizations) / len(memory_utilizations) if memory_utilizations else 0

    # Print average CPU usage for each core
    for i, core_avg in enumerate(avg_cpu_util):
        print(f"Average CPU Utilization for Core {i}: {core_avg:.2f}%")
    print(f"Average Memory Utilization: {avg_memory_util:.2f}%")

if __name__ == "__main__":
    classify_all_images_after_delay()
