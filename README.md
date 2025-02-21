# Fog Computing System Simulation for Smart Warehouse Environment

## Overview
This project simulates a fog computing system with distributed image classification using AWS EC2 instances, Docker, Cassandra, and HAProxy. The system consists of three EC2 instances:

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

### Step 1: Spin up the AWS EC2 instances
- All of these will use the Ubuntu OS
- 2 of them are to be T2.large instances (WorkloadGenerator and Database, respectively). The 3rd one (Classifier instance) is to be m7a.xlarge (4 physical cores).
- Make sure to have relaxed security group rules (i.e. allow all incoming traffic).

### Step 2: Configure the WorkloadGenerator instance (EC2-1)

Run the following commands:

```bash
# Updates package lists and upgrades all installed packages automatically
sudo apt update && sudo apt upgrade -y
```

```bash
# Install necessary packages like git, virtual python env, and pip
sudo apt install -y git python3-venv python3-pip
```

```bash
# Clone the repo
git clone https://github.com/daiwik-swaminathan/Drone-Simulator.git
```

```bash
# Set up Python virtual environment and enter it
python3 -m venv venv
source venv/bin/activate
```

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

