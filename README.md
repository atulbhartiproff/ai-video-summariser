# AI Video Summarizer

A full-stack web application that allows users to upload videos, extract transcripts, and generate AI-powered summaries using Google's Gemini API. Built with React (Vite + Tailwind), FastAPI, and Docker.

## 🎯 Features

- **Drag & Drop Upload**: Intuitive video upload interface
- **AI-Powered Summaries**: Uses Google Gemini 1.5 Flash for fast, accurate summaries
- **Clean UI**: Minimal, Apple Notes-style card layout
- **Progress Tracking**: Real-time upload and processing progress
- **Dockerized**: Ready for local development and AWS ECS deployment

## 🏗️ Architecture

- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI (Python)
- **AI**: Google Gemini API
- **Storage**: Local temporary files (cleaned up after processing)
- **Deployment**: Docker containers for AWS ECS Fargate

## 📁 Project Structure

```
ai-video-summarizer/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── UploadBox.jsx
│   │   │   └── SummaryCard.jsx
│   │   ├── api.js
│   │   ├── main.jsx
│   │   └── index.css
│   ├── vite.config.js
│   ├── package.json
│   ├── Dockerfile
│   └── tailwind.config.js
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🚀 Quick Start (Local Development)

### Prerequisites

- Docker and Docker Compose installed
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-video-summarizer
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   VITE_API_URL=http://localhost:5000
   MAX_FILE_SIZE_MB=500
   ```

3. **Start the application**
   ```bash
   docker compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost:5000
   - Health Check: http://localhost:5000/health

### Testing

Test the backend directly:
```bash
curl -X POST -F "file=@your-video.mp4" http://localhost:5000/api/upload
```

## 🐳 Docker Commands

```bash
# Build and start all services
docker compose up --build

# Start in detached mode
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild specific service
docker compose build frontend
docker compose build backend
```

## ☁️ Deploy on AWS ECS (Fargate)

> **🎉 Good News**: The frontend now uses **runtime configuration** via nginx reverse proxy! You don't need to know the backend URL at build time. The frontend uses relative URLs, and nginx proxies API calls to the backend using the `BACKEND_URL` environment variable set at container startup.

### Step 1: Build and Push Docker Images to ECR

1. **Create ECR repositories** (if not exists):
   ```bash
   aws ecr create-repository --repository-name ai-video-frontend --region ap-southeast-2
   aws ecr create-repository --repository-name ai-video-backend --region ap-southeast-2
   ```

2. **Authenticate Docker to ECR**:
   ```bash
   aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 899673281251.dkr.ecr.ap-southeast-2.amazonaws.com
   ```

3. **Build and tag images**:
   
   **No build-time configuration needed!** The frontend uses relative URLs and nginx reverse proxy.
   
   ```bash
   # Build frontend (no VITE_API_URL needed - uses runtime config)
   docker build -t ai-video-frontend ./frontend
   docker tag ai-video-frontend:latest 899673281251.dkr.ecr.ap-southeast-2.amazonaws.com/ai-video-frontend:latest
   
   # Build backend
   docker build -t ai-video-backend ./backend
   docker tag ai-video-backend:latest 899673281251.dkr.ecr.ap-southeast-2.amazonaws.com/ai-video-backend:latest
   ```
   
   **How it works**: 
   - Frontend makes API calls to relative URLs (e.g., `/api/upload`)
   - Nginx in the frontend container proxies these to the backend
   - Backend URL is configured at runtime via `BACKEND_URL` environment variable
   - This means you can build once and deploy anywhere!

4. **Push images to ECR**:
   ```bash
   docker push 899673281251.dkr.ecr.ap-southeast-2.amazonaws.com/ai-video-frontend:latest
   docker push 899673281251.dkr.ecr.ap-southeast-2.amazonaws.com/ai-video-backend:latest
   ```

### Step 2: Create ECS Task Definition

A task definition is a blueprint for your containers. It specifies which containers to run, their configuration, and how they work together.

#### 2.1: Get Your AWS Account ID

You'll need your account ID for the Secrets Manager ARN. Get it with:

```bash
aws sts get-caller-identity --query Account --output text
```

Or find it in the AWS Console (top right corner, next to your username).

#### 2.2: Create Task Definition via AWS Console

**Step-by-step:**

1. **Navigate to ECS:**
   - Go to **ECS** → **Task Definitions** → **Create new Task Definition**

2. **Configure Task Definition:**
   - **Task definition family:** `ai-video-summarizer`
   - **Launch type:** AWS Fargate
   - **Operating system/Architecture:** Linux/X86_64
   - **Task size:**
     - **CPU:** `1 vCPU` (1024)
     - **Memory:** `2 GB` (2048)
     - *Note: Video processing is resource-intensive. For larger files, consider 2 vCPU / 4 GB*

3. **Add Backend Container:**
   - Click **Add container**
   - **Container name:** `backend`
   - **Image URI:** `899673281251.dkr.ecr.ap-southeast-2.amazonaws.com/ai-video-backend:latest`
   - **Essential container:** ✅ Yes
   - **Memory limits (MiB):** `1024` (half of task memory)
   - **Port mappings:**
     - **Container port:** `5000`
     - **Protocol:** `TCP`
   - **Environment variables:**
     - `PORT` = `5000`
     - `MAX_FILE_SIZE_MB` = `500`
   - **Secrets:**
     - Click **Add secret**
     - **Key:** `GEMINI_API_KEY`
     - **Value from:** Select your secret ARN (e.g., `arn:aws:secretsmanager:ap-southeast-2:899673281251:secret:ai-video-gemini-key`)
   - **Logging:**
     - **Log driver:** `awslogs`
     - **Log group:** `/ecs/ai-video-summarizer`
     - **Region:** `ap-southeast-2`
     - **Stream prefix:** `backend`
   - Click **Add**

4. **Add Frontend Container:**
   - Click **Add container**
   - **Container name:** `frontend`
   - **Image URI:** `899673281251.dkr.ecr.ap-southeast-2.amazonaws.com/ai-video-frontend:latest`
   - **Essential container:** ✅ Yes
   - **Memory limits (MiB):** `512` (remaining memory)
   - **Port mappings:**
     - **Container port:** `80`
     - **Protocol:** `TCP`
   - **Environment variables:**
     - `BACKEND_URL` = `http://localhost:5000`
   - **Container dependencies:**
     - Click **Add dependency**
     - **Container name:** `backend`
     - **Condition:** `START`
   - **Logging:**
     - **Log driver:** `awslogs`
     - **Log group:** `/ecs/ai-video-summarizer`
     - **Region:** `ap-southeast-2`
     - **Stream prefix:** `frontend`
   - Click **Add**

