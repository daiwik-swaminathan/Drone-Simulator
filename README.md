# Distributed Image Classification System

## Overview
This project simulates a distributed image classification system using AWS EC2 instances, Docker, Cassandra, HAProxy, and Flask. The system consists of three EC2 instances:

1. **Workload Generator (EC2-1)**: Simulates drones sending image data.
2. **Database & Load Balancer (EC2-2)**: Hosts a Cassandra database, HAProxy, and a script for forwarding classification requests.
3. **Image Classifier Nodes (EC2-3)**: Runs multiple Docker containers with the image classifier script.

## Architecture Diagram
```                                                                                                                            
           +-----------------------------+                    +----------------------------------+                             +--------------------------------+
           | Workload Generator (EC2-1)  |    (Image data)    | Database & Load Balancer (EC2-2) |   (Requests via HAProxy)    | Image Classifier Nodes (EC2-3) |
           |  - Drone Simulator (Python) |  --------------->  |  - Cassandra (Docker)            |  ------------------------>  |                                |
           |  - Sends Image Data         |                    |  - push_to_haproxy.py            |                             |    +-----------------------+   |
           +-----------------------------+                    |  - HAProxy                       |                             |    |   Docker Container 1  |   |              
                                                              +----------------------------------+                             |    | - image_classifier.py |   |
                                                                                                                               |    | - Flask server        |   |    
                                                                                                                               |    +-----------------------+   |
                                                                                                                               |                .               |
                                                                                                                               |                .               |
                                                                                                                               |                .               |
                                                                                                                               |    +-----------------------+   |
                                                                                                                               |    |   Docker Container 5  |   | 
                                                                                                                               |    | - image_classifier.py |   |
                                                                                                                               |    | - Flask server        |   |
                                                                                                                               |    +-----------------------+   |
                                                                                                                               |                                |
                                                                                                                               +--------------------------------+
```

## Components
### 1. **Workload Generator (EC2-1)**
- Simulates 1-5 drones sending image data.
- Python script sends images to Cassandra in EC2-2.

### 2. **Database & Load Balancer (EC2-2)**
- Runs a Cassandra database in a Docker container.
- HAProxy balances requests to image classifier nodes.
- `push_to_haproxy.py` forwards processing requests to HAProxy.

### 3. **Image Classifier Nodes (EC2-3)**
- Hosts multiple Docker containers (1-5) running a Flask-based image classifier.
- Pulls images from Cassandra and processes them.

## Setup Instructions
### Prerequisites
- AWS EC2 instances set up with necessary security group rules.
- Docker and Python installed on relevant instances.

### Step 1: Setting Up Cassandra on EC2-2
```bash
# Install and run Cassandra in Docker
sudo docker run --name cassandra-db -d cassandra
```

### Step 2: Running HAProxy on EC2-2
```bash
# Install HAProxy
sudo apt update && sudo apt install haproxy -y
# Configure HAProxy (edit /etc/haproxy/haproxy.cfg)
```

### Step 3: Deploying Image Classifiers on EC2-3
```bash
# Run multiple classifier containers
sudo docker run -d -p 5000:5000 image-classifier
```

## Usage
- Start the workload generator to simulate drones.
- Monitor HAProxy logs to see request distribution.
- Check classifier logs for image processing results.

## Future Improvements
- Implement fault tolerance for EC2 instances.
- Enhance database scalability.
- Use Kubernetes for container orchestration.

