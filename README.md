# Meshroom Processing Microservice

Enterprise-grade 3D reconstruction microservice using Meshroom photogrammetry with RabbitMQ message queue and MinIO object storage.

## 🏗️ Architecture

```
┌─────────────────┐
│  Main Backend   │ (Your application)
└────────┬────────┘
         │ HTTP POST /api/v1/reconstruct
         │ + image_urls
         │ + callback_url
         ▼
┌─────────────────┐
│ Meshroom API    │ (REST Gateway)
│  (FastAPI)      │
└────────┬────────┘
         │ Publish job
         ▼
┌─────────────────┐
│   RabbitMQ      │ (Message Queue)
└────────┬────────┘
         │ Consume
         ▼
┌─────────────────┐
│ Meshroom Worker │ (Processing)
│   × N replicas  │
└────────┬────────┘
         │ Upload results
         ▼
┌─────────────────┐     Webhook
│     MinIO       │────────────►  Main Backend
│   (Storage)     │              (Callback)
└─────────────────┘
```

## ✨ Features

- **Scalable**: Run multiple workers independently
- **Reliable**: RabbitMQ ensures jobs aren't lost
- **Async**: Non-blocking REST API with webhook callbacks
- **Secure**: API key authentication
- **Production-ready**: Docker Compose, health checks, logging

## 🚀 Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- MinIO or S3-compatible storage
- Images uploaded to MinIO/S3

### 2. Setup

```bash
# Clone repository
cd meshroom-processing-microservice

# Copy environment variables
cp env.example .env

# Edit .env with your settings
nano .env
```

**Required environment variables:**

```env
# MinIO/S3 credentials
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin

# RabbitMQ credentials
BROKER_USER=user
BROKER_PASSWORD=pass

# API security (CHANGE IN PRODUCTION!)
X_API_KEY=your-secret-api-key-change-in-production
```

### 3. Run

**Local development:**
```bash
docker compose -f local.yml up --build
```

**Production:**
```bash
docker compose -f production.yml up -d --build
```

### 4. Access Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672 (user/pass)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## 📡 API Usage

### Create Reconstruction Job

```bash
curl -X POST http://localhost:8000/api/v1/reconstruct \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-change-in-production" \
  -d '{
    "image_urls": [
      "http://minio:9000/3d-generator/photo1.jpg",
      "http://minio:9000/3d-generator/photo2.jpg"
    ],
    "callback_url": "https://your-backend.com/api/webhooks/meshroom",
    "metadata": {
      "user_id": 123,
      "project_id": 456
    }
  }'
```

**Response:**
```json
{
  "job_id": "abc123def456",
  "status": "queued",
  "message": "Job abc123def456 has been queued for processing"
}
```

### Webhook Callback

When job completes, your backend will receive:

```json
POST https://your-backend.com/api/webhooks/meshroom
{
  "job_id": "abc123def456",
  "status": "completed",
  "result_url": "http://minio:9000/3d-generator/results/abc123def456/texturedMesh.obj",
  "metadata": {
    "user_id": 123,
    "project_id": 456
  }
}
```

**On failure:**
```json
{
  "job_id": "abc123def456",
  "status": "failed",
  "error": "Meshroom process failed with exit code 1",
  "metadata": {...}
}
```

## 🔧 Integration Example (Python)

```python
import httpx

async def create_3d_model(user_id: int, image_urls: list[str]):
    """Submit 3D reconstruction job."""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://meshroom-api:8000/api/v1/reconstruct",
            json={
                "image_urls": image_urls,
                "callback_url": "https://your-backend.com/api/webhooks/meshroom",
                "metadata": {"user_id": user_id}
            },
            headers={"X-API-Key": "your-secret-api-key"},
            timeout=30.0,
        )
        result = response.json()
    
    return result["job_id"]

# Webhook handler in your backend
@app.post("/api/webhooks/meshroom")
async def meshroom_callback(payload: dict):
    job_id = payload["job_id"]
    status = payload["status"]
    
    if status == "completed":
        result_url = payload["result_url"]
        user_id = payload["metadata"]["user_id"]
        
        # Download and save model
        await save_user_model(user_id, result_url)
        await notify_user(user_id, "Your 3D model is ready!")
    
    return {"status": "ok"}
```

## 📁 Project Structure

```
meshroom-processing-microservice/
├── app/
│   ├── main.py                    # REST API Gateway
│   ├── worker.py                  # Job consumer
│   ├── api/
│   │   ├── dependencies.py        # FastAPI dependencies
│   │   ├── models.py              # Request/response models
│   │   └── v1/routers/
│   │       └── reconstruct.py     # Reconstruction endpoints
│   ├── core/
│   │   ├── broker.py              # RabbitMQ client
│   │   ├── logger.py              # Loguru configuration
│   │   ├── settings.py            # Configuration models
│   │   └── storage/
│   │       ├── base/storage.py    # Storage interface
│   │       └── minio.py           # MinIO implementation
│   ├── services/
│   │   └── meshroom_service.py    # Meshroom processing logic
│   └── config/
│       └── app_config.json        # Application config
├── pipelines/
│   └── default.mg                 # Meshroom pipeline
├── local.yml                      # Docker Compose (dev)
├── production.yml                 # Docker Compose (prod)
├── Dockerfile                     # Container image
└── requirements.txt               # Python dependencies
```

## 🔍 Monitoring

### RabbitMQ Management UI

1. Open http://localhost:15672
2. Login with BROKER_USER/BROKER_PASSWORD
3. View queue depth, message rates, workers

### Logs

```bash
# API logs
docker logs meshroom-api -f

# Worker logs
docker logs meshroom-worker -f

# All services
docker compose -f local.yml logs -f
```

## ⚙️ Configuration

### `app/config/app_config.json`

```json
{
  "logging": {
    "level": "DEBUG"
  },
  "aws": {
    "endpoint_url": "http://minio:9000",
    "bucket_name": "3d-generator"
  },
  "broker": {
    "host": "rabbitmq",
    "port": 5672,
    "queue_name": "meshroom_jobs"
  },
  "meshroom": {
    "binary": "/opt/meshroom/meshroom_photogrammetry",
    "pipeline_path": "/service/pipelines/default.mg",
    "workspace_dir": "/var/lib/meshroom",
    "resources": {
      "max_concurrent_jobs": 1,
      "timeout_seconds": 7200
    }
  }
}
```

## 🚀 Scaling

### Horizontal Scaling (More Workers)

```bash
# Scale to 5 workers
docker compose -f production.yml up -d --scale worker=5
```

### Vertical Scaling (GPU Support)

Edit `production.yml`:

```yaml
worker:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

## 🔒 Security

1. **Change API Key**: Update `X_API_KEY` in `.env`
2. **Change RabbitMQ credentials**: Update `BROKER_USER`/`BROKER_PASSWORD`
3. **Use HTTPS**: Deploy behind reverse proxy (Nginx, Traefik)
4. **Network isolation**: Use Docker networks in production

## 🐛 Troubleshooting

### Job stuck in queue

```bash
# Check worker logs
docker logs meshroom-worker-1 -f

# Check RabbitMQ
# Visit http://localhost:15672 → Queues
```

### Out of memory

- Reduce `max_concurrent_jobs` in config
- Increase worker resources
- Scale horizontally instead

### Meshroom timeout

- Increase `timeout_seconds` in config
- Use fewer/smaller images
- Check GPU availability

## 📝 Development

### Install dependencies locally

```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### Run tests

```bash
pytest tests/
```

### Code quality

```bash
ruff check .
mypy app/
```

## 📄 License

MIT License - see LICENSE file

## 🤝 Contributing

Pull requests welcome! Please ensure:

1. Code follows project structure
2. All tests pass
3. Documentation updated

---

**Made with ❤️ for 3D reconstruction**