5. **Review and Create:**
   - Review all settings
   - Click **Create**

#### 2.3: Create Task Definition via CLI (JSON File)

**Step 1: Get your account ID**
```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"
```

**Step 2: Get Secrets Manager ARN**

**Option A - If secret already exists:**
```bash
# Get the full ARN
SECRET_ARN=$(aws secretsmanager describe-secret \
  --secret-id ai-video-gemini-key \
  --region ap-southeast-2 \
  --query 'ARN' \
  --output text)
echo "Secret ARN: $SECRET_ARN"
```

**Option B - Construct ARN manually:**
```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SECRET_ARN="arn:aws:secretsmanager:ap-southeast-2:${ACCOUNT_ID}:secret:ai-video-gemini-key"
echo "Secret ARN: $SECRET_ARN"
```

**Note:** If the secret doesn't exist yet, create it first (see Step 3), then use Option A to get the exact ARN (which includes a random suffix).

**Step 3: Create task-definition.json**

Create a file named `task-definition.json`:

```json
{
  "family": "ai-video-summarizer",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "899673281251.dkr.ecr.ap-southeast-2.amazonaws.com/ai-video-backend:latest",
      "essential": true,
      "memory": 1024,
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "PORT",
          "value": "5000"
        },
        {
          "name": "MAX_FILE_SIZE_MB",
          "value": "500"
        }
      ],
      "secrets": [
        {
          "name": "GEMINI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:ap-southeast-2:899673281251:secret:ai-video-gemini-key-XXXXXX"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-video-summarizer",
          "awslogs-region": "ap-southeast-2",
          "awslogs-stream-prefix": "backend"
        }
      }
    },
    {
      "name": "frontend",
      "image": "899673281251.dkr.ecr.ap-southeast-2.amazonaws.com/ai-video-frontend:latest",
      "essential": true,
      "memory": 512,
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "BACKEND_URL",
          "value": "http://localhost:5000"
        }
      ],
      "dependsOn": [
        {
          "containerName": "backend",
          "condition": "START"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-video-summarizer",
          "awslogs-region": "ap-southeast-2",
          "awslogs-stream-prefix": "frontend"
        }
      }
    }
  ]
}
```

