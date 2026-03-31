FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY models.py .
COPY baseline.py .
COPY server/environment.py server/
COPY server/app.py server/

# Create __init__ files
touch __init__.py
touch server/__init__.py

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=7860
ENV WORKERS=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:7860/health')" || exit 1

# Expose port (HF Spaces standard)
EXPOSE 7860

# Run server
CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
