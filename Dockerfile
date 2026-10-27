FROM docker.io/library/python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VOCAL_REMOVER_DATA_DIR=/app/data \
    VOCAL_REMOVER_MODELS_DIR=/app/models
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
# The CPU index avoids installing CUDA libraries in a CPU-only image.
RUN python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install -r requirements.txt
COPY app.py worker.py index.html ./
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data /app/models && chown -R appuser:appuser /app
USER appuser
EXPOSE 7860
CMD ["python", "app.py", "--host", "0.0.0.0", "--port", "7860", "--no-browser"]