**Important Notes:**
- Replace `899673281251` with your actual AWS account ID
- Secrets Manager ARNs include a random suffix (e.g., `-XXXXXX`). After creating the secret (Step 3), use `aws secretsmanager describe-secret` to get the exact ARN
- The ARN format is: `arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:SECRET_NAME-SUFFIX`

**Step 4: Register the task definition**
```bash
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json \
  --region ap-southeast-2
```

**Step 5: Verify task definition**
```bash
aws ecs describe-task-definition \
  --task-definition ai-video-summarizer \
  --region ap-southeast-2 \
  --query 'taskDefinition.{Family:family,Revision:revision,Status:status,CPU:cpu,Memory:memory}'
```

#### 2.4: Understanding Task Definition Fields

**Task-level settings:**
- **family**: Name of the task definition (used for versioning)
- **networkMode**: `awsvpc` required for Fargate (each task gets its own network interface)
- **requiresCompatibilities**: `["FARGATE"]` for serverless containers
- **cpu**: Total CPU units (256, 512, 1024, 2048, 4096, 8192, 16384)
- **memory**: Total memory in MB (512, 1024, 2048, 4096, 8192, 16384, 30720)

**CPU/Memory combinations for Fargate:**
- 256 CPU → 512, 1024, 2048 MB
- 512 CPU → 1024, 2048, 3072, 4096 MB
- 1024 CPU → 2048, 3072, 4096, 5120, 6144, 7168, 8192 MB
- 2048 CPU → 4096 to 16384 MB (in 1GB increments)
- 4096 CPU → 8192 to 30720 MB (in 1GB increments)

**Container-level settings:**
- **name**: Container identifier (must be unique in task)
- **image**: Docker image URI from ECR
- **essential**: If true, task stops if this container stops
- **memory**: Memory limit for this container (must be ≤ task memory)
- **portMappings**: Container ports to expose
- **environment**: Plain text environment variables
- **secrets**: Environment variables from AWS Secrets Manager
- **dependsOn**: Container startup order
- **logConfiguration**: Where to send container logs

#### 2.5: Update Task Definition

**To update a task definition:**

1. **Via Console:**
   - Go to **ECS** → **Task Definitions** → Select `ai-video-summarizer` → **Create new revision**
   - Make your changes
   - Click **Create**

2. **Via CLI:**
   ```bash
   # Modify task-definition.json with your changes
   # Then register new revision
   aws ecs register-task-definition \
     --cli-input-json file://task-definition.json \
     --region ap-southeast-2
   ```

**Note:** New revisions are automatically created. Services will use the latest revision unless you specify a version.

#### 2.6: Common Task Definition Configurations

**For small videos (< 100MB):**
```json
"cpu": "512",
"memory": "2048"
```

**For medium videos (100-500MB) - Recommended:**
```json
"cpu": "1024",
"memory": "2048"
```

**For large videos (> 500MB):**
```json
"cpu": "2048",
"memory": "4096"
```

**For high-throughput (multiple concurrent requests):**
```json
"cpu": "4096",
"memory": "8192"
```

#### 2.7: Troubleshooting Task Definition Issues

1. **"Invalid CPU or memory value"**
   - Check that CPU/memory combination is valid for Fargate
   - Use the combinations listed in section 2.4

2. **"Container memory exceeds task memory"**
   - Sum of all container memory limits must be ≤ task memory
   - Backend: 1024 MB + Frontend: 512 MB = 1536 MB ≤ 2048 MB ✓

3. **"Secrets Manager ARN not found" or "API key not valid"**
   - **Verify the secret exists:**
     ```bash
     aws secretsmanager describe-secret --secret-id ai-video-gemini-key --region ap-southeast-2
     ```
   - **Get the correct ARN (includes random suffix):**
     ```bash
     aws secretsmanager describe-secret \
       --secret-id ai-video-gemini-key \
       --region ap-southeast-2 \
       --query 'ARN' \
       --output text
     ```
   - **Verify the secret value is correct (plain string, not JSON):**
     ```bash
     # Check if it's stored correctly
     aws secretsmanager get-secret-value \
       --secret-id ai-video-gemini-key \
       --region ap-southeast-2 \
       --query 'SecretString' \
       --output text
     ```
   - **Common mistakes:**
     - Secret stored as JSON `{"key": "value"}` instead of plain string
     - Wrong ARN in task definition (missing or incorrect suffix)
     - API key copied incorrectly (extra spaces, missing characters)
   - **Check ECS task can read the secret:**
     - Verify task execution role has `secretsmanager:GetSecretValue` permission
     - Check CloudWatch logs for backend container to see if API key is loaded
   - **Update task definition with correct ARN:**
     - Use the ARN from `describe-secret` command (includes `-XXXXXX` suffix)
     - Register new task definition revision
     - Force service deployment

