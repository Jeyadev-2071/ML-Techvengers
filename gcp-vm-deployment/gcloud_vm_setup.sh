# Login using gcloud cli
gcloud auth login
gcloud config set project YOUR_PROJECT_ID ## <---- replace this with your project id

# Creating VM Instance 
gcloud compute instances create my-app-instance  ## replace the name based on you requirement
    --zone=us-central1-a ## replace the zone based on you requirement
    --machine-type=e2-standard-2  ## replace the machine type based on you requirement
    --boot-disk-size=10GB  ## replace the boot disk based on you requirement
    --image-family=debian-11  ## replace the image family based on you requirement
    --image-project=debian-cloud  ## replace the project based on you requirement
    --tags=http-server,https-server ## replace the tags based on you requirement
    --metadata startup-script='#! /bin/bash ## <---- Replace this to start up kit based on your application
exec > /var/log/startup-script.log 2>&1
set -e
echo "Startup script initiated"
sudo apt-get update
sudo apt install -y git
sudo apt-get install -y python3 python3-pip
git clone https://github.com/Jeyadev-2071/ML-Techvengers.git  ## <---- Replace this to your repo
cd ML-Techvengers
pip3 install -r requirements.txt
streamlit run app.py --server.port 8501 --server.headless true
echo "Startup script completed"'

# Creating a VM instance template instead of creating a single vm

gcloud compute instance-templates create my-app-template  ## replace the name based on you requirement
    --machine-type=e2-standard-2 ## replace the machine type based on you requirement
    --boot-disk-size=20GB  ## replace the boot disk based on you requirement
    --image-family=debian-10  ## replace the image family based on you requirement
    --image-project=debian-cloud ## replace the project based on you requirement
    --metadata startup-script='#! /bin/bash ## <---- Replace this to start up kit based on your application
exec > /var/log/startup-script.log 2>&1
set -e
echo "Startup script initiated"
sudo apt-get update
sudo apt install -y git
sudo apt-get install -y python3 python3-pip
pip3 install streamlit
git clone https://github.com/Jeyadev-2071/ML-Techvengers.git ## <---- Replace this to your repo
cd ML-Techvengers
pip3 install -r requirements.txt
streamlit run app.py --server.port 8501 --server.headless true
echo "Startup script completed"'


# Creating a Managed Instance Group MIG with autoscaling

gcloud compute instance-groups managed create my-app-instance-group ## replace the name based on you requirement
    --base-instance-name=my-app-vm  ## replace the name based on you requirement
    --template=my-app-template  ## replace the name based on you requirement
    --size=1  ## replace the size based on you requirement
    --zone=us-central1-a  ## replace the zone based on you requirement

gcloud compute instance-groups managed set-autoscaling my-app-instance-group 
    --max-num-replicas=10  ## replace the replicas number based on you requirement
    --target-cpu-utilization=0.8  ## replace the thershold based on you requirement
    --cool-down-period=90   ## replace the cool down period based on you requirement
    --zone=us-central1-a ## replace the zone based on you requirement

# Reserving External Static IP

gcloud compute addresses create my-static-ip --region=us-central1

# Check your reserved IP

gcloud compute addresses describe my-static-ip --region=us-central1

#  Set Up the Load Balancer with External IP

gcloud compute backend-services create my-backend-service 
    --protocol=HTTP 
    --port-name=http 
    --health-checks=my-health-check 
    --global

# Create a health check:

gcloud compute health-checks create http my-health-check --port 80

# Add the instance group to the backend service:

gcloud compute backend-services add-backend my-backend-service 
    --instance-group=my-app-instance-group 
    --instance-group-zone=us-central1-a 
    --global

# Create a URL map and target HTTP proxy:

gcloud compute url-maps create my-url-map \
    --default-service my-backend-service

gcloud compute target-http-proxies create my-http-proxy \
    --url-map=my-url-map

# Create a forwarding rule to route traffic to the load balancer:

gcloud compute forwarding-rules create my-forwarding-rule \
    --address=my-static-ip \
    --global \
    --target-http-proxy=my-http-proxy \
    --ports=80


# Summary
# The VM is set up with a startup script to deploy your application automatically.
# The instance group is configured with autoscaling based on CPU utilization.
# A load balancer is set up with a reserved external IP to handle incoming traffic.
# By running these commands in your terminal, you'll have the entire environment set up via code without using the GUI.