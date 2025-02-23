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
```

```bash
# Start HAProxy
sudo systemctl start haproxy
```

```bash
# Ensure it is running
sudo systemctl status haproxy
```

Press "q" to leave the status screen/mode.

```bash
# Open and modify HAProxy's config file:
sudo vi /etc/haproxy/haproxy.cfg
```

In this config file add the following to the end of the file:

```bash
frontend http_front
    bind *:8080
    default_backend workers

backend workers
    balance leastconn
    option http-server-close
    option forwardfor

    server worker1 <Classifier_IP>:5000
    #server worker2 <Classifier_IP>:5001
    #server worker3 <Classifier_IP>:5002
    #server worker4 <Classifier_IP>:5003
    #server worker5 <Classifier_IP>:5004
```

This will let HAProxy know about the workers (the classifier containers sitting in the Classifier instance).
Once this has been added, make sure to restart HAProxy:

```bash
sudo systemctl restart haproxy
```

```bash
# Ensure it is running
sudo systemctl status haproxy
```

#### Python Virtual Environment

```bash
# Install packages needed to start a python virtual env
sudo apt install -y python3-venv python3-pip
```

```bash
# Create virtual env (this should be in the root directory of the Database instance).
python3 -m venv venv
```

```bash
# Install the requests library (to be used by the push_to_haproxy.py script):
pip install requests
```

#### push_to_haproxy.py

In the root directory of the Database instance, add this script called `push_to_haproxy.py`:

```python
import requests
import threading
import time

NUM_DRONES = 1  # Number of drones
HAPROXY_URL = 'http://127.0.0.1:8080/classify'  # Replace with HAProxy IP/port

def send_request(drone_id):
    table_name = f"drone_{drone_id}"
    print(f"Drone {drone_id} is starting to send table {table_name}...")  # Print statement at the start

    start_time = time.time()  # Start the timer for this request
    response = requests.post(
        HAPROXY_URL,
        json={"table_name": table_name}
    )
    end_time = time.time()  # End the timer for this request

    elapsed_time = end_time - start_time  # Calculate elapsed time
    print(f"Drone {drone_id} sent table {table_name}, response: {response.status_code}, time taken: {elapsed_time:.2f} seconds")

