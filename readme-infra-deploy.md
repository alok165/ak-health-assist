# AK Health Assist — Infrastructure & Deployment Guide

Target: EC2 public IP **3.27.238.23**
Container registry: **AWS ECR**
App port: **8501** (Streamlit)

---

## Prerequisites

### Local machine
| Tool | Install |
|---|---|
| Docker Desktop | https://docs.docker.com/get-docker/ |
| AWS CLI v2 | https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html |
| An IAM user with `AmazonEC2ContainerRegistryFullAccess` | AWS Console → IAM |

### On the EC2 instance
- Amazon Linux 2023 / Ubuntu 22.04
- Security group with inbound rules:

| Type | Protocol | Port | Source |
|---|---|---|---|
| SSH | TCP | 22 | Your IP |
| Custom TCP | TCP | 8501 | 0.0.0.0/0 |

---

## 1. Configure AWS CLI (local machine)

```bash
aws configure
# AWS Access Key ID:     <your-access-key>
# AWS Secret Access Key: <your-secret-key>
# Default region name:   ap-southeast-2      # change to your region
# Default output format: json
```

---

## 2. Create an ECR Repository

```bash
# Set your variables
export AWS_REGION=ap-southeast-2          # change if different
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REPO=ak-health-assist

# Create the repository
aws ecr create-repository \
    --repository-name $ECR_REPO \
    --region $AWS_REGION

# Note the repositoryUri from the output, e.g.:
# 123456789012.dkr.ecr.ap-southeast-2.amazonaws.com/ak-health-assist
```

---

## 3. Build the Docker Image (local machine)

```bash
# From the project root (where Dockerfile lives)
cd /path/to/ak-health-assist
 #C:\Users\alok1\GITREPOS\ak-health-assist
docker build -t ak-health-assist .

# Verify the image
docker images | grep ak-health-assist
```

### Test locally before pushing

```bash
docker run --rm -p 8501:8501 \
    --env GOOGLE_API_KEY=your_api_key_here \
    ak-health-assist
```

Open http://localhost:8501 to confirm the app runs correctly.

---

## 4. Push Image to AWS ECR

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS \
    --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Tag the image
docker tag ak-health-assist:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

# Push to ECR
docker push \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
```

Verify in AWS Console → ECR → `ak-health-assist` → Images.

---

## 5. Prepare the EC2 Instance

### 5a. SSH into the instance

```bash
ssh -i your-key.pem ec2-user@3.27.238.23      # Amazon Linux
# or
ssh -i your-key.pem ubuntu@3.27.238.23         # Ubuntu
```

### 5b. Install Docker

**Amazon Linux 2023:**
```bash
sudo dnf update -y
sudo dnf install -y docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user
# Log out and back in for the group change to take effect
```

**Ubuntu 22.04:**
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu
```

### 5c. Install AWS CLI on EC2

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

### 5d. Grant EC2 access to ECR

**Option A (recommended) — IAM Instance Role:**
1. AWS Console → EC2 → Select instance → Actions → Security → Modify IAM role
2. Attach a role with `AmazonEC2ContainerRegistryReadOnly` policy
3. No credentials needed on the instance — role is assumed automatically

**Option B — AWS CLI credentials on EC2:**
```bash
aws configure   # enter access key / secret / region
```

---

## 6. Pull and Run the Container on EC2

```bash
# Set variables on EC2
export AWS_REGION=ap-southeast-2
export AWS_ACCOUNT_ID=<your-12-digit-account-id>
export ECR_REPO=ak-health-assist

# Authenticate Docker to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS \
    --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Pull the image
docker pull $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

# Run the container
docker run -d \
    --name ak-health-assist \
    --restart unless-stopped \
    -p 8501:8501 \
    -e GOOGLE_API_KEY=your_api_key_here \
    -v /home/ec2-user/logs:/app/logs \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
```

> Replace `your_api_key_here` with your Google AI Studio API key.
> The `-v` flag mounts a host directory so audit logs persist outside the container.

---

## 7. Access the App

Open your browser:

```
http://3.27.238.23:8501
```

---

## 8. Useful Management Commands (on EC2)

```bash
# Check running containers
docker ps

# View live logs
docker logs -f ak-health-assist

# Stop the container
docker stop ak-health-assist

# Restart
docker restart ak-health-assist

# Update to a new image version
docker pull $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
docker stop ak-health-assist && docker rm ak-health-assist
# then re-run the docker run command from Step 6
```

---

## 9. Deploying a New Version

Whenever you update the code, repeat these steps on your **local machine**:

```bash
# 1. Rebuild
docker build -t ak-health-assist .

# 2. Re-tag
docker tag ak-health-assist:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

# 3. Push
docker push \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
```

Then on the **EC2 instance**:

```bash
docker pull $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
docker stop ak-health-assist && docker rm ak-health-assist
docker run -d \
    --name ak-health-assist \
    --restart unless-stopped \
    -p 8501:8501 \
    -e GOOGLE_API_KEY=your_api_key_here \
    -v /home/ec2-user/logs:/app/logs \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
```

---

## File Summary

```
ak-health-assist/
├── Dockerfile             # Container definition
├── .dockerignore          # Files excluded from the image
├── readme-infra-deploy.md # This guide
└── ...
```

---

## Security Notes

- Never bake `GOOGLE_API_KEY` into the Docker image. Always pass it at runtime via `-e` or `--env-file`.
- Restrict the EC2 security group port 8501 to known IPs in production.
- Rotate your Google API key periodically in [Google AI Studio](https://aistudio.google.com).
- For production, consider fronting Streamlit with an Nginx reverse proxy on port 80/443 with TLS.