4. **"Image not found"**
   - Verify image exists in ECR: `aws ecr describe-images --repository-name ai-video-backend --region ap-southeast-2`
   - Check image URI matches exactly (including tag)

5. **"Log group does not exist"**
   - Create log group first (see Step 4.1)
   - Or ECS will create it automatically, but you may see initial errors

### Step 3: Store Gemini API Key in AWS Secrets Manager

**Important:** The API key must be stored as a plain string value, not JSON.

**Option A - Create new secret:**
```bash
aws secretsmanager create-secret \
  --name ai-video-gemini-key \
  --secret-string "your-actual-gemini-api-key-here" \
  --region ap-southeast-2
```

**Option B - Update existing secret:**
```bash
aws secretsmanager update-secret \
  --secret-id ai-video-gemini-key \
  --secret-string "your-actual-gemini-api-key-here" \
  --region ap-southeast-2
```

**Verify the secret:**
```bash
# Get the secret ARN (needed for task definition)
aws secretsmanager describe-secret \
  --secret-id ai-video-gemini-key \
  --region ap-southeast-2 \
  --query 'ARN' \
  --output text

# Verify the secret value (first 10 chars only)
aws secretsmanager get-secret-value \
  --secret-id ai-video-gemini-key \
  --region ap-southeast-2 \
  --query 'SecretString' \
  --output text | head -c 10
```

**Common Issues:**
- ❌ **Don't store as JSON:** The secret should be a plain string, not `{"key": "value"}`
- ✅ **Correct format:** Just the API key string itself: `AIzaSy...`
- ✅ **Get your API key from:** https://aistudio.google.com/app/apikey

### Step 4: Create ECS Service

#### 4.1: Create CloudWatch Log Group

```bash
aws logs create-log-group --log-group-name /ecs/ai-video-summarizer --region ap-southeast-2
```

#### 4.2: Create ECS Cluster (if not exists)

**Option A - Via AWS Console:**
1. Go to **ECS** → **Clusters** → **Create Cluster**
2. Select **AWS Fargate (serverless)**
3. Cluster name: `ai-video-summarizer-cluster`
4. Click **Create**

**Option B - Via CLI:**
```bash
aws ecs create-cluster \
  --cluster-name ai-video-summarizer-cluster \
  --region ap-southeast-2
```

#### 4.3: Create Security Group

The security group needs to allow:
- **Port 80** (HTTP) - for frontend access
- **Port 443** (HTTPS) - if using SSL/TLS (optional)
- **Port 5000** - only if you want direct backend access (not required with nginx proxy)

**Via AWS Console:**
1. Go to **VPC** → **Security Groups** → **Create security group**
2. Name: `ai-video-summarizer-sg`
3. Description: `Security group for AI Video Summarizer ECS service`
4. VPC: Select your VPC
5. **Inbound rules:**
   - Type: `HTTP`, Port: `80`, Source: `0.0.0.0/0` (or your IP range)
   - Type: `HTTPS`, Port: `443`, Source: `0.0.0.0/0` (optional, for SSL)
6. **Outbound rules:** Leave default (all traffic)
7. Click **Create security group**

**Via CLI:**
```bash
# Get your VPC ID first
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region ap-southeast-2)

# Create security group
SG_ID=$(aws ec2 create-security-group \
  --group-name ai-video-summarizer-sg \
  --description "Security group for AI Video Summarizer ECS service" \
  --vpc-id $VPC_ID \
  --region ap-southeast-2 \
  --query 'GroupId' --output text)

# Add inbound rule for HTTP
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region ap-southeast-2
```

#### 4.4: Create ECS Service

**Option A - Via AWS Console (Recommended for first-time setup):**

1. **Navigate to ECS:**
   - Go to **ECS** → **Clusters** → Select your cluster → **Services** tab → **Create**

