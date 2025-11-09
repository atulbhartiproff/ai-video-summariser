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

Create a task definition JSON file (`task-definition.json`):

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
          "valueFrom": "arn:aws:secretsmanager:ap-southeast-2:<account-id>:secret:gemini-api-key"
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

Register the task definition:
```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Step 3: Store Gemini API Key in AWS Secrets Manager

```bash
aws secretsmanager create-secret \
  --name gemini-api-key \
  --secret-string "your-gemini-api-key-here" \
  --region ap-southeast-2
```

### Step 4: Create ECS Service

1. **Create CloudWatch Log Group**:
   ```bash
   aws logs create-log-group --log-group-name /ecs/ai-video-summarizer --region ap-southeast-2
   ```

2. **Create ECS Service** (via AWS Console or CLI):
   - Cluster: Your Fargate cluster
   - Task Definition: `ai-video-summarizer`
   - Service name: `ai-video-summarizer-service`
   - Number of tasks: 1 (or more for high availability)
   - VPC: Your VPC
   - Subnets: Public subnets (or private with NAT)
   - Security Group: Allow inbound on ports 80 and 5000
   - Load Balancer: Optional (Application Load Balancer recommended)

3. **Access the Application**:
   - If using ALB: Use the ALB DNS name (e.g., `http://ai-video-123456789.ap-southeast-2.elb.amazonaws.com`)
   - If using public IP: Use the task's public IP on port 80
   
   **Note on BACKEND_URL**: 
   - Since both containers are in the same ECS task, use `http://localhost:5000` (as shown in task definition)
   - The frontend nginx will proxy `/api/*` requests to the backend container
   - No need to expose backend port 5000 publicly - nginx handles the routing internally

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

