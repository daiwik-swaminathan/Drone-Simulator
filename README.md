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

### Step 1: Spin up the AWS EC2 instances
- All of these will use the Ubuntu OS
- 2 of them are to be T2.large instances (WorkloadGenerator and Database, respectively). The 3rd one (Classifier instance) is to be m7a.xlarge (4 physical cores).
- Make sure to have relaxed security group rules (i.e. allow all incoming traffic).

### Step 2: Configure the Database instance (EC2-2)

#### Cassandra Setup

Run the following commands:

```bash
# Install Docker
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt install docker-ce
```

To verify that Docker is installed correctly, check its status:

```bash
# Verify Docker
sudo systemctl status docker
```

You should see output that shows Docker is active and running. Press q to exit the status screen.

```bash
# Pull the cassandra db container image
sudo docker pull cassandra
```

```bash
# Start the cassandra db container
sudo docker run --name cassandra-container -d -p 9042:9042 cassandra
```

```bash
# Check if cassandra is running
sudo docker ps
```

Optional:

```bash
# This will open the cqlsh shell, where you can execute CQL (Cassandra Query Language) commands.
sudo docker exec -it cassandra-container cqlsh
```

#### HAproxy Setup

```bash
# Install HAProxy
sudo apt update && sudo apt install haproxy -y
# Configure HAProxy (edit /etc/haproxy/haproxy.cfg)
```

### Step 3: Configure the WorkloadGenerator instance (EC2-1)

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
# Enter Drone-Simulator, set up Python virtual environment and enter it
cd Drone-Simulator
python3 -m venv venv
source venv/bin/activate
```

Modify the drone script to use the IP address of the database instance. The drone script will not work as intended otherwise.

```bash
cd Simulators
vi drone_simulator.py
```

Run the drone script:

```bash
python drone_simulator.py
```

It should take a few minutes to finish, depending on the configurations in the script.
