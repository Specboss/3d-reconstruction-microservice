FROM python:3.12-slim

# -----------------------------
# 1️⃣ Системные зависимости
# -----------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    git \
    libgl1 \
    libxrandr2 \
    libxinerama1 \
    libxcursor1 \
    libxi6 \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# 2️⃣ Устанавливаем obj2gltf
# -----------------------------
RUN npm install -g obj2gltf

# -----------------------------
# 3️⃣ Устанавливаем AliceVision_photogrammetry
# -----------------------------
RUN wget https://github.com/alicevision/AliceVision/releases/download/v2025.1.0/AliceVision-2025.1.0-Linux.tar.gz -O /tmp/alicevision.tar.gz && \
    tar -xzf /tmp/alicevision.tar.gz -C /opt/ && \
    rm /tmp/alicevision.tar.gz

ENV PATH="/opt/AliceVision-2025.1.0/bin:${PATH}"

# -----------------------------
# 4️⃣ Настраиваем Python окружение
# -----------------------------
WORKDIR /service

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app ./app

# -----------------------------
# 5️⃣ Порты и CMD
# -----------------------------
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