2. **Configure Service:**
   - **Launch type:** AWS Fargate
   - **Task Definition:** Select `ai-video-summarizer` (the one you registered)
   - **Service name:** `ai-video-summarizer-service`
   - **Number of tasks:** `1` (increase for high availability)
   - **Deployment configuration:** 
     - **Minimum healthy percent:** `100`
     - **Maximum percent:** `200`

3. **Configure Network:**
   - **VPC:** Select your VPC
   - **Subnets:** 
     - For public access: Select **public subnets** (have Internet Gateway)
     - For private: Select **private subnets** (must have NAT Gateway)
   - **Security groups:** Select `ai-video-summarizer-sg` (created above)
   - **Auto-assign public IP:** 
     - **ENABLED** if using public subnets
     - **DISABLED** if using private subnets with NAT

4. **Load Balancing (Optional but Recommended):**
   - **Load balancer type:** Application Load Balancer
   - **Load balancer name:** `ai-video-summarizer-alb` (or create new)
   - **Container to load balance:**
     - **Container name:** `frontend`
     - **Port:** `80`
   - **Listener:**
     - **Port:** `80`
     - **Protocol:** `HTTP`
   - **Target group:**
     - Create new target group: `ai-video-summarizer-tg`
     - **Target type:** `IP`
     - **Protocol:** `HTTP`
     - **Port:** `80`
     - **Health check path:** `/` (or `/health` if you add it to frontend)

5. **Service Auto Scaling (Optional):**
   - Enable auto scaling if you want automatic scaling based on CPU/memory
   - **Min capacity:** `1`
   - **Max capacity:** `10`
   - **Target tracking:** CPU utilization at 70%

6. **Review and Create:**
   - Review all settings
   - Click **Create**

**Option B - Via AWS CLI:**

```bash
# Set variables
CLUSTER_NAME="ai-video-summarizer-cluster"
SERVICE_NAME="ai-video-summarizer-service"
TASK_DEFINITION="ai-video-summarizer"
SUBNET_IDS="subnet-xxxxx,subnet-yyyyy"  # Replace with your subnet IDs
SECURITY_GROUP_ID="sg-xxxxx"  # Replace with your security group ID

# Create service without load balancer (simpler setup)
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name $SERVICE_NAME \
  --task-definition $TASK_DEFINITION \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
  --region ap-southeast-2
```

**Option C - Via AWS CLI with Load Balancer:**

First, create the load balancer and target group:

```bash
# Variables
VPC_ID="vpc-xxxxx"  # Your VPC ID
SUBNET_IDS="subnet-xxxxx,subnet-yyyyy"  # Your public subnet IDs
SECURITY_GROUP_ID="sg-xxxxx"  # Your security group ID

# Create Application Load Balancer
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name ai-video-summarizer-alb \
  --subnets $SUBNET_IDS \
  --security-groups $SECURITY_GROUP_ID \
  --region ap-southeast-2 \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --region ap-southeast-2 \
  --query 'LoadBalancers[0].DNSName' --output text)

echo "ALB DNS: $ALB_DNS"

# Create target group
TG_ARN=$(aws elbv2 create-target-group \
  --name ai-video-summarizer-tg \
  --protocol HTTP \
  --port 80 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-path / \
  --region ap-southeast-2 \
  --query 'TargetGroups[0].TargetGroupArn' --output text)

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN \
  --region ap-southeast-2

# Create ECS service with load balancer
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name $SERVICE_NAME \
  --task-definition $TASK_DEFINITION \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=frontend,containerPort=80" \
  --region ap-southeast-2
```

#### 4.5: Verify Service Status

**Check service status:**
```bash
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region ap-southeast-2 \
  --query 'services[0].{Status:status,RunningCount:runningCount,DesiredCount:desiredCount}'
```

**View service logs:**
```bash
# Frontend logs
aws logs tail /ecs/ai-video-summarizer --follow --region ap-southeast-2 --filter-pattern "frontend"

# Backend logs
aws logs tail /ecs/ai-video-summarizer --follow --region ap-southeast-2 --filter-pattern "backend"
```

#### 4.6: Access the Application

