# GCP GKE Setup with Autoscaling and Load Balancer
This will help you setup you basic GKE with auto scaling enabled.

## Prerequisites
- Google Cloud SDK installed
- A Google Cloud project with appropriate permissions
- Ensure you are logged in via the `gcloud` CLI: `gcloud auth login`
- Set your project ID: `gcloud config set project YOUR_PROJECT_ID`

### Login into google cloud 

```bash
    - gcloud auth configure-docker
```

### Configure your GKE cluster with

```bash
    - gcloud container clusters create [CLUSTER_NAME]
```

### Deploy the application

```bash
    - kubectl apply -f gke-deployment\gke-deployment.yaml
```

### Creating image locally 

```bash
    - docker build -t gcr.io/vcc-deployement/streamlit-app .
```

### Pushing image to google 

```bash
    - docker push gcr.io/vcc-deployment/streamlit-app
```

### Restarting Kubernetics Cluster

```bash
    - kubectl rollout restart deployment streamlit-app-deployment
```

### Contributors

    Gayathri T (G23AI2012) - https://github.com/Gayathiriramalingam2024
    Jeyadev L (G23AI2071) - https://github.com/Jeyadev-2071 / https://github.com/Jeyadev42
    Bratati Rout (G23AI2074) - https://github.com/bratati-rout
    Devasree R (G23AI2078)- https://github.com/DevSr96