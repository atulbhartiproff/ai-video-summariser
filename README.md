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

### Step 1: Build and Push Docker Images to ECR

1. **Create ECR repositories** (if not exists):
   ```bash
   aws ecr create-repository --repository-name ai-video-frontend --region us-east-1
   aws ecr create-repository --repository-name ai-video-backend --region us-east-1
   ```

2. **Authenticate Docker to ECR**:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.us-east-1.amazonaws.com
   ```

3. **Build and tag images**:
   ```bash
   # Build frontend
   docker build -t ai-video-frontend ./frontend --build-arg VITE_API_URL=http://your-backend-url:5000
   docker tag ai-video-frontend:latest <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-video-frontend:latest
   
   # Build backend
   docker build -t ai-video-backend ./backend
   docker tag ai-video-backend:latest <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-video-backend:latest
   ```

4. **Push images to ECR**:
   ```bash
   docker push <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-video-frontend:latest
   docker push <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-video-backend:latest
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
      "image": "<your-account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-video-backend:latest",
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
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:gemini-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-video-summarizer",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "backend"
        }
      }
    },
    {
      "name": "frontend",
      "image": "<your-account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-video-frontend:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
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
          "awslogs-region": "us-east-1",
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
  --region us-east-1
```

### Step 4: Create ECS Service

1. **Create CloudWatch Log Group**:
   ```bash
   aws logs create-log-group --log-group-name /ecs/ai-video-summarizer --region us-east-1
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
   - If using ALB: Use the ALB DNS name
   - If using public IP: Use the task's public IP on port 80

## 🔧 Environment Variables

### Backend
- `GEMINI_API_KEY` (required): Your Google Gemini API key
- `PORT` (default: 5000): Backend server port
- `MAX_FILE_SIZE_MB` (default: 500): Maximum upload file size in MB

### Frontend
- `VITE_API_URL` (default: http://localhost:5000): Backend API URL

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

