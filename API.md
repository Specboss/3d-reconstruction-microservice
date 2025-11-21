# 📡 API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
All endpoints require API key authentication via header:
```
X-API-Key: your-secret-api-key
```

---

## Endpoints

### 1. Create Reconstruction Job

**POST** `/api/v1/reconstruct`

Create a new 3D reconstruction job from ZIP archive with photos.

#### Request

```json
{
  "model_id": 123,
  "images_url": "https://minio/bucket-name/photos.zip",
  "callback_url": "https://your-backend.com/webhook"  // optional
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_id` | integer | ✅ Yes | Unique model identifier (must be > 0) |
| `images_url` | string (URL) | ✅ Yes | MinIO URL to ZIP archive with photos |
| `callback_url` | string (URL) | ❌ No | Webhook URL for completion notification |

#### Response (200 OK)

```json
{
  "model_id": 123,
  "status": "queued"
}
```

#### Example (cURL)

```bash
curl -X POST http://localhost:8000/api/v1/reconstruct \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d '{
    "model_id": 123,
    "images_url": "https://minio:9000/bucket-name/photos.zip",
    "callback_url": "https://your-backend.com/webhook"
  }'
```

#### Example (Python)

```python
import httpx

async def create_3d_model(model_id: int, images_url: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/reconstruct",
            json={
                "model_id": model_id,
                "images_url": images_url,
                "callback_url": "https://your-backend.com/webhook",
            },
            headers={"X-API-Key": "your-secret-api-key"},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
```

#### Example (JavaScript)

```javascript
async function create3DModel(modelId, imagesUrl) {
  const response = await fetch('http://localhost:8000/api/v1/reconstruct', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'your-secret-api-key',
    },
    body: JSON.stringify({
      model_id: modelId,
      images_url: imagesUrl,
      callback_url: 'https://your-backend.com/webhook',
    }),
  });
  
  return await response.json();
}
```

---

### 2. Health Check

**GET** `/health`

Check service health status.

#### Response (200 OK)

```json
{
  "status": "ok",
  "meshroom_binary": "/opt/meshroom/meshroom_photogrammetry",
  "bucket": "3d-generator"
}
```

---

## Webhook Callback

When job completes (successfully or with error), if `callback_url` was provided, the service will send a POST request to that URL.

### Success Callback

```json
POST {callback_url}
Content-Type: application/json

{
  "model_id": 123,
  "status": "success",
  "model_url": "https://minio/bucket-name/models/model_123/model.gltf"
}
```

### Error Callback

```json
POST {callback_url}
Content-Type: application/json

{
  "model_id": 123,
  "status": "error",
  "error": "Meshroom process failed with exit code 1"
}
```

### Webhook Handler Example (Python/FastAPI)

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class MeshroomCallback(BaseModel):
    model_id: int
    status: str  # "success" or "error"
    model_url: str | None = None
    error: str | None = None

@app.post("/webhook")
async def meshroom_webhook(payload: MeshroomCallback):
    if payload.status == "success":
        # Save model URL to database
        await db.update_model(
            model_id=payload.model_id,
            status="completed",
            model_url=payload.model_url,
        )
        
        # Notify user
        await notify_user(payload.model_id, "Your 3D model is ready!")
    
    elif payload.status == "error":
        # Handle error
        await db.update_model(
            model_id=payload.model_id,
            status="failed",
            error=payload.error,
        )
        
        # Notify user about error
        await notify_user(payload.model_id, f"Error: {payload.error}")
    
    return {"status": "ok"}
```

---

## Error Responses

### 400 Bad Request
Invalid request body or parameters.

```json
{
  "detail": [
    {
      "loc": ["body", "model_id"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error"
    }
  ]
}
```

### 403 Forbidden
Invalid or missing API key.

```json
{
  "detail": "Invalid API key"
}
```

### 422 Unprocessable Entity
Validation error (e.g., invalid URL format).

```json
{
  "detail": [
    {
      "loc": ["body", "images_url"],
      "msg": "invalid or missing URL scheme",
      "type": "value_error.url.scheme"
    }
  ]
}
```

---

## Complete Integration Example

### 1. User Uploads Photos

```python
# User uploads photos to your backend
@app.post("/api/models/{model_id}/photos")
async def upload_photos(model_id: int, files: list[UploadFile]):
    # Create ZIP archive
    zip_path = f"/tmp/model_{model_id}_photos.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in files:
            content = await file.read()
            zipf.writestr(file.filename, content)
    
    # Upload ZIP to MinIO
    minio_url = await upload_to_minio(
        zip_path,
        bucket="3d-models",
        key=f"inputs/model_{model_id}.zip",
    )
    
    # Save to database
    await db.update_model(model_id, input_zip=minio_url, status="uploaded")
    
    return {"model_id": model_id, "zip_url": minio_url}
```

### 2. Trigger 3D Reconstruction

```python
@app.post("/api/models/{model_id}/reconstruct")
async def start_reconstruction(model_id: int):
    # Get model from DB
    model = await db.get_model(model_id)
    
    if not model.input_zip:
        raise HTTPException(400, "No photos uploaded")
    
    # Call Meshroom microservice
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://meshroom-api:8000/api/v1/reconstruct",
            json={
                "model_id": model_id,
                "images_url": model.input_zip,
                "callback_url": "https://your-backend.com/api/webhooks/meshroom",
            },
            headers={"X-API-Key": settings.MESHROOM_API_KEY},
        )
        result = response.json()
    
    # Update status
    await db.update_model(model_id, status="processing")
    
    return result
```

### 3. Receive Webhook

```python
@app.post("/api/webhooks/meshroom")
async def meshroom_callback(payload: MeshroomCallback):
    if payload.status == "success":
        # Update database
        await db.update_model(
            model_id=payload.model_id,
            status="completed",
            model_url=payload.model_url,
        )
        
        # Notify user via WebSocket/Email/Push
        await notify_user(payload.model_id, {
            "status": "completed",
            "model_url": payload.model_url,
        })
    
    return {"status": "ok"}
```

### 4. User Downloads Model

```python
@app.get("/api/models/{model_id}/download")
async def download_model(model_id: int):
    model = await db.get_model(model_id)
    
    if model.status != "completed":
        raise HTTPException(400, "Model not ready")
    
    # Redirect to MinIO presigned URL or proxy download
    return RedirectResponse(model.model_url)
```

---

## Rate Limiting

Currently not implemented. Consider adding rate limiting in production:

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post(
    "/api/v1/reconstruct",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def create_reconstruction_job(...):
    ...
```

---

## OpenAPI Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Support

For issues or questions:
1. Check logs: `docker logs meshroom-api -f`
2. Check RabbitMQ: http://localhost:15672
3. Verify MinIO: http://localhost:9001

