FROM python:3.12-slim

ARG MESHROOM_VERSION=2023.3.0
ARG MESHROOM_TGZ_URL=https://github.com/alicevision/meshroom/releases/download/v${MESHROOM_VERSION}/Meshroom-${MESHROOM_VERSION}-linux.tar.gz

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MESHROOM_WORKSPACE=/var/lib/meshroom

WORKDIR /service

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/meshroom && \
    curl -L "${MESHROOM_TGZ_URL}" | tar -xz --strip-components=1 -C /opt/meshroom && \
    chmod +x /opt/meshroom/meshroom_photogrammetry

RUN mkdir -p "${MESHROOM_WORKSPACE}"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY pipelines ./pipelines

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
