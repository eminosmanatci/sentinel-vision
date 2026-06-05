FROM python:3.11-slim

WORKDIR /app

# System dependencies for OpenCV (Debian trixie compatible)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application
COPY . .

# Create upload directory
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Fix PyTorch 2.6 weights_only for YOLOv8
ENV ULTRALYTICS_YOLO_WEIGHTS_DIR=/app/weights
ENV TORCH_FORCE_WEIGHTS_ONLY_LOAD=false

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]