def send_to_haproxy():
    start_time = time.time()  # Start the timer
    threads = []

    for i in range(NUM_DRONES):  # Launch one thread per drone
        thread = threading.Thread(target=send_request, args=(i,))
        threads.append(thread)
        thread.start()

    for thread in threads:  # Wait for all threads to complete
        thread.join()

    end_time = time.time()  # End the timer
    elapsed_time = end_time - start_time
    print(f"Total time taken to process all requests: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    send_to_haproxy()
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

```bash
# Install needed libraries
pip install cassandra-driver
```

Modify the drone script (line 24) to use the IP address of the database instance. The drone script will not work as intended otherwise.
Ensure that cassandra is running in the other EC2 instance. Feel free to modify the other configurations of the script to vary the workload.
For example, to get 400 images to be in every table, you could modify the sleep statement on line 90 to be 3 seconds and modify the 
simulation_duration variable on line 97 to be 1200 (seconds). This way, there will be 20 images put into every table every 1 minute. The script
would run for a total of 20 minutes. Thus, 20 images per min and running for 20 min will end up having 400 images per table in the end.

```bash
cd Simulators
vi drone_simulator.py
```

Run the drone script:

```bash
python drone_simulator.py
```

It should take a few minutes to finish, depending on the configurations in the script.

### Step 4: Configure the Classifier instance (EC2-3)

```bash
# Updates package lists and upgrades all installed packages automatically
sudo apt update && sudo apt upgrade -y
```

```bash
# Install git
sudo apt install -y git
```

```bash
# Install collectl
sudo apt install collectl
```

```bash
# Verify collectl installation
collectl --version
```

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

#### Building our own docker container

We need to build our own docker containers that run the image classifier script:

```bash
# Clone the repo
git clone https://github.com/daiwik-swaminathan/Drone-Simulator.git
```

```bash
# Navigate to the appropriate directory
cd Drone-Simulator/Classifiers
```

Modify the image classifier script (line 27) to use the IP address of the database instance. The image classifier script will not work as intended otherwise.

```bash
vi image_classifier.py
```

```bash
# Build the container image after making the IP address change from above
sudo docker build -t class-image .
```

The above command should take a few seconds to build the image. Once it is done, launch the 5 containers:

```bash
sudo docker run --name classifier1 -p 5000:5000 -d class-image
sudo docker run --name classifier2 -p 5001:5000 -d class-image
sudo docker run --name classifier3 -p 5002:5000 -d class-image
sudo docker run --name classifier4 -p 5003:5000 -d class-image
sudo docker run --name classifier5 -p 5004:5000 -d class-image
```

```bash
# Stop the containers
sudo docker stop $(sudo docker ps -q)
```

Add this script called "run_containers.sh" to the root directory of your instance:

```bash
#!/bin/bash

# Number of containers to run
NUM_CONTAINERS=1

# Starting port number
START_PORT=5000

# Create and start containers
for i in $(seq 1 $NUM_CONTAINERS); do
    NAME="classifier$i"
    HOST_PORT=$((START_PORT + i - 1))
    sudo docker start "$NAME"
    echo "Started container $NAME on port $HOST_PORT"
done
```

Give executable perms to the above script:

```bash
chmod +x run_containers.sh
```

This script will start (not create) the classifier containers. To see more about when/how to use this script, see step 5.

### Step 5: Running Experiments

#### Pre-requisites

The following needs to have been done prior to any experimentation being possible:
1) The drone_simulator.py script must have run successfully with the expected number of images sitting in each of the drone tables in cassandra. Note that for running tests, the WorkloadGenerator instance does not need to be active.
2) The Database instance is active and has both cassandra and HAProxy running (ensure HAProxy's config file has the right IP of the Classifier instance and has been restarted).
3) The Classifier instance has 5 containers that are currently stopped (not actively running nor removed). I.e if you run `sudo docker ps`, nothing should show up.
4) The Classifier instance should have the script `run_containers.sh` in its root directory.
5) The Database instance should have a Python virtual environment ready to use.
6) The Database instance should have the script `push_to_haproxy.py` in its root directory.

#### Setup

You will need 3 terminals open:
1) One for running collectl on the Classifier instance (Terminal A)
2) One for starting and stopping the classifier containers on the Classifier instance (Terminal B)
3) One for modifying push_to_haproxy.py and /etc/haproxy/haproxy.cfg on the Database instance (Terminal C)

#### Sample test walkthrough

Suppose you would like to run a test with 1 classifer container running. Here are the steps you would need to do:

1) Start the Python virtual environment in the Database instance via this command: `source venv/bin/activate`.
2) Modify the `NUM_CONTAINERS` constant at the top of the `run_containers.sh` script to `1`. Recall this script lives in the Classifier instance.
3) Modify the `NUM_DRONES` constant at the top of the `push_to_haproxy.py` script to `1`.
4) Open `/etc/haproxy/haproxy.cfg` in the Database instance and ensure only worker1 is active (worker2 ... worker5 should be commented out).
5) Run `sudo systemctl restart haproxy` in the Database instance.
6) Run `collectl -sCD` on the Classifer instance (Terminal A).
7) Run `./run_containers` on the Classifier instance (Terminal B). You should observe a spike in CPU usage (via collectl output) due to the containers being started.
8) When the CPU usage falls back to 0, run `python push_to_haproxy.py` in the Database instance (Terminal C). You should observe a spike in CPU usage (via collectl output) due to the containers processing the incoming workload.
9) When `push_to_haproxy` is done, it will output the response times of each request (drone table classification).
10) Stop the collectl command (via ctrl-c) (Terminal A).
11) Run `sudo docker stop $(sudo docker ps -q)` in the same terminal you ran `./run_containers` (Terminal B).
12) Note down the outputs of the collectl command and the response times. I like to copy and paste them into local files on my computer and use a local script to parse them.

For subsequent tests with the same number of drones, you only need to repeat steps 6-12.

For tests where you want to change the number of drones, you need to repeat steps 2-12.
