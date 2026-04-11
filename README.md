# multi-cloud-gitops-platform/hello-world-app/README.md


# Hello World - Multi-Cloud Sample Application

This is a minimal Flask web application that returns a cloud-specific greeting. It is designed to demonstrate a complete multi-cloud CI/CD pipeline:

- Build a Docker image from the application code.
- Push the image to **Amazon ECR** (AWS) and **Azure Container Registry** (Azure) simultaneously.
- Automatically update Kubernetes deployment manifests in a separate GitOps repository.
- Trigger ArgoCD to synchronise the new image version to both AWS EKS and Azure AKS clusters.


## Application Overview

The app (`app.py`) runs a Flask server on port 5000 and responds to `GET /` with:

Hello from <cloud>!

The `<cloud>` value is read from the `CLOUD` environment variable (e.g., `aws` or `azure`). This allows you to distiguish which cloud the pod is running on when you test the deployment.


### Files

File                            Description
`app.py`                        Flask application
`Dockerfile`                    Builds a lightweight Python 3.9 image
`requirements.txt`              Python dependecies (Flask 2.3.3)
`.github/workflows/ci.yml`      Github Actions workflow for build & GitOps update


## CI/CD Pipeline (Github Actions)

The workflow is triggered on every push to the `main` branch (or manually via `workflow_dispatch`). It performs the following steps:

1. **Checkout** the application code.
2. **Set up Docker Buildx** for multi-platform builds.
3. **Authenticate to AWS** (using stored secrets) and login to Amazon ECR.
4. **Authenticate to Azure** (using stored secrets) and login to ACR.
5. **Build and push** the Docker image with two tags (`:latest` and `:<git-sha>`):
    - To AWS ECR: `{account-id}.dkr.ecr.{region}.amazonaws.com/{repo}:{tag}`
    - To Azure ACR: `{acr-name}.azurecr.io/{repo}:{tag}`
6. **Clone the GitOps repository** (separate repo containing Kubernetes manifests).
7. **Update image tags** in `aws/deployment.yaml` and `azure/deployment.yaml` using `yq`.
8. **Commit and push** the changes back to the GitOps repo.
9. (Optional) ArgoCD automatically syncs the changes to the target clusters.

> **Assumptions:** ArgoCD is already installed on both EKS and AKS clusters and is configured to watch the GitOps repository.


## Prerequisites

Before using this pipeline, ensure you have:

### 1. Cloud Infrastructure

- An **AWS EKS cluster** with an ECR repository (see `environments/aws`).
- An **Azure AKS cluster** with an ACR repository (see `environments/azure`).
- The ECR repository name and ACR login server must match the values in the workflow.


### 2. GitOps Repository

A separate GitHub repository (e.g., `kenkaserebe/hello-world-gitops`) containing at least:

aws/
    deployment.yaml

azure/
    deployment.yaml

Each `deployment.yaml` must have a container image field that can be updated by `yq` (typically at `.spec.template.spec.container[0].image`).


### 3. GitHub Secrets

Add the following secrets to your GitHub repository (`hello-world-app`):

Secret Name                     Description
`AWS_ACCESS_KEY_ID`             AWS IAM user key with ECR push permissions
`AWS_SECRET_ACCESS_KEY`         Corresponding secret key
`AZURE_CREDENTIALS`             Azure service principal JSON (for `azure/login@v1`)
`GITOPS_REPO_PAT`               GitHub Personal Access Token (classic) with `repo` scope,
                                used to push to the GitOps repo


## Environment Variables (Workflow)

The workflow uses the following environment variables (defined in `.github/workflows/ci.yml`). Adjust them to match your setup:

Variable                    Purpose
`AWS_REGION`                AWS region (e.g., `eu-west-2`)
`ECR_REPOSITORY`            Name of the ECR repository (e.g., `ken-eks-cluster-app-repo`)
`ACR_REPOSITORY`            Repository name **inside** ACR (e.g., `hello-world`)
`ACR_NAME`                  ACR login server prefix (e.g., `kenaksclusteracr`)
`GITOPS_REPO`               GitOps repository (format: `owner/name`)


## Running the Pipeline Locally (Manual Build)

If you want to build and push manually without GitHub Actions:

bash
# Build the image
docker build -t hello-world .

# Tag for AWS ECR
docker tag hello-world:latest <account-id>.dkr.ecr.<region>.amazonaws.com/<repo>:latest

# Tag for Azure ACR
docker tag hello-world:latest <acr-name>.azurecr.io/<repo>:latest

# Login to both registries
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
az acr login --name <acr-name>

# Push
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/<repo>:latest
docker push <acr-name>.azurecr.io/<repo>:latest


## Testing the Deployed Application

After ArgoCD syncs the changes to the clusters, you can test each cloud deployment.

### On AWS (EKS)

Get the LoadBalancer hostname of the hello-world service:

bash
kubectl get svc hello-world -n default -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

Then curl the URL:

bash
curl http://<hostname>
# Expected output: Hello from aws!


### On Azure (AKS)

Similarly, get the external IP or hostname:

bash
kubectl get svc hello-world -n default -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

bash
curl http://<hostname>
# Expected output: Hello from azure!


## Customisation

Changing the Cloud Identifier

Set the `CLOUD` environment variable in your Kubernetes deployment manifest:

yaml
env:
    - name: CLOUD
      value: "aws"   # or "azure"


### Using Kustomize
If your GitOps repository uses Kustomize, modify the workflow to update the image in kustomization.yaml instead of a raw deployment.yaml.


### Troubleshooting
- Workflow fails on AWS login: Ensure the IAM user has `AmazonEC2ContainerRegistryPowerUser or similar policy.
- Workflow fails on Azure login: Verify the service principal JSON is valid and has `AcrPush` role on the ACR.
- GitOps push fails: The PAT must have `write` access to the GitOps repo. Use a fine-grained token if needed.
- ArgoCD does not sync automatically: Check that ArgoCD is configured to auto-sync (or manually sync via UI/CLI). Also ensure the GitOps repo URL and path are correct in ArgoCD application definitions.


### License

[Specify your license, e.g., MIT]