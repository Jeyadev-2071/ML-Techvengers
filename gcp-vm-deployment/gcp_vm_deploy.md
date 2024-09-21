
# GCP VM Setup with Autoscaling and Load Balancer

This guide will help you set up a Virtual Machine (VM), configure a Managed Instance Group (MIG) with autoscaling, and deploy an application with a Load Balancer and an external static IP using Google Cloud Platform (GCP) through the CLI.

## Prerequisites
- Google Cloud SDK installed
- A Google Cloud project with appropriate permissions
- Ensure you are logged in via the `gcloud` CLI: `gcloud auth login`
- Set your project ID: `gcloud config set project YOUR_PROJECT_ID`

## Steps

### 1. Create a VM Instance with a Startup Script

Run the following command to create a VM instance. Replace values as needed.

```bash
gcloud compute instances create my-app-instance     --zone=us-central1-a     --machine-type=e2-standard-2     --boot-disk-size=10GB     --image-family=debian-11     --image-project=debian-cloud     --tags=http-server,https-server     --metadata startup-script='#! /bin/bash
exec > /var/log/startup-script.log 2>&1
set -e
echo "Startup script initiated"
sudo apt-get update
sudo apt install -y git
sudo apt-get install -y python3 python3-pip
git clone https://github.com/Jeyadev-2071/ML-Techvengers.git
cd ML-Techvengers
pip3 install -r requirements.txt
streamlit run app.py --server.port 8501 --server.headless true
echo "Startup script completed"'
```

### 2. Create a VM Instance Template

You can create an instance template to simplify creating multiple VMs later.

```bash
gcloud compute instance-templates create my-app-template     --machine-type=e2-standard-2     --boot-disk-size=20GB     --image-family=debian-10     --image-project=debian-cloud     --metadata startup-script='#! /bin/bash
exec > /var/log/startup-script.log 2>&1
set -e
echo "Startup script initiated"
sudo apt-get update
sudo apt install -y git
sudo apt-get install -y python3 python3-pip
pip3 install streamlit
git clone https://github.com/Jeyadev-2071/ML-Techvengers.git
cd ML-Techvengers
pip3 install -r requirements.txt
streamlit run app.py --server.port 8501 --server.headless true
echo "Startup script completed"'
```

### 3. Create a Managed Instance Group with Autoscaling

After creating an instance template, create a managed instance group and configure autoscaling:

```bash
gcloud compute instance-groups managed create my-app-instance-group     --base-instance-name=my-app-vm     --template=my-app-template     --size=1     --zone=us-central1-a

gcloud compute instance-groups managed set-autoscaling my-app-instance-group     --max-num-replicas=10     --target-cpu-utilization=0.8     --cool-down-period=90     --zone=us-central1-a
```

### 4. Reserve an External Static IP

Reserve a static IP for your load balancer:

```bash
gcloud compute addresses create my-static-ip --region=us-central1
```

Check your reserved IP address:

```bash
gcloud compute addresses describe my-static-ip --region=us-central1
```

### 5. Set Up the Load Balancer with External IP

Set up the backend service for the load balancer:

```bash
gcloud compute backend-services create my-backend-service     --protocol=HTTP     --port-name=http     --health-checks=my-health-check     --global
```

Create a health check:

```bash
gcloud compute health-checks create http my-health-check --port 80
```

Add the instance group to the backend service:

```bash
gcloud compute backend-services add-backend my-backend-service     --instance-group=my-app-instance-group     --instance-group-zone=us-central1-a     --global
```

Create a URL map and target HTTP proxy:

```bash
gcloud compute url-maps create my-url-map     --default-service my-backend-service

gcloud compute target-http-proxies create my-http-proxy     --url-map=my-url-map
```

Create a forwarding rule to route traffic to the load balancer:

```bash
gcloud compute forwarding-rules create my-forwarding-rule     --address=my-static-ip     --global     --target-http-proxy=my-http-proxy     --ports=80
```

### Summary

- The VM is set up with a startup script to deploy your application automatically.
- The instance group is configured with autoscaling based on CPU utilization.
- A load balancer is set up with a reserved external IP to handle incoming traffic.

By running these commands in your terminal, you'll have the entire environment set up via code without using the GUI.

