# Meshroom Processing Microservice

Enterprise-grade 3D reconstruction microservice using Meshroom photogrammetry with Celery task queue, Redis broker, and MinIO object storage.

## 🏗️ Architecture

```
┌─────────────────┐
│  Main Backend   │ (Your application)
└────────┬────────┘
         │ HTTP POST /api/v1/reconstruct
         │ + images_url
         │ + callback_url
         ▼
┌─────────────────┐
│ Meshroom API    │ (REST Gateway)
│  (FastAPI)      │
└────────┬────────┘
         │ Submit Celery task
         ▼
┌─────────────────┐
│     Redis       │ (Message Broker + Result Backend)
└────────┬────────┘
         │ Consume
         ▼
┌─────────────────┐
│ Celery Workers  │ (Processing)
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

- **Scalable**: Run multiple Celery workers independently
- **Reliable**: Celery ensures jobs aren't lost with automatic retries
- **Async**: Non-blocking REST API with webhook callbacks
- **Secure**: API key authentication
- **Monitoring**: Flower UI for real-time task monitoring
- **Production-ready**: Docker Compose, health checks, structured logging
- **Provider Architecture**: Pluggable reconstruction providers (Meshroom, Colmap, etc.)

## 🚀 Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- MinIO or S3-compatible storage
- Images uploaded to MinIO/S3 as ZIP archive

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
- **Flower Monitoring**: http://localhost:5555
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin) *(local only)*

## 📡 API Usage

### Create Reconstruction Job

```bash
curl -X POST http://localhost:8000/api/v1/reconstruct \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-change-in-production" \
  -d '{
    "model_id": 123,
    "images_url": "http://minio:9000/3d-generator/photos.zip",
    "callback_url": "https://your-backend.com/api/webhooks/meshroom"
  }'
```

**Response:**
```json
{
  "model_id": 123,
  "status": "queued"
}
```

### Webhook Callback

When job completes, your backend will receive:

**Success:**
```json
POST https://your-backend.com/api/webhooks/meshroom
{
  "model_id": 123,
  "status": "success",
  "model_url": "http://minio:9000/3d-generator/models/model_123/model.gltf",
  "texture_urls": [
    "http://minio:9000/3d-generator/models/model_123/texture_0.png"
  ],
  "stats": {
    "input_images": 25,
    "provider": "meshroom"
  }
}
```

**Failure:**
```json
{
  "model_id": 123,
  "status": "error",
  "error": "Not enough images for reconstruction: 2 (minimum 3 required)"
}
```

## 🔧 Integration Example (Python)

```python
import httpx

async def create_3d_model(model_id: int, images_zip_url: str):
    """Submit 3D reconstruction job."""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://meshroom-api:8000/api/v1/reconstruct",
            json={
                "model_id": model_id,
                "images_url": images_zip_url,
                "callback_url": "https://your-backend.com/api/webhooks/meshroom"
            },
            headers={"X-API-Key": "your-secret-api-key"},
            timeout=30.0,
        )
        result = response.json()
    
    return result["status"]  # "queued"

# Webhook handler in your backend
@app.post("/api/webhooks/meshroom")
async def meshroom_callback(payload: dict):
    model_id = payload["model_id"]
    status = payload["status"]
    
    if status == "success":
        model_url = payload["model_url"]
        
        # Download and save model
        await save_model(model_id, model_url)
        await notify_user(model_id, "Your 3D model is ready!")
    else:
        error = payload["error"]
        await notify_user(model_id, f"Error: {error}")
    
    return {"status": "ok"}
```

## 📁 Project Structure

```
meshroom-processing-microservice/
├── app/
│   ├── main.py                           # REST API Gateway (FastAPI)
│   ├── worker.py                         # Celery worker entrypoint
│   ├── celery_app.py                     # Celery configuration
│   ├── tasks.py                          # Celery tasks
│   ├── api/
│   │   ├── dependencies.py               # FastAPI dependencies
│   │   ├── models.py                     # Request/response models
│   │   └── v1/routers/
│   │       └── reconstruct.py            # Reconstruction endpoints
│   ├── core/
│   │   ├── logger.py                     # Loguru configuration
│   │   ├── settings.py                   # Configuration models
│   │   ├── reconstruct_provider/         # Reconstruction providers
│   │   │   ├── base/provider.py          # Base provider interface
│   │   │   ├── meshroom.py               # Meshroom implementation
│   │   │   └── factory.py                # Provider factory
│   │   └── storage/
│   │       ├── base/storage.py           # Storage interface
│   │       └── minio.py                  # MinIO implementation
│   ├── services/
│   │   └── reconstruction_service.py     # Universal reconstruction service
│   └── config/
│       └── app_config.json               # Application config
├── pipelines/
│   └── default.mg                        # Meshroom pipeline
├── local.yml                             # Docker Compose (dev)
├── production.yml                        # Docker Compose (prod)
├── Dockerfile                            # Container image
└── requirements.txt                      # Python dependencies
```

## 🔍 Monitoring

### Flower UI (Celery Monitoring)

1. Open http://localhost:5555
2. View:
   - Active tasks
   - Task history
   - Worker status
   - Success/failure rates
   - Task execution times

### Logs

```bash
# API logs
docker logs meshroom-api -f