**If using Application Load Balancer:**
```bash
# Get ALB DNS name
aws elbv2 describe-load-balancers \
  --region ap-southeast-2 \
  --query 'LoadBalancers[?LoadBalancerName==`ai-video-summarizer-alb`].DNSName' \
  --output text
```
Access at: `http://<alb-dns-name>` (e.g., `http://ai-video-summarizer-alb-123456789.ap-southeast-2.elb.amazonaws.com`)

**If using public IP (no load balancer):**
```bash
# Get task public IP
aws ecs list-tasks --cluster $CLUSTER_NAME --service-name $SERVICE_NAME --region ap-southeast-2

# Get task details (including network interfaces)
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name $SERVICE_NAME --region ap-southeast-2 --query 'taskArns[0]' --output text)

# Get ENI ID and then public IP from EC2
ENI_ID=$(aws ecs describe-tasks --cluster $CLUSTER_NAME --tasks $TASK_ARN --region ap-southeast-2 --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)

PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --region ap-southeast-2 --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

echo "Access at: http://$PUBLIC_IP"
```

#### 4.7: Important Notes

**Backend URL Configuration:**
- Since both containers are in the same ECS task, the `BACKEND_URL` in the task definition uses `http://localhost:5000`
- The frontend nginx will proxy `/api/*` requests to the backend container
- **No need to expose backend port 5000 publicly** - nginx handles the routing internally
- Only port 80 (frontend) needs to be accessible from the internet

**Troubleshooting:**

1. **Service won't start:**
   - Check CloudWatch logs: `/ecs/ai-video-summarizer`
   - Verify task definition is registered correctly
   - Check security group allows outbound traffic
   - Verify subnets have internet access (for public subnets) or NAT Gateway (for private)

2. **Can't access application:**
   - Verify security group allows inbound on port 80
   - Check if public IP is assigned (if not using ALB)
   - Verify ALB target group health checks are passing
   - Check ECS service events for errors

3. **Backend connection errors:**
   - Verify `BACKEND_URL` environment variable is set correctly in task definition
   - Check that both containers are running in the same task
   - Review nginx logs in frontend container

4. **Nginx "invalid URL prefix" error:**
   - **Cause:** `BACKEND_URL` environment variable is not set or empty in the frontend container
   - **Solution:** 
     - Verify `BACKEND_URL` is set in the ECS task definition for the frontend container
     - Check task definition: `aws ecs describe-task-definition --task-definition ai-video-summarizer --region ap-southeast-2 --query 'taskDefinition.containerDefinitions[?name==`frontend`].environment'`
     - Ensure value is `http://localhost:5000` (for containers in same task) or the backend's internal URL
     - Rebuild and redeploy the service after fixing the task definition
   - **Quick fix command:**
     ```bash
     # Update the task definition to add BACKEND_URL if missing
     # Then force a new deployment
     aws ecs update-service \
       --cluster ai-video-summarizer-cluster \
       --service ai-video-summarizer-service \
       --force-new-deployment \
       --region ap-southeast-2
     ```

5. **413 Request Entity Too Large error:**
   - **Cause:** Nginx default upload limit is 1MB, which is too small for video files
   - **Solution:** The nginx configuration has been updated to allow 500MB uploads
   - If you need larger files, update `client_max_body_size` in the frontend Dockerfile nginx config
   - Also ensure backend `MAX_FILE_SIZE_MB` environment variable matches (default: 500MB)

6. **High memory/CPU usage:**
   - Video processing is resource-intensive
   - Consider increasing task CPU/memory in task definition
   - Enable auto-scaling for multiple concurrent requests

## 🔧 Environment Variables

### Backend
- `GEMINI_API_KEY` (required): Your Google Gemini API key
- `PORT` (default: 5000): Backend server port
- `MAX_FILE_SIZE_MB` (default: 500): Maximum upload file size in MB

### Frontend
- `BACKEND_URL` (default: http://localhost:5000): Backend URL for nginx reverse proxy (runtime configuration)
- `VITE_API_URL` (optional, for local dev): Only needed for local development without Docker

## 📝 API Endpoints

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "ai-video-summarizer-backend"
}
```

### `POST /api/upload`
Upload and process a video file.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` (video file)

**Response:**
```json
{
  "summary": "Video summary text...",
  "filename": "video.mp4",
  "status": "success"
}
```

**Error Responses:**
- `400`: Invalid file type or file too large
- `500`: Processing error

## 🛠️ Development

### Local Development (without Docker)

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 5000
```

### Requirements

- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- ffmpeg (for audio extraction)

## 📄 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on GitHub.

