# 🚀 Quick Start Guide

## Быстрый старт за 5 минут

### 1. Настройка окружения

```bash
# Создайте .env файл
cp env.example .env

# Отредактируйте .env (ОБЯЗАТЕЛЬНО поменяйте X_API_KEY!)
nano .env
```

### 2. Запуск

```bash
# Локальная разработка (с hot-reload)
docker compose -f local.yml up --build

# Или production
docker compose -f production.yml up -d --build
```

### 3. Проверка

```bash
# Health check
curl http://localhost:8000/health

# API документация
open http://localhost:8000/docs
```

### 4. Создание задачи

```bash
curl -X POST http://localhost:8000/api/v1/reconstruct \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-change-in-production" \
  -d '{
    "model_id": 123,
    "images_url": "http://minio:9000/3d-generator/photos.zip",
    "callback_url": "https://webhook.site/your-unique-url"
  }'
```

## 🔍 Мониторинг

- **RabbitMQ UI**: http://localhost:15672 (user/pass)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **API Docs**: http://localhost:8000/docs
- **Logs**: `docker compose -f local.yml logs -f`

## 🎯 Интеграция с вашим бекендом

### Python (FastAPI/Django)

```python
import httpx

async def create_3d_model(model_id: int, images_zip_url: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://meshroom-api:8000/api/v1/reconstruct",
            json={
                "model_id": model_id,
                "images_url": images_zip_url,
                "callback_url": "https://your-backend.com/webhook",
            },
            headers={"X-API-Key": "your-api-key"},
            timeout=30.0,
        )
    return response.json()

# Webhook handler
@app.post("/webhook")
async def meshroom_callback(data: dict):
    model_id = data["model_id"]
    if data["status"] == "success":
        await save_model(model_id, data["model_url"])
    elif data["status"] == "error":
        await log_error(model_id, data["error"])
    return {"ok": True}
```

### Node.js

```javascript
const axios = require('axios');

async function create3DModel(modelId, imagesZipUrl) {
  const response = await axios.post(
    'http://meshroom-api:8000/api/v1/reconstruct',
    {
      model_id: modelId,
      images_url: imagesZipUrl,
      callback_url: 'https://your-backend.com/webhook',
    },
    {
      headers: { 'X-API-Key': 'your-api-key' }
    }
  );
  return response.data;
}

// Webhook handler
app.post('/webhook', async (req, res) => {
  const { model_id, status, model_url, error } = req.body;
  if (status === 'success') {
    await saveModel(model_id, model_url);
  } else if (status === 'error') {
    await logError(model_id, error);
  }
  res.json({ ok: true });
});
```

## ⚙️ Масштабирование

```bash
# Запустить 5 воркеров
docker compose -f production.yml up -d --scale worker=5

# Проверить статус
docker compose -f production.yml ps
```

## 🐛 Troubleshooting

### Проблема: Worker не обрабатывает задачи

```bash
# Проверить логи
docker logs meshroom-worker-1 -f

# Проверить RabbitMQ
curl -u user:pass http://localhost:15672/api/queues/%2F/meshroom_jobs
```

### Проблема: Out of memory

Уменьшите `max_concurrent_jobs` в `app/config/app_config.json`:

```json
{
  "meshroom": {
    "resources": {
      "max_concurrent_jobs": 1
    }
  }
}
```

### Проблема: Timeout

Увеличьте `timeout_seconds`:

```json
{
  "meshroom": {
    "resources": {
      "timeout_seconds": 14400
    }
  }
}
```

## 📚 Дополнительно

- [Полная документация](README.md)
- [API Reference](http://localhost:8000/docs)
- [RabbitMQ Management](http://localhost:15672)

---

**Вопросы?** Откройте issue на GitHub!

