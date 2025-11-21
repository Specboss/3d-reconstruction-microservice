# 🏗️ Architecture Documentation

## Overview

Meshroom Processing Microservice — это **enterprise-grade** микросервис для 3D реконструкции из фотографий с использованием Meshroom, построенный по принципам **Clean Architecture** и **микросервисной архитектуры**.

## 🎯 Design Principles

1. **Separation of Concerns** — четкое разделение слоев (API, Services, Core)
2. **Dependency Inversion** — зависимости направлены к абстракциям
3. **Single Responsibility** — каждый модуль отвечает за одну задачу
4. **Open/Closed** — расширяемость через интерфейсы
5. **Scalability** — горизонтальное масштабирование через RabbitMQ

## 📐 Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                     Presentation Layer                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  REST API    │  │   Worker     │  │   Webhooks   │  │
│  │  (FastAPI)   │  │  (Consumer)  │  │   (httpx)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                     Application Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Services   │  │  Use Cases   │  │    Models    │  │
│  │ (Business    │  │              │  │  (Pydantic)  │  │
│  │  Logic)      │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                     Infrastructure Layer                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   RabbitMQ   │  │    MinIO     │  │   Meshroom   │  │
│  │   (Broker)   │  │  (Storage)   │  │   (Binary)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 🗂️ Project Structure

```
app/
├── main.py                      # FastAPI application (API Gateway)
├── worker.py                    # Background job consumer
│
├── api/                         # Presentation Layer
│   ├── dependencies.py          # FastAPI dependencies
│   ├── models.py                # Request/Response models
│   └── v1/routers/
│       └── reconstruct.py       # Reconstruction endpoints
│
├── services/                    # Application Layer
│   ├── meshroom_service.py      # Meshroom orchestration
│   └── base/
│       └── reconstruct.py       # Abstract service interface
│
├── core/                        # Infrastructure Layer
│   ├── broker.py                # RabbitMQ client
│   ├── logger.py                # Logging configuration
│   ├── settings.py              # Configuration models
│   │
│   ├── storage/                 # Storage abstraction
│   │   ├── base/
│   │   │   └── storage.py       # Storage interface
│   │   └── minio.py             # MinIO implementation
│   │
│   └── reconstruct/             # Provider abstraction
│       ├── base/
│       │   └── provider.py      # Provider interface
│       └── meshroom_provider.py # Meshroom provider
│
└── config/
    └── app_config.json          # Application configuration
```

## 🔄 Data Flow

### 1. Job Creation Flow

```
Client
  │
  │ POST /api/v1/reconstruct
  │ {image_urls, callback_url, metadata}
  ↓
FastAPI Gateway (main.py)
  │
  │ validate request
  │ generate job_id
  ↓
RabbitMQ Broker (core/broker.py)
  │
  │ publish message
  │ {job_id, image_urls, callback_url, metadata}
  ↓
RabbitMQ Queue
  │
  ↓ response to client
Client ← {job_id, status: "queued"}
```

### 2. Job Processing Flow

```
RabbitMQ Queue
  │
  │ consume message
  ↓
Worker (worker.py)
  │
  │ parse job data
  ↓
MeshroomService (services/meshroom_service.py)
  │
  ├─→ MinIO Storage (core/storage/minio.py)
  │     ├─ download images
  │     └─ upload results
  │
  ├─→ Meshroom Binary
  │     └─ run reconstruction
  │
  └─→ Webhook Client
        └─ notify backend
```

### 3. Webhook Notification Flow

```
Worker
  │
  │ job completed/failed
  ↓
httpx Client
  │
  │ POST callback_url
  │ {job_id, status, result_url, metadata}
  ↓
Main Backend
  │
  │ save results
  │ notify user
  ↓
End
```

## 🧩 Components

### 1. API Gateway (`app/main.py`)

**Responsibility**: HTTP endpoints, request validation, authentication

```python
# Endpoints:
POST /api/v1/reconstruct  # Create reconstruction job
GET  /health              # Health check
GET  /                    # Service info
```

**Features**:
- FastAPI lifespan manager for graceful startup/shutdown
- API key authentication via header
- OpenAPI documentation
- Pydantic validation

### 2. Worker (`app/worker.py`)

**Responsibility**: Consume jobs from RabbitMQ, orchestrate processing

**Flow**:
1. Connect to RabbitMQ
2. Consume messages from queue
3. Call MeshroomService
4. Send webhook notification
5. ACK/NACK message

### 3. RabbitMQ Broker (`app/core/broker.py`)

**Responsibility**: Message queue abstraction

**Features**:
- Robust connection (auto-reconnect)
- Persistent messages
- Prefetch control (QoS)
- Exchange + Queue management

