FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gosu \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install --no-cache-dir \
    torch==2.2.0+cpu \
    torchvision==0.17.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN addgroup --system appgroup && adduser --system --group appuser
RUN chown -R appuser:appgroup /app && mkdir -p /app/uploads && chown appuser:appgroup /app/uploads

EXPOSE 8000

ENV ULTRALYTICS_YOLO_WEIGHTS_DIR=/app/weights
ENV TORCH_FORCE_WEIGHTS_ONLY_LOAD=false

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]