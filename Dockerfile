# Production Dockerfile for Student Wellbeing Score Prediction Service
FROM python:3.13-slim

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    API_ENV=production

# Install essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and model artifacts
COPY app/ ./app/
COPY models/phase5_tuned_extra_trees.joblib ./models/
COPY models/phase5_metadata.json ./models/
COPY models/phase7_1_conformal_calibration.json ./models/
COPY main.py .
COPY index.html .
COPY style.css .
COPY script.js .

# Expose port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Launch production server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