### 4. Meshroom Service (`app/services/meshroom_service.py`)

**Responsibility**: 3D reconstruction orchestration

**Flow**:
1. Download images from URLs
2. Execute Meshroom binary
3. Upload results to MinIO
4. Cleanup workspace

**Error Handling**:
- Timeout control
- Exit code validation
- Exception propagation

### 5. MinIO Storage (`app/core/storage/minio.py`)

**Responsibility**: S3-compatible object storage

**Features**:
- Async boto3 (aiobotocore)
- Upload/download files
- Presigned URLs
- HTTP(S) download

### 6. Logger (`app/core/logger.py`)

**Responsibility**: Centralized logging

**Features**:
- Loguru integration
- Structured logging
- Module-level loggers
- Configurable levels

### 7. Settings (`app/core/settings.py`)

**Responsibility**: Configuration management

**Features**:
- JSON config + .env secrets
- Pydantic validation
- Type-safe access
- Cached singleton

## 🔐 Security

### 1. API Authentication

```python
# Header-based API key
X-API-Key: your-secret-key
```

Implemented in `app/api/dependencies.py::verify_api_key`

### 2. Network Isolation

Docker networks isolate services:
- `meshroom` network for internal communication
- Only API exposed to outside

### 3. Secret Management

Secrets stored in `.env`, not in code:
```env
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
X_API_KEY=...
BROKER_USER=...
BROKER_PASSWORD=...
```

## 📊 Scalability

### Horizontal Scaling

```bash
# Scale workers
docker compose -f production.yml up -d --scale worker=10
```

**Benefits**:
- Independent worker processes
- Automatic load balancing via RabbitMQ
- No shared state

### Vertical Scaling

```yaml
# Add GPU support
worker:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

## 🔍 Observability

### Logging

- **Structured logs** with Loguru
- **Per-module loggers** for granular control
- **Correlation IDs** (job_id) in all logs

### Metrics (TODO)

- Prometheus exporters
- Grafana dashboards
- Metrics:
  - Job processing time
  - Queue depth
  - Success/failure rate

### Tracing (TODO)

- OpenTelemetry integration
- Distributed tracing

## 🧪 Testing Strategy

### Unit Tests

```python
# Test individual components
tests/unit/
  ├── test_meshroom_service.py
  ├── test_broker.py
  └── test_storage.py
```

### Integration Tests

```python
# Test component interactions
tests/integration/
  ├── test_api_endpoints.py
  └── test_worker_flow.py
```

### E2E Tests

```python
# Test full workflow
tests/e2e/
  └── test_reconstruction_flow.py
```

## 🚀 Deployment

### Development

```bash
docker compose -f local.yml up --build
```

Features:
- Hot reload
- Debug logging
- 2 workers

### Production

```bash
docker compose -f production.yml up -d --build
```

Features:
- 4 API workers (uvicorn)
- 4 processing workers
- Restart policies
- Health checks

### Kubernetes (TODO)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: meshroom-worker
spec:
  replicas: 10
  template:
    spec:
      containers:
      - name: worker
        image: meshroom-service:latest
        command: ["python", "-m", "app.worker"]
```

## 🔧 Configuration

### Environment Variables (.env)

```env
# Storage
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Message Broker
BROKER_USER=...
BROKER_PASSWORD=...

# Security
X_API_KEY=...
```

### Application Config (app_config.json)

```json
{
  "logging": {"level": "INFO"},
  "aws": {...},
  "broker": {...},
  "meshroom": {
    "binary": "/opt/meshroom/meshroom_photogrammetry",
    "pipeline_path": "/service/pipelines/default.mg",
    "resources": {
      "timeout_seconds": 7200,
      "max_concurrent_jobs": 1
    }
  }
}
```

## 🔄 Future Improvements

1. **Job Status Storage** — Redis/PostgreSQL для персистентности статусов
2. **Priority Queues** — разные очереди для срочных/обычных задач
3. **Retry Logic** — автоматический retry с exponential backoff
4. **Dead Letter Queue** — обработка failed jobs
5. **Metrics & Monitoring** — Prometheus + Grafana
6. **Authentication** — OAuth2/JWT вместо API key
7. **Rate Limiting** — защита от DDoS
8. **Distributed Tracing** — OpenTelemetry
9. **Caching** — Redis для часто запрашиваемых результатов
10. **Multi-tenancy** — изоляция по пользователям/организациям

## 📚 References

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [RabbitMQ Tutorials](https://www.rabbitmq.com/tutorials/tutorial-one-python.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [12-Factor App](https://12factor.net/)

---

**Architecture designed for scale, maintainability, and reliability** 🚀