# Worker logs
docker logs meshroom-local-worker-1 -f

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
    "host": "redis",
    "port": 6379,
    "redis_db": 0,
    "result_backend_db": 1
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

### Celery Configuration

Key Celery settings (in `celery_app.py`):

- **Task timeout**: 2 hours (configurable)
- **Automatic retry**: 3 attempts with exponential backoff
- **Concurrency**: 1 task per worker (resource-intensive)
- **Result expiration**: 24 hours
- **Acknowledgement**: Late (after task completion)

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

## 🏗️ Provider Architecture

The service supports multiple reconstruction providers through a pluggable architecture:

### Current Providers

- **Meshroom**: Photogrammetry pipeline (default)

### Adding New Providers

1. Create provider class in `app/core/reconstruct_provider/`:

```python
from app.core.reconstruction.base import BaseReconstructProvider


class ColmapProvider(BaseReconstructProvider):
    async def reconstruct(self, model_id: int, images_zip_url: str, **kwargs) -> dict:
        # Implement Colmap reconstruction logic
        pass
```

2. Register in factory (`app/core/reconstruct_provider/factory.py`):

```python
elif provider_type == "colmap":
    return ColmapProvider(config=config, storage=storage)
```

3. Use in tasks by changing `provider_type`:

```python
reconstruction_service = ReconstructionService(
    provider_type="colmap",  # or "meshroom"
    config=settings.meshroom,
    storage=storage,
)
```

## 🔒 Security

1. **Change API Key**: Update `X_API_KEY` in `.env`
2. **Use HTTPS**: Deploy behind reverse proxy (Nginx, Traefik)
3. **Network isolation**: Use Docker networks in production
4. **MinIO credentials**: Change default credentials in production

## 🐛 Troubleshooting

### Job stuck in queue

```bash
# Check worker logs
docker logs meshroom-local-worker-1 -f

# Check Flower UI
# Visit http://localhost:5555
```

### Out of memory

- Reduce worker replicas (edit `docker-compose.yml`)
- Increase worker resources
- Reduce `max_concurrent_jobs` in config

### Meshroom timeout

- Increase `timeout_seconds` in config (default: 7200s)
- Use fewer/smaller images
- Check GPU availability

### Task keeps retrying

Celery automatically retries failed tasks 3 times with exponential backoff. Check logs for the root cause:

```bash
docker logs meshroom-local-worker-1 -f
```

## 📝 Development

### Install dependencies locally

```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### Run locally without Docker

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start API
uvicorn app.main:app --reload

# Terminal 3: Start Worker
python -m app.worker

# Terminal 4: Start Flower (optional)
celery -A app.celery_app flower
```

### Code quality

```bash
ruff check .
mypy app/
```

## 🆚 Celery vs RabbitMQ (Previous Version)

This service was migrated from a custom RabbitMQ implementation to Celery. Benefits:

| Feature | Custom RabbitMQ | Celery |
|---------|----------------|--------|
| Automatic retries | ❌ | ✅ (exponential backoff) |
| Task monitoring UI | ❌ | ✅ (Flower) |
| Task priorities | ❌ | ✅ |
| Scheduled tasks | ❌ | ✅ |
| Result backend | ❌ | ✅ (Redis) |
| Code complexity | ~100 lines | ~50 lines |
| Industry standard | ❌ | ✅ |

## 📄 License

MIT License - see LICENSE file

## 🤝 Contributing

Pull requests welcome! Please ensure:

1. Code follows project structure
2. All tests pass
3. Documentation updated

---

**Made with ❤️ for 3D reconstruction**
