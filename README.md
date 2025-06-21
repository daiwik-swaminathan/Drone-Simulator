# FLAIR: Fog Layer Architecture with Intelligent Routing

## Overview

FLAIR is a fog-native workload placement framework designed to support low-latency, QoS-aware deployment of classification tasks in smart warehouse environments. It leverages a digital twin simulation to estimate resource impact and a data-driven predictive model (powered by AutoML) to predict response time, enabling intelligent placement decisions without relying on the cloud.

The project simulates this architecture using Amazon EC2 instances for full system emulation.

For more details, see the **"Experiment Setup"** chapter in the Thesis.

---

## System Architecture

FLAIR consists of the following nodes:

- **Drone Emulator (EC2 instance spun up from pre-built AMI)**
  - Runs the `drone_simulator.py` script to simulate drones generating data and sending it to Cassandra.
  - Future versions may simulate additional IoT devices or sensors.

- **Aggregator (EC2 instance spun up from a second AMI)**
  - Hosts:
    - Cassandra (containerized)
    - HAProxy
    - Response Time Model (RTM)
    - Controller, which is composed of:
      - All orchestration scripts (see below)
      - Digital Twin simulation logic
      - Decision making logic

- **Classifier Nodes / Digital Twin (EC2 instances spun up from a third shared AMI)**
  - Nodes where image classification containers are deployed.
  - The same AMI is reused for:
    - Classifier1
    - Classifier2
    - Classifier3
    - Digital Twin instance (sandbox simulator for predicting response time)

---

## Initial Setup

### FLAIR AMI Setup Instructions

These AMIs contain pre-configured environments for reproducing the FLAIR computing setup.

### AMI IDs

| Role            | AMI ID                      |
|------------------|------------------------------|
| Drone Emulator   | ami-045b470df4a52f35f        |
| Aggregator       | ami-06284cc2a72b2ada4        |
| Classifier Node  | ami-082b011c095328a6c        |

These AMIs are **private**. To access them, please send your 12-digit AWS account ID to me. I will manually share the AMIs with your account via EC2 launch permissions.

### Steps to Launch an Instance from an AMI

1. Log into your AWS Console.
2. Go to EC2 → Instances → Launch Instance.
3. Click **Browse more AMIs**.
4. Click the **"Shared with me"** tab.
5. Search for the relevant AMI using the AMI ID (e.g., `ami-045b470df4a52f35f`).
6. Choose the AMI.
7. Select an instance type:
   - Drone Emulator → `t2.large`
   - Aggregator → `t2.large`
   - Digital Twin & Classifier Nodes → `m7a.2xlarge` (REQUIRED)
8. Configure the instance as needed:
   - Open security group ports (use perms from 410)
   - Set appropriate storage (default is OK)
   - Choose an SSH key pair (you must have your own `.pem` file)
9. Click **Launch**.

Repeat this process for:
- One Drone Emulator instance
- One Aggregator instance
- Four Classifier Nodes (3 for live deployment, 1 for digital twin)

### SSH Access

You will need to use your own `.pem` key file to connect to each instance.

Example:
```
ssh -i your-key.pem ubuntu@<public-ip>
```

---

## Drone Emulator Details

Path to simulator script:
```
/Drone-Simulator/Simulators/drone_simulator.py
```

This script sends base64-encoded image data to the Cassandra database, simulating drone behavior. Other devices (sensors, cameras, etc.) can be added here to extend the simulation scope.

---

## Aggregator Scripts

Inside the aggregator instance, you will find the following:

```
ubuntu@ip-172-31-21-191:~$ ls
auto_ml.py   csc570.pem           main_data           rebuild_classifier.sh
automate.sh  generate_dataset.py  push_to_haproxy.py  results.csv
run_requests.sh                   saved_model         use_case_1.py
use_case_2.py                     use_case_3.py       venv/
```

Descriptions:
- `auto_ml.py`: trains the response time prediction model (assumes a CSV file has data ready as input)
- `generate_dataset.py`: generates training data for the model using controlled experiments (parses the log files to make the CSV file)
- `automate.sh`: runs the controlled experiments mentioned above to generate a directory full of log files to parse
- `push_to_haproxy.py`: sends classification requests to HAProxy
- `use_case_1.py/2.py/3.py`: implements experiment logic for each use case
- `rebuild_classifier.sh`: rebuilds classifier Docker images
- `venv/`: contains Python virtual environment
- `saved_model/`: holds the trained model for prediction

---

## HAProxy

HAProxy routes incoming classification requests to available classifier containers. The config is dynamically updated based on the number of containers spun up using the orchestration scripts.

---

## Running Experiments

To run experiments:

```bash
python3 use_case_1.py --rebuild --num-runs 1 
```

This:
- Will simulate the existing and new workloads on the Digital Twin and then see how long the actual response time is when deployed on the Classifier Node
- Rebuild and clean all containers/images before run
- Repeat the runs `num-runs` times

---

## Logs and Results

Logs will be saved in the Aggregator instance, including:
- Log files of CPU/memory usage
- Actual and predicted response times
- Decision outcomes (approve/reject)

---

## Discord Notifications (Optional)

Each `use_case_X.py` script has Discord webhook code **commented out**. If you would like to receive test run summaries via Discord:

- Let me know and I can add you to the FLAIR Discord server.
- Then uncomment the webhook code in the script and insert your Discord webhook URL.

---

---

## Other Notes

For questions, contact: Daiwik Swaminathan